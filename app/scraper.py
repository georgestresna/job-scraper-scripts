import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def run_scraper():
    print("[*] Initializing WebDriver...")
    
    options = Options()
    options.add_argument("--headless")
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
        return

    try:
        print("[*] Navigating to LinkedIn...")
        driver.get("https://www.linkedin.com")
        
        print(f"[+] Page title: {driver.title}")
        
        print("[*] Waiting 3 seconds...")
        time.sleep(3)
        
        driver.quit()
        print("[*] Done.")
        
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    run_scraper()