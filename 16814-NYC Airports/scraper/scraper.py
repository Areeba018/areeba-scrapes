import os
import time
from datetime import datetime, timezone
import logging
import csv
import requests
import pandas as pd

# Configuration
base_url = " https://www.jfkairport.com/"
job_name = "Airport Security & Customs Wait Times Scraper"
output_filename = os.path.join("16814-NYC Airports", job_name.lower().replace(" ", "-") + "-data.csv")
scrape_datetime = datetime.now(timezone.utc)
proxy_address = os.environ.get("HTTP_PROXY")

script_path = os.path.realpath(__file__)
WORKING_DIR = os.path.dirname(script_path)

SECURITY_URLS = {
    "JFK": "https://avi-prod-mpp-webapp-api.azurewebsites.net/api/v1/SecurityWaitTimesPoints/JFK",
    "LGA": "https://avi-prod-mpp-webapp-api.azurewebsites.net/api/v1/SecurityWaitTimesPoints/LGA",
    "EWR": "https://avi-prod-mpp-webapp-api.azurewebsites.net/api/v1/SecurityWaitTimesPoints/EWR"
}

CUSTOMS_URLS = {
    "JFK": "https://avi-prod-mpp-webapp-api.azurewebsites.net/api/CustomClearanceTimesPoints/JFK",
    "LGA": "https://avi-prod-mpp-webapp-api.azurewebsites.net/api/CustomClearanceTimesPoints/LGA",
    "EWR": "https://avi-prod-mpp-webapp-api.azurewebsites.net/api/CustomClearanceTimesPoints/EWR"
}

job_name = "Airport Security & Customs Wait Times Scraper"
# output_filename = "airport_wait_times.csv"
scrape_datetime = datetime.now(tz=timezone.utc)

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Origin': 'https://www.jfkairport.com',
    'Referer': 'https://www.jfkairport.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

def retry_on_failure(func):
    def wrapper(*args, **kwargs):
        MAX_ATTEMPTS = 3
        attempts = MAX_ATTEMPTS
        while attempts > 0:
            try:
                response = func(*args, **kwargs)
                if response.status_code == 200:
                    return response
                else:
                    logging.error(f"Request failed. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts.")
                    attempts -= 1
                    time.sleep(10)
            except Exception as e:
                logging.error(f"An error occurred - Exception: {e}. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts.")
                attempts -= 1
                time.sleep(10)
        logging.warning(f"All attempts failed. Unable to make successful request.")
        return None
    return wrapper

class Scraper:
    def __init__(self):
        self.MASTER_LIST = []
        self.CLIENT = requests.Session()
        logging.info(f"STARTING SCRAPE... {job_name}")
        time.sleep(2)

    @retry_on_failure
    def make_request(self, url):
        return self.CLIENT.get(url, headers=headers, timeout=60)

    def scrape_data(self, urls, wait_time_type):
        for airport, url in urls.items():
            response = self.make_request(url)
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    for item in data:
                        self.MASTER_LIST.append({
                            "scrape_datetime": scrape_datetime,
                            "airport": airport,
                            "wait_time_type": wait_time_type,
                            "terminal": item.get("title", "Unknown"),
                            "wait_time_subtype": item.get("queueType", "Unknown"),
                            "wait_time_value": item.get("timeInMinutes", "Unknown")
                        })
                except requests.exceptions.JSONDecodeError:
                    logging.error(f"Invalid JSON response for {wait_time_type} wait times at {airport}")
            else:
                logging.error(f"Failed to retrieve {wait_time_type} wait times for {airport}")

    def start_scraper(self):
        self.scrape_data(SECURITY_URLS, "security")
        self.scrape_data(CUSTOMS_URLS, "customs")


def run(filename: str):
    scraper = Scraper()
    scraper.start_scraper()
    results = scraper.MASTER_LIST
    if len(results) < 1:
        logging.error("NO DATA SCRAPED. EXITING...")
        return
    df = pd.DataFrame(results)
    logging.info("GENERATING FINAL OUTPUT...")
    df.to_csv(filename, encoding="utf-8", quotechar='"', quoting=csv.QUOTE_ALL, index=False)

if __name__ == "__main__":
    run(filename=output_filename)
    logging.info("ALL DONE")
