# Scraping Instrument Website

This repository contains a single Python script, scraping_script.py, that scrapes module data from an online instrument marketplace (ModularGrid). The script collects information about both currently available and discontinued modules, then outputs a combined CSV file (`product_df.csv`) with the collected data.

## Overview

The `scraping_script.py` file:

1. Uses Selenium to automate a headless Chrome browser.
2. Scrolls through all search results to load every module on the page.
3. Extracts key data for each module:
   - Name, manufacturer, and descriptions
   - Availability status
   - Physical dimensions & power requirements
   - Pricing in both Euro and Dollar
   - Image links (uploaded to Cloudinary)
4. Combines results for both "currently available" and "discontinued" modules into a single DataFrame.
5. Writes final data to `product_df.csv`. 

## Requirements

- Python 3.7+
- Chrome Browser
- ChromeDriver
- Libraries
   - requests
   - selenium
   - pandas
   - beautifulsoup4
   - cloudinary

## Setup Instructions

1. Clone this repository

```bash
git clone https://github.com/merveogretmek/scraping_instrument_website.git
cd scraping_instrument_website
```

2. Install required packages

```bash
pip install selenium pandas beautifulsoup4 cloudinary
```

3. Download ChromeDriver
- Make sure to get the matching version for your installed Chrome.

4. Set Your Cloudinary Credentials

Within `scraping_script.py`, update the placeholder values:

```bash
cloudinary.config(
    cloud_name = "cloud_name_here",
    api_key = "api_key_here",
    api_secret = "api_secret_here"
)
```

## Usage

Run the script directly:

```bash
python scraping_script.py
```

1. The script launches a headless Chrome window.
2. Navigates to the "currently available" modules page and scrapes data.
3. Navigates to the "discounted" modules page and scrapes data.
4. Outputs the combined results into `product_df.csv`.

## Key Sections in `scraping_script.py`

- `scroll_to_bottom()`: Scrolls through the oage until all models are loaded.
- `get_module_data()`: Collects the IDs and links for each module from the loaded search results.
- `scrape_page()`: Visits each module page to parse its details (manufacturer, description, price, etc.). Uploads the primary product image to Cloudinary and retrieves its secure URL.
- Main Flow: Combines "currently available" and "discontinued" data into a final CSV.


Issues and pull requests are welcome. If you add or improve features, feel free to open a PR.










