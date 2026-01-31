import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_scraper():
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
            # wait = WebDriverWait(driver, 20)
            break
        except Exception:
            print(f"[*] Waiting for Selenium (attempt {i+1}/30)...")
            time.sleep(1)
            
    if not driver:
        print("[!] Could not connect to Selenium after 30 seconds.")
        return

    try:
        # Search parameters
        job_title = "Software Engineer"
        location = "New York"
        url = f"https://www.linkedin.com/jobs/search?keywords={job_title.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        
        print(f"[*] Navigating to: {url}")
        driver.get(url)

        # Initial wait for page load
        print("[*] Waiting 5s for initial page load...")
        time.sleep(5)


        # 1. Handle Sign-in Modal
        try:
            print("[*] Looking for contextual sign-in modal button...")
            sign_in_modal_btn = driver.find_element(By.XPATH, '//*[@id="base-contextual-sign-in-modal"]/div/section/button')
            
            if sign_in_modal_btn.is_displayed():
                print("[*] Moving mouse to button and clicking...")
                actions = ActionChains(driver)
                actions.move_to_element(sign_in_modal_btn).click().perform()
                time.sleep(3)
            else:
                print("[*] Button found but not displayed.")
        except Exception:
            print("[*] Contextual modal not present.")


        # 2. CLICK FIRST JOB LISTING (Bypass Trigger)
        # 2. Click First Job (Bypass Trigger)
        try:
            print("[*] Clicking first job listing to trigger bypass...")
            first_job_link = driver.find_element(By.CSS_SELECTOR, "ul.jobs-search__results-list > li a.base-card__full-link")
            first_job_link.click()
            
            print("[*] Waiting 10s for job page to load...")
            time.sleep(10)
            
            print("[*] Going back...")
            driver.back()
            
            print("[*] Waiting 5s for search page to reload...")
            time.sleep(5)
        except Exception as e:
             print(f"[*] First job click failed: {e}")

        print("[*] Starting Full Page Scroll & Scrape Loop...")
        jobs_data = []
        seen_links = set()
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Full Page Scroll
            print("[*] Scrolling to bottom...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5) # Wait for load

            
            # Scrape visible jobs immediately
            job_cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list > li")
            for card in job_cards:
                try:
                    link_el = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                    link = link_el.get_attribute("href")
                    
                    if link not in seen_links:
                        title = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
                        company = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle").text.strip()
                        loc = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location").text.strip()
                        
                        jobs_data.append({
                            "Title": title,
                            "Company": company,
                            "Location": loc,
                            "Link": link
                        })
                        seen_links.add(link)
                except:
                    continue
            
            print(f"[*] Collected {len(jobs_data)} unique jobs so far...")

            if len(jobs_data) >= 200:
                print("[*] Reached target of 200 listings. Stopping.")
                break
            
            # Check EOF
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[*] Hit bottom. Waiting 10s to see if more loads...")
                time.sleep(10)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("[!] Truly reached end of page.")
                    break
            last_height = new_height
            
            # Check for "See more" button
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
                if btn.is_displayed():
                    print("[*] Clicking 'See more' button...")
                    actions = ActionChains(driver)
                    actions.move_to_element(btn).click().perform()
                    time.sleep(5)
            except:
                pass



        print(f"[*] Finished. Total unique jobs: {len(jobs_data)}")
        
        # Create DataFrame
        df = pd.DataFrame(jobs_data)
        
        # Save to CSV
        csv_file = "jobs.csv"
        df.to_csv(csv_file, index=False)
        print(f"[*] Saved data to {csv_file}")
        


        print("\n" + "="*50)
        print(f"[*] Successfully Scraped {len(df)} Jobs")
        print("="*50)
        
        driver.quit()
        
    except Exception as e:
        print(f"[!] Error: {e}")
        if driver:

            driver.quit()

if __name__ == "__main__":
    run_scraper()