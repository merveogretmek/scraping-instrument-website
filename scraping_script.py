# Scraping Instrument Website

## Libraries

import sys
import json
import time
import pandas as pd
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import cloudinary
import cloudinary.uploader

## Functions

def scroll_to_bottom(wait_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")

    items_loaded_history = []

    while True:

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)

        items = driver.find_elements(By.CSS_SELECTOR, ".box-module")
        total_items = len(items)
        items_loaded_history.append(total_items)
        print(f"Total items loaded so far: {total_items}")

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break

        last_height = new_height
    
    return items_loaded_history

def get_module_data():
    
    print("Collecting module links from the search page...")
    module_data = []
    box_modules = driver.find_elements(By.CLASS_NAME, "box-module")

    for module in box_modules:
        try:
            module_id = module.get_attribute("data-module-id")
            link_element = module.find_element(By.TAG_NAME, "a")
            href = link_element.get_attribute("href")

            if href.startswith("https"):
                print(f"Found module ID {module_id} with link {href}")
                module_data.append({"id": module_id, "link": href})
        except Exception as e:
            print("No link found in this module:", e)

    print("Total modules found:", len(module_data))
    return module_data

def scrape_page(module_info, wait, driver):
    url = module_info['link']
    module_id = module_info['id']
    
    # Initialize results with default values
    results = {
        "id": module_id,
        "module_name": None,
        "manufacturer": None,
        "primary_desc": None,
        "available": None,
        "approved_stamp": None,
        "physical_dim": None,
        "power_req": None,
        "module_tags": None,
        "full_desc": None,
        "price_in_euro": None,
        "price_in_dollar": None,
        "module_url": url,
        "cloudinary_url": None
    }
    
    try: 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".module-view-header h1")))
    except Exception as e:
        print(f"Timeout waiting for module name on {url}: {e}")
    
    # --------------------------------------- MODULE NAME ---------------------------------------
    try:
        module_name_element = driver.find_element(By.CSS_SELECTOR, ".module-view-header h1")
        results["module_name"] = module_name_element.text.strip()
    except Exception as e:
        print(f"Module name not found for {url}: {e}")
        results["module_name"] = ""
    
    # --------------------------------------- MANUFACTURER ---------------------------------------
    try: 
        manufacturer_element = driver.find_element(By.CSS_SELECTOR, ".vendor-name")
        results["manufacturer"] = manufacturer_element.text.strip()
    except Exception as e:
        print(f"Manufacturer not found for {url}: {e}")
        results["manufacturer"] = ""
    
    # --------------------------------------- PRIMARY DESCRIPTION ---------------------------------------
    try:
        primary_description_element = driver.find_element(By.CSS_SELECTOR, "p.lead.wrap")
        results["primary_desc"] = primary_description_element.text.strip()
    except Exception as e:
        print(f"Primary description not found for {url}: {e}")
        results["primary_desc"] = ""
    
    # --------------------------------------- AVAILABILITY ---------------------------------------
    try: 
        availability_elements = driver.find_elements(
            By.XPATH, 
            "//div[contains(@class, 'subspec')]/p[contains(@class, 'text-success') and contains(., 'currently available')]"
        )
        results["available"] = 1 if availability_elements else 0
    except Exception as e:
        print(f"Error determining availability for {url}: {e}")
        results["available"] = 0
    
    # --------------------------------------- APPROVED STAMP ---------------------------------------
    try:
        driver.find_element(By.CSS_SELECTOR, ".box-approved")
        results["approved_stamp"] = 1
    except Exception:
        results["approved_stamp"] = 0
    
    # --------------------------------------- PHYSICAL DIMENSIONS ---------------------------------------
    try:
        dims_dt = driver.find_element(By.XPATH, "//dt[normalize-space(text())='Dimensions']")
        parent_dl = dims_dt.find_element(By.XPATH, "./..")
        dd_elements = parent_dl.find_elements(By.TAG_NAME, "dd")
        dimensions_list = [dd.text.strip() for dd in dd_elements if dd.text.strip()]
        results["physical_dim"] = " | ".join(dimensions_list)
    except Exception as e:
        print(f"Dimensions not found for {url}: {e}")
        results["physical_dim"] = ""
    
    # --------------------------------------- POWER REQUIREMENTS ---------------------------------------
    try:
        current_draw_dt = driver.find_element(By.XPATH, "//dt[contains(., 'Current') and contains(., 'Draw')]")
        parent_dl = current_draw_dt.find_element(By.XPATH, "./..")
        dd_elements = parent_dl.find_elements(By.TAG_NAME, "dd")
        current_draw_list = [dd.text.strip() for dd in dd_elements if dd.text.strip()]
        results["power_req"] = " | ".join(current_draw_list)
    except Exception as e:
        print(f"Power requirements not found for {url}: {e}") 
        results["power_req"] = ""
    
    # --------------------------------------- MODULE TAGS ---------------------------------------
    try:
        tags_div = driver.find_element(By.CSS_SELECTOR, "div.module-tags")
        tag_spans = tags_div.find_elements(By.CSS_SELECTOR, "span.label")
        results["module_tags"] = ", ".join([span.text.strip() for span in tag_spans if span.text.strip()])
    except Exception as e:
        print(f"Module tags not found for {url}: {e}")
        results["module_tags"] = ""
    
    # --------------------------------------- FULL DESCRIPTION ---------------------------------------
    try:
        module_details_div = driver.find_element(By.ID, "module-details")
        p_elements = module_details_div.find_elements(By.TAG_NAME, "p")
        full_desc_paragraphs = []
        for p in p_elements:
            p_classes = p.get_attribute("class") or ""
            if "lead" in p_classes and "wrap" in p_classes:
                continue
            if p.find_elements(By.TAG_NAME, "a"):
                continue
            text = p.text.strip()
            if text:
                full_desc_paragraphs.append(text)
        results["full_desc"] = "\n".join(full_desc_paragraphs)
    except Exception as e:
        print(f"Full description not found for {url}: {e}")
        results["full_desc"] = ""
    
    # --------------------------------------- PRICING INFORMATION (EURO) ---------------------------------------
    try:
        price_dd = driver.find_element(By.XPATH, "//dt[normalize-space(text())='Price']/following-sibling::dd")
        price_spans = price_dd.find_elements(By.XPATH, ".//span[contains(@class, 'currency-approx') or contains(@class, 'currency')]")
        price_texts = []
        for span in price_spans:
            text = span.text.strip()
            classes = span.get_attribute("class")
            if "currency-approx" in classes:
                text = "≈" + text
            price_texts.append(text)
        results["price_in_euro"] = " | ".join(price_texts)
    except Exception as e:
        print(f"Euro price not found for {url}: {e}")
        results["price_in_euro"] = ""
    
    # --------------------------------------- SWITCH TO USD AND SCRAPE PRICING ---------------------------------------
    try:
        usd_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, 'Display prices in $')]")))
        driver.execute_script("arguments[0].scrollIntoView();", usd_link)
        driver.execute_script("arguments[0].click();", usd_link)
        wait.until(lambda d: "$" in d.find_element(By.XPATH, "//dt[normalize-space(text())='Price']/following-sibling::dd").text)
        price_dd_usd = driver.find_element(By.XPATH, "//dt[normalize-space(text())='Price']/following-sibling::dd")
        price_spans_usd = price_dd_usd.find_elements(By.XPATH, ".//span[contains(@class, 'currency-approx') or contains(@class, 'currency')]")
        price_texts_usd = []
        for span in price_spans_usd:
            text = span.text.strip()
            classes = span.get_attribute("class")
            if "currency-approx" in classes:
                text = "≈" + text
            price_texts_usd.append(text)
        results["price_in_dollar"] = " | ".join(price_texts_usd)
    except Exception as e:
        print(f"Dollar price not found for {url}: {e}")
        results["price_in_dollar"] = ""
    
    # --------------------------------------- REVERT TO EURO CURRENCY ---------------------------------------
    try:
        euro_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, 'Display prices in €')]")))
        driver.execute_script("arguments[0].scrollIntoView();", euro_link)
        driver.execute_script("arguments[0].click();", euro_link)
        wait.until(lambda d: "€" in d.find_element(By.XPATH, "//dt[normalize-space(text())='Price']/following-sibling::dd").text)
    except Exception as e:
        print(f"Could not click to display Euro prices for {url}: {e}")
    
    # --------------------------------------- IMAGE EXTRACTION AND UPLOAD ---------------------------------------
    try:
        g_image_div = driver.find_element(By.CLASS_NAME, "g-image")
        a_tag = g_image_div.find_element(By.TAG_NAME, "a")
        relative_image_url = a_tag.get_attribute("href")
        if relative_image_url.startswith("/"):
            base_url = "https://modulargrid.net/"
            full_image_url = base_url + relative_image_url
        else:
            full_image_url= relative_image_url
        upload_result = cloudinary.uploader.upload(full_image_url)
        results["cloudinary_url"] = upload_result.get("secure_url", "")
    except Exception as e:
        print(f"Error uploading image for {url}: {e}")
        results["cloudinary_url"] = ""
    
    print(f"Finished scraping module ID {module_id}\n")
    return results

## Cloudinary Configuration

cloudinary.config(
    cloud_name = "cloud_name_here",
    api_key = "api_key_here",
    api_secret = "api_secret_here"
)

## Scraping

print("Setting up Webdriver and navigating to the search URL...")
chrome_options = Options()
chrome_options.add_argument("--headless") # comment this out if you want to see the browser being controlled by the code
driver = webdriver.Chrome(options=chrome_options)

### Currently Available

BASE_URL = "https://modulargrid.net"
SEARCH_URL_AVAILABLE = (
    "https://modulargrid.net/e/modules/browser?"
    "SearchName=&SearchVendor=&SearchFunction=&SearchSecondaryfunction=&SearchHeight=&SearchTe=&"
    "SearchTemethod=max&SearchBuildtype=a&SearchLifecycle=available&SearchSet=&SearchMarketplace=&"
    "SearchIsmodeled=0&SearchShowothers=0&SearchShowpanel=0&order=newest&direction=asc"
)

wait = WebDriverWait(driver, 3)

driver.get(SEARCH_URL_AVAILABLE)
time.sleep(3)

time.sleep(2)

ITEM_SELECTOR = ".box-module"

SCROLL_PAUSE_TIME = 5

scroll_to_bottom(wait_time=SCROLL_PAUSE_TIME)

elements = driver.find_elements(By.CSS_SELECTOR, ITEM_SELECTOR)
print(f"Scrolling complete. Total items found: {len(elements)}")

# Check to see if everything is in the view
if len(elements) < 7000:
    print(f"Expected at least 7000 items, but only found {len(elements)}. Exiting program, try rerunning.")
    sys.exit(1)

module_data = get_module_data()

available = []
skipped_urls = []

total_links = len(module_data)

driver.set_page_load_timeout(10)

for idx, module_info in enumerate(module_data, start=1):
    url = module_info['link']
    print(f"Processing link {idx} of {total_links}: {url}")

    try:
        driver.get(url)
    except TimeoutException:
        print(f"Skipping {url} due to timeout")
        skipped_urls.append(module_info)
        continue

    result = scrape_page(module_info, wait, driver)
    if result is None:
        print(f"Warning: Scrape function returned None for {module_info}")
    else:
        available.append(result)

print("\nScraping complete.")
print(f"Total modules processed: {len(available)}")
print(f"Number of originally skipped URLs: {len(skipped_urls)}")

available_df = pd.DataFrame(available)
available_df['product_lifecycle'] = 'Currently Available'

### Discontinued 

SEARCH_URL_DISCONTINUED = (
    "https://modulargrid.net/e/modules/browser?"
    "SearchName=&SearchVendor=&SearchFunction=&SearchSecondaryfunction=&SearchHeight=&SearchTe=&"
    "SearchTemethod=max&SearchBuildtype=a&SearchLifecycle=discontinued&SearchSet=&SearchMarketplace=&"
    "SearchIsmodeled=0&SearchShowothers=0&SearchShowpanel=0&order=newest&direction=asc"
)

wait = WebDriverWait(driver, 3)

driver.get(SEARCH_URL_DISCONTINUED)
time.sleep(3)

time.sleep(2)

try:
    alphabetic_button = driver.find_element(By.CSS_SELECTOR, "a[data-search-order='alphabetic']")
    alphabetic_button.click()
    time.sleep(2)
    
except Exception as e:
    print("Alphabetic sort button not found or click failed:", e)


ITEM_SELECTOR = ".box-module"

SCROLL_PAUSE_TIME = 5

scroll_to_bottom(wait_time=SCROLL_PAUSE_TIME)

elements = driver.find_elements(By.CSS_SELECTOR, ITEM_SELECTOR)
print(f"Scrolling complete. Total items found: {len(elements)}")

module_data_discontinued = get_module_data()

discontinued = []
skipped_urls_discontinued = []

total_links_discontinued = len(module_data_discontinued)

driver.set_page_load_timeout(10)

for idx, module_info in enumerate(module_data_discontinued, start=1):
    url = module_info['link']
    print(f"Processing link {idx} of {total_links_discontinued}: {url}")

    try:
        driver.get(url)
    except TimeoutException:
        print(f"Skipping {url} due to timeout")
        skipped_urls.append(module_info)
        continue

    result = scrape_page(module_info, wait, driver)
    if result is None:
        print(f"Warning: Scrape function returned None for {module_info}")
    else:
        discontinued.append(result)

print("\nScraping complete.")
print(f"Total modules processed: {len(discontinued)}")
print(f"Number of originally skipped URLs: {len(skipped_urls_discontinued)}")

discontinued_df = pd.DataFrame(discontinued)
discontinued_df['product_lifecycle'] = "Discontinued"

data = pd.concat([available_df, discontinued_df], ignore_index = True)

data.to_csv("product_df.csv", index=False)