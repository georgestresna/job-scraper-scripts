import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database import init_db, SessionLocal, Job
from sqlalchemy.exc import IntegrityError
import requests
from bs4 import BeautifulSoup


def is_in_db(db, job_link):
    result = db.query(Job).filter(Job.link == job_link).first()
    return result is not None

def process_job_details(db, job_link):
    try:
        response = requests.get(job_link, headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'})

        if response.status_code != 200:
            print(f"[!] Failed to fetch details: Status {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')

        #extracting details
        title = soup.find("h1", class_="top-card-layout__title")
        title = title.get_text(strip=True) if title else "Unknown Title"

        company = soup.find("a", class_="topcard__org-name-link")
        company = company.get_text(strip=True) if company else "Unknown Company"

        location = soup.find("span", class_="topcard__flavor topcard__flavor--bullet")
        location = location.get_text(strip=True) if location else "Unknown Location"

        desc_div = soup.find("div", class_="description__text")
        description = desc_div.get_text(separator="\n", strip=True) if desc_div else ""

        criteria_items = soup.find_all("li", class_="description__job-criteria-item")
        seniority = criteria_items[0].find("span").get_text(strip=True) if len(criteria_items) > 0 else "Not Listed"
        emp_type = criteria_items[1].find("span").get_text(strip=True) if len(criteria_items) > 1 else "Not Listed"

        new_job = Job(
            title=title,
            company=company,
            location=location,
            description=description,
            seniority=seniority,
            employment_type=emp_type,
            link=job_link,
        )
        db.add(new_job)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[!] Error processing {job_link}: {e}")

def cleanup_expired_jobs():
    pass

def run_scraper(
        job_title="Software Engineer", 
        location="Bucharest", 
        timeframe="r86400", 
        experience="1,2"
    ):

    print("[*] Initializing Database...")
    init_db()
    db = SessionLocal()

    print("[*] Initializing WebDriver...")
    
    options = Options()
    # options.add_argument("--headless") # Commented out for visual debugging
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Avoid detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    selenium_url = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")

    driver = None
    for i in range(30):
        try:
            driver = webdriver.Remote(command_executor=selenium_url, options=options)
            break
        except Exception:
            print(f"[*] Waiting for Selenium (attempt {i+1}/30)...")
            time.sleep(1)
            
    if not driver:
        print("[!] Could not connect to Selenium after 30 seconds.")
        db.close()
        return

    wait = WebDriverWait(driver, 10)

    try:

        url = (
            f"https://www.linkedin.com/jobs/search"
            f"?keywords={job_title.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}"
            f"&f_TPR={timeframe}"      # Posted in the last week (604800 seconds)
            f"&f_E={experience}"               # Experience level: Entry Level + internship
            #f"&geoId=105889820"     # Specific ID for Bucharest
            f"&distance=25"         # 25km radius
        )       

        print(f"[*] Navigating to: {url}")
        driver.get(url)

        # Initial wait for page load
        print("[*] Waiting for initial page load...")
        try:
            wait.until(lambda d: d.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul/li[1]/div/a').is_displayed())
        except:
            print("    [!] Timeout waiting for job list.")

        try:
            driver.find_element(By.XPATH, '//*[@id="base-contextual-sign-in-modal"]/div/section/button').click()
        except:
            print("[!] X'd the SignIn wall")


        #Bypass antibot
        try:
            print("[*] Clicking first job listing...")
            first_job_link = driver.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul/li[1]/div/a')
            first_job_link.click()
            
            print("[*] Waiting for job page to load...")
            try:
                wait.until(lambda d: d.find_element(By.TAG_NAME, "h1").is_displayed())
            except:
                print("    [!] Timeout waiting for job details.")
            
            print("[*] Going back...")
            driver.back()
            
            print("[*] Waiting for search page to reload...")
            try:
                wait.until(lambda d: d.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul/li[1]/div/a').is_displayed())
            except:
                print("    [!] Timeout waiting for search results.")
        except Exception as e:
             print(f"[*] First job click failed: {e}")

        ##De aici incepe scrapingul
        
        current = 1
        while current <= 3:
            try:
                locator = (By.XPATH, f'//*[@id="main-content"]/section[2]/ul/li[{current}]/div/a')
                job_element = wait.until(EC.presence_of_element_located(locator))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_element)
                job_link = job_element.get_attribute("href").split("?")[0]

                #otherwise, i get bot--blocked
                time.sleep(0.3)

                if not is_in_db(db, job_link):
                    process_job_details(db, job_link)

                print(f"[*] Job scraped: {job_link}")
                current += 1

            except Exception:
                #if no card found
                try:
                    print("[*] Card not found. Trying 'See more'...")
                    btn = driver.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/button')
                    btn.click()
                    #time.sleep(0.5)
                    #NO MORE current+=1, so this step restarts
                except Exception:
                    try:
                        msg = driver.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/div/p').text
                        if "viewed all jobs" in msg:
                            print("[!] Reached the very end.")
                            break
                    except:
                        print("[?] Stuck. Exiting...")
                        break

        print(f"[*] Finished. Total processed: {current - 1}")
    except Exception as e:
        print(f"[!] Critical Error: {e}")
    finally:
        if driver:
            driver.quit()
        # db.close()

if __name__ == "__main__":
    run_scraper()