from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-save-password-bubble')
    options.add_argument('--disable-translate')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    options.add_argument('--disable-site-isolation-trials')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--force-color-profile=srgb')
    options.add_argument('--hide-scrollbars')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # Binary detection
    if os.name != 'nt':
        for path in ['/usr/bin/google-chrome-stable','/usr/bin/google-chrome','/usr/bin/chrome','/usr/bin/chromium','/usr/bin/chromium-browser']:
            if os.path.exists(path):
                options.binary_location = path
                logger.info(f"Using Chrome binary at {path}")
                break
    return options

def initialize_webdriver():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            options = get_chrome_options()
            try:
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
            except Exception:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            driver.get("about:blank")
            return driver
        except Exception as e:
            logger.error(f"Webdriver init failed (attempt {attempt+1}): {e}")
            time.sleep(5)
    return None

def scrape_pagasa_rainfall():
    logger.info("Starting rainfall scraping...")
    driver = initialize_webdriver()
    if not driver:
        logger.error("Failed to initialize webdriver for rainfall scraping")
        return None, None
    try:
        for attempt in range(3):
            try:
                driver.get("https://pasig-marikina-tullahanffws.pagasa.dost.gov.ph/rainfall/table.do")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-type1"))
                )
                time.sleep(5)
                break
            except Exception as e:
                logger.error(f"Navigation attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    return None, None
                time.sleep(5)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'class': 'table-type1'})
        if not table:
            logger.error("Could not find rainfall data table")
            return None, None
        headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
        data = []
        search_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 8:
                data.append({
                    'station': cols[0].get_text(strip=True),
                    'current_rf': cols[1].get_text(strip=True),
                    'rf_30min': cols[2].get_text(strip=True),
                    'rf_1hr': cols[3].get_text(strip=True),
                    'rf_3hr': cols[4].get_text(strip=True),
                    'rf_6hr': cols[5].get_text(strip=True),
                    'rf_12hr': cols[6].get_text(strip=True),
                    'rf_24hr': cols[7].get_text(strip=True),
                    'timestamp': search_time
                })
        return headers, data
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        return None, None
    finally:
        driver.quit()

def display_rainfall_data(headers, data):
    """Displays the rainfall data in the exact table format"""
    if not data:
        print("No rainfall data available")
        return
    
    # Get the timestamp from the first record
    timestamp = data[0]['timestamp'] if data else datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"\n# Time : {timestamp}")
    print("| Station | Current RF | 30min RF | 1hr RF | 3hr RF | 6hr RF | 12hr RF | 24hr RF |")
    print("|---|---|---|---|---|---|---|---|")
    
    for entry in data:
        station = entry['station']
        current_rf = entry['current_rf']
        rf_30min = entry['rf_30min']
        rf_1hr = entry['rf_1hr']
        rf_3hr = entry['rf_3hr']
        rf_6hr = entry['rf_6hr']
        rf_12hr = entry['rf_12hr']
        rf_24hr = entry['rf_24hr']
        print(f"| {station} | {current_rf} | {rf_30min} | {rf_1hr} | {rf_3hr} | {rf_6hr} | {rf_12hr} | {rf_24hr} |")

def save_to_csv(data):
    """Saves the data to CSV file"""
    if not data:
        print("No data to save")
        return
    
    df = pd.DataFrame(data)
    filename = f"pagasa_rainfall_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename, index=False)
    print(f"\nData saved to {filename}")

def main():
    print("PAGASA Rainfall Data Scraper")
    print("=" * 40)
    
    # Scrape the data
    headers, rainfall_data = scrape_pagasa_rainfall()
    
    # Display the results
    display_rainfall_data(headers, rainfall_data)
    
    # Option to save to CSV
    if rainfall_data:
        save = input("\nDo you want to save this data to CSV? (y/n): ").lower()
        if save == 'y':
            save_to_csv(rainfall_data)

if __name__ == "__main__":
    # Install required packages if needed
    try:
        import pandas as pd
    except ImportError:
        import subprocess
        subprocess.check_call(['pip', 'install', 'pandas'])
        import pandas as pd
    
    main()