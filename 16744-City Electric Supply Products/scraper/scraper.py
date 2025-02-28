
import os
import json
import csv
from curl_cffi import requests  # Install: pip install curl-cffi
from bs4 import BeautifulSoup
import datetime
from datetime import datetime, timezone, timedelta
import time
import logging
import random

import pandas as pd


# URLs to scrape
BASE_URLS = [
    "https://www.cityelectricsupply.com/tffn-building-wire",
    "https://www.cityelectricsupply.com/thhn-wire",
    "https://www.cityelectricsupply.com/nm-b-wire",
    "https://www.cityelectricsupply.com/aluminum-armor",
    "https://www.cityelectricsupply.com/urd",
    "https://www.cityelectricsupply.com/ser-aluminum",
    "https://www.cityelectricsupply.com/wire-cord-cable",
]

JOB_NAME = "City Electric Supply Products"
OUTPUT_FILE = os.path.join("16744-City Electric Supply Products", JOB_NAME.lower().replace(" ", "-") + "-data.csv")
SCRAPE_DATETIME = datetime.now(timezone.utc)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.cityelectricsupply.com/",
    "Origin": "https://www.cityelectricsupply.com",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

class Scraper:
    def __init__(self):
        self.MASTER_LIST = []
        self.DOWNLOAD_DIR = None
        self.CLIENT = self.make_session()
        
        self.DEBUG = False
        if self.DEBUG:
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                level=logging.DEBUG,
                datefmt="%d-%b-%y %H:%M:%S",
            )
        else:
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                level=logging.INFO,
                datefmt="%d-%b-%y %H:%M:%S",
            )

        logging.info(f"STARTING SCRAPE... {JOB_NAME}")
        time.sleep(2)
    
    def make_session(self, headers=None):
        session = requests.Session()
        default_headers = HEADERS
        session.headers.update(headers or default_headers)
        return 
    
    def make_request(self, url, method="GET", data=None):
        if method == "GET":
            return self.CLIENT.get(url, timeout=60)
        elif method == "POST" and data:
            return self.CLIENT.post(url, data=data, timeout=60)
        return None
    
    def fetch_html(self,url):
        """Fetch the HTML content of a page."""
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.text
        return None



    def scrape_products(self, base_url):
        """Scrape all products from paginated pages, handling subcategories if necessary."""
        all_products = {}
        time_ids = []
        stock_ids = []

        # Check if this URL requires subcategory extraction
        if base_url in [
            "https://www.cityelectricsupply.com/thhn-wire",
            # "https://www.cityelectricsupply.com/wire-cord-cable"
        ]:
            response = requests.get(base_url, headers=HEADERS, impersonate="chrome110")
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract subcategory links
            subcategories = soup.select(".sub-category-item a")
            if subcategories:
                subcategory_urls = [
                    f"https://www.cityelectricsupply.com{a['href']}" for a in subcategories if 'href' in a.attrs
                ]
                
                for sub_url in subcategory_urls:
                    print(f"🔄 Visiting subcategory: {sub_url}")
                    sub_product_details, sub_time_ids, sub_stock_ids = self.scrape_products(sub_url)
                    all_products.update(sub_product_details)
                    time_ids.extend(sub_time_ids)
                    stock_ids.extend(sub_stock_ids)

                return all_products, time_ids, stock_ids  # Return early since we handled subcategories

        if base_url in [
                    "https://www.cityelectricsupply.com/wire-cord-cable"
                ]:
            response = requests.get(base_url, headers=HEADERS, impersonate="chrome110")
            soup = BeautifulSoup(response.text, "html.parser")


            # Extract subcategory links
            subcategories = soup.select(".sub-category-item a")
            # print(subcategories)
            if subcategories:
                subcategory_urls = [
                    f"https://www.cityelectricsupply.com{a['href']}" for a in subcategories if 'href' in a.attrs
                ]
                print(subcategory_urls)

                sub_subcategory_urls = []  # Initialize empty list to store sub-subcategory URLs

                for subcategory_url in subcategory_urls:
                    # Extract sub-subcategory links
                    response = requests.get(subcategory_url, headers=HEADERS, impersonate="chrome110")
                    sub_soup = BeautifulSoup(response.text, "html.parser")

                    sub_subcategories = sub_soup.select(".category-grid.sub-category-grid .item-box .sub-category-item h2.title a")
                    # print(sub_subcategories)

                    if sub_subcategories:
                        sub_subcategory_urls = [
                            f"https://www.cityelectricsupply.com{a['href']}" for a in sub_subcategories if 'href' in a.attrs
                        ]
                        print("subbbb:",sub_subcategory_urls)
                        for sub_url in sub_subcategory_urls:
                            print(f"🔄 Visiting subcategory: {sub_url}")
                            sub_product_details, sub_time_ids, sub_stock_ids = self.scrape_products(sub_url)
                            all_products.update(sub_product_details)
                            time_ids.extend(sub_time_ids)
                            stock_ids.extend(sub_stock_ids)

                        return all_products, time_ids, stock_ids  # Return early since we handled subcategories


                    
        # Normal product scraping (if no subcategories or for other URLs)
        next_page = base_url  

        while next_page:
            print(f"Scraping: {next_page}")  # Debugging info
            response = requests.get(next_page, headers=HEADERS, impersonate="chrome110")
            
            if response.status_code != 200:
                print(f"Failed to fetch {next_page}")
                break
            
            soup = BeautifulSoup(response.text, "html.parser")
            products = soup.find_all("div", class_="product-item")

            for product in products:
                link = product.find("a", class_="search-page-product")
                stock_code = product.get("data-productsku", "No Stock Code")

                description_div = product.find("div", class_="description")
                description_items = [li.get_text(strip=True) for li in description_div.find_all("li")] if description_div else []
                buying_option = ", ".join(description_items)

                category_input = product.find("input", {"id": "impression"})
                catalog_code = "No Catalog Code"
                product_category = "No Product Category"
                ims_id = ""

                if category_input and category_input.has_attr("value"):
                    try:
                        category_data = json.loads(category_input["value"])
                        catalog_code = category_data.get("ManufacturerPartNumber", "No Catalog Code")
                        product_category = category_data.get("Category3", "No Category")
                        ims_id = str(category_data.get("Id", ""))

                        if ims_id:
                            time_ids.append(ims_id)
                            all_products[ims_id] = {
                                "scrape_datetime": SCRAPE_DATETIME,
                                "base_url": base_url,
                                "category": product_category,
                                "product_url": "https://www.cityelectricsupply.com" + link["href"] if link and link.has_attr("href") else "No URL",
                                "product_name": link["title"] if link and link.has_attr("title") else "No Title",
                                "catalog_code": catalog_code,
                                "stock_code": stock_code,
                                "availability": "N/A",
                                "buying_option": buying_option,
                                "price": "N/A"
                            }

                        if stock_code:
                            stock_ids.append(stock_code)
                    except json.JSONDecodeError:
                        pass

            # Pagination Handling: Find next page
            next_page_element = soup.select_one(".next-page a")
            next_page = f"https://www.cityelectricsupply.com{next_page_element['href']}" if next_page_element else None

        return all_products, time_ids, stock_ids

    def fetch_prices(self,time_ids):
        """Fetch product prices."""
        imsid_to_price = {}
        if time_ids:
            price_url = "https://www.cityelectricsupply.com/product/lazyprice"
            json_data = {"imsIds": time_ids}
            price_response = requests.post(price_url, headers=HEADERS, json=json_data)
            
            if price_response.status_code == 200:
                try:
                    price_data = price_response.json()
                    for item in price_data:
                        ims_id = str(item.get("ImsId", ""))
                        display_price = item.get("DisplayPrice", "N/A")
                        if ims_id:
                            imsid_to_price[ims_id] = display_price
                except json.JSONDecodeError:
                    pass
        return imsid_to_price

    def fetch_availability(self,stock_ids):
        """Fetch stock availability."""
        stock_availability = {}
        if stock_ids:
            avail_url = "https://www.cityelectricsupply.com/product/lazyinventory"
            json_data = {"skus": stock_ids}
            avail_response = requests.post(avail_url, headers=HEADERS, json=json_data)
            
            if avail_response.status_code == 200:
                try:
                    avail_data = avail_response.json()
                    for item in avail_data:
                        sku = item.get("Sku")
                        quantity = item.get("Total", 0)
                        location_stocks = item.get("Overview", {}).get("LocationStocks", [])
                        
                        if location_stocks:
                            quantity = location_stocks[0].get("Quantity", 0)
                        
                        stock_availability[sku] = f"Available: ({quantity} Feet)"
                except json.JSONDecodeError:
                    pass
        return stock_availability

    def save_to_csv(self,data, filename):
        """Save scraped data to a CSV file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "scrape_datetime", "base_url", "category", "product_url", "product_name", 
                "catalog_code", "stock_code", "availability", "buying_option", "price"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def start_scraper(self):
        """Main function to scrape all products with pagination."""
        all_products = []
        for base_url in BASE_URLS:
            product_details, time_ids, stock_ids = self.scrape_products(base_url)
            imsid_to_price = self.fetch_prices(time_ids)
            stock_availability = self.fetch_availability(stock_ids)

            for ims_id, details in product_details.items():
                details["price"] = imsid_to_price.get(ims_id, "N/A")
                details["availability"] = stock_availability.get(details["stock_code"], "N/A")

                # ✅ Only override base_url for "https://www.cityelectricsupply.com/wire-cord-cable" because at this url, data drom from sub_sub_category
                if "wire-cord-cable" in base_url:
                    details["base_url"] = "https://www.cityelectricsupply.com/wire-cord-cable"
                else:
                    details["base_url"] = base_url  # Keep actual base URL for others


                all_products.append(details)

        self.MASTER_LIST = all_products  # ✅ Save to MASTER_LIST
        self.save_to_csv(all_products, OUTPUT_FILE)
        print(f"✅ Scraping completed. Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    scraper = Scraper()
    scraper.start_scraper()

    results = scraper.MASTER_LIST
    if len(results) == 0:
        logging.error("NO DATA SCRAPED. EXITING...")
        
    df = pd.DataFrame(results)

    logging.info("GENERATING FINAL OUTPUT...")
    df.to_csv(
        OUTPUT_FILE,
        encoding="utf-8",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
        index=False,
    )
    logging.info("✅ Scraping completed.")
