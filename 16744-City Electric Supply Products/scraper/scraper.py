import os
import json
import csv
from curl_cffi import requests  # Install: pip install curl-cffi
from bs4 import BeautifulSoup
import datetime
from datetime import datetime, timezone, timedelta


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

def scrape_products(base_url):
    response = requests.get(base_url, headers=HEADERS, impersonate="chrome110")
    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="product-item")
    
    product_details = {}
    time_ids = []
    stock_ids = []
    
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
                    product_details[ims_id] = {
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
    
    return product_details, time_ids, stock_ids

def fetch_prices(time_ids):
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

def fetch_availability(stock_ids):
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

def save_to_csv(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "scrape_datetime", "base_url", "category", "product_url", "product_name", 
            "catalog_code", "stock_code", "availability", "buying_option", "price"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    all_products = []
    for base_url in BASE_URLS:
        product_details, time_ids, stock_ids = scrape_products(base_url)
        imsid_to_price = fetch_prices(time_ids)
        stock_availability = fetch_availability(stock_ids)
        
        for ims_id, details in product_details.items():
            details["price"] = imsid_to_price.get(ims_id, "N/A")
            details["availability"] = stock_availability.get(details["stock_code"], "N/A")
            all_products.append(details)
    
    save_to_csv(all_products, OUTPUT_FILE)
    print(f"✅ Scraping completed. Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
