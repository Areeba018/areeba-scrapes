import os
import time
import json
import logging
import random
import shutil
import csv
from datetime import datetime, timezone, timedelta

import requests
import pandas as pd

# region configuration
BASE_URL = "https://index.dongchedi.com/dzx_index/analyze/trend_top_event"
JOB_NAME = "Dongchedi Index Scraper"
output_filename = os.path.join("16800-Dongchedi Index", JOB_NAME.lower().replace(" ", "-") + "-data.csv")
SCRAPE_DATETIME = datetime.now(timezone.utc)
PROXY_ADDRESS = os.environ.get("HTTP_PROXY")

SCRIPT_PATH = os.path.realpath(__file__)
WORKING_DIR = os.path.dirname(SCRIPT_PATH)
# endregion

# region DECORATORS
def retry_on_failure(func):
    def wrapper(*args, **kwargs):
        MAX_ATTEMPTS = 3
        attempts = MAX_ATTEMPTS
        while attempts > 0:
            try:
                logging.info(f"Requesting URL: {args[1]}")
                time.sleep(random.uniform(2.5, 3.5))
                response = func(*args, **kwargs)
                if response and response.status_code == 200:
                    return response
                else:
                    logging.error(f"Request failed. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts.")
                    attempts -= 1
                    time.sleep(10)
            except Exception as e:
                logging.error(f"An error occurred - Exception: {e}. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts.")
                attempts -= 1
                time.sleep(10)
        logging.warning(f"All attempts failed. Unable to make successful request. URL: {args[1]}")
        return None
    return wrapper
# endregion

# region Scraper_Class
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



    # region REQUESTS_SESSION_FUNCTIONS
    def make_session(self, headers=None):
        session = requests.Session()
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Referer": "https://index.dongchedi.com/",
            "Accept": "application/json",
        }
        session.headers.update(headers or default_headers)
        return session

    @retry_on_failure
    def make_request(self, url, method="GET", data=None):
        if method == "GET":
            return self.CLIENT.get(url, timeout=60)
        elif method == "POST" and data:
            return self.CLIENT.post(url, data=data, timeout=60)
        return None
    # endregion

    # region HELPER FUNCTIONS
    def create_dir(self, path):
        dir_path = os.path.join(WORKING_DIR, path)
        try:
            dir_path = os.path.abspath(dir_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logging.info(f'Folder {path} created in {dir_path}')
            else:
                logging.info(f'Folder {path} already exists in {dir_path}')
        except Exception as ex:
            logging.error(f"Error creating folder {path} | Exception: {ex}")
        finally:
            return dir_path

    def remove_dir(self, path):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                logging.info(f'{path} removed successfully.')
            else:
                logging.info(f'{path} does not exist...')
        except Exception as ex:
            logging.error(f"Failed to delete directory: {path} | Exception: {ex}")
    # endregion

    # region MAIN SCRAPER LOGIC
    def generate_url(self, brand_id, start_date, end_date):
        return f"{BASE_URL}?rank_type=%E5%93%81%E7%89%8C%E6%A6%9C%E5%8D%95&id_list={brand_id}&province=%E5%85%A8%E5%9B%BD&start_date={start_date}&end_date={end_date}"

    def fetch_avg_value(self, brand_id, start_date, end_date):
        url = self.generate_url(brand_id, start_date, end_date)
        logging.info(f"Fetching data from URL: {url}")

        response = self.make_request(url)
        if response and response.status_code == 200:
            try:
                data = response.json()
                avg_value = data.get("data", {}).get("event", {}).get(str(brand_id), {}).get("avg_value", None)
                return avg_value
            except (json.JSONDecodeError, KeyError):
                logging.error(f"Error parsing avg_value for brand_id: {brand_id}")
                return None
        else:
            logging.error(f"Failed to fetch avg_value for brand_id {brand_id}. Status Code: {response.status_code if response else 'N/A'}")
            return None

    def scrape_data(self):
        latest_date = datetime.today().date()
        start_date = datetime(2021, 1, 1).date()
        logging.info(f"Scraping data from {start_date} to {latest_date}")

        # Load JSON file with brands
        json_path = os.path.join(os.path.dirname(__file__), "brands.json")
        with open(json_path, "r", encoding="utf-8") as file:
            BRANDS_DATA = json.load(file)

        data = []

        # Iterate backward, collecting data year by year
        current_date = latest_date
        # while current_date >= start_date:
        while current_date.year > 2021:  # Stops before reaching 2021
            end_date = current_date.strftime("%Y-%m-%d")
            start_of_year = current_date.replace(year=current_date.year - 1).strftime("%Y-%m-%d")

            logging.info(f"\n🔄 Processing data from {start_of_year} to {end_date}...")

            for brand in BRANDS_DATA:
                brand_name = brand["outter_brand_name"]
                brand_id = brand["outter_brand_id"]
                for series in brand["series"]:  # Iterate through the series list
                    series_name = series["series_name"]

                logging.info(f"Fetching avg_value for {brand_name} (ID: {brand_id})...")

                avg_value = self.fetch_avg_value(brand_id, start_of_year, end_date)

                if avg_value is not None:
                    data.append({
                        "scrape_datetime": datetime.utcnow().isoformat(),
                        "data_date": end_date,
                        "brand": brand_name,
                        "model":series_name,
                        # "start_date": start_of_year,
                        "avg_value": avg_value,
                    })

            # Move back one year
            current_date = current_date.replace(year=current_date.year - 1)

        return data
    # endregion

    # region START SCRAPER
    def start_scraper(self):
        results = self.scrape_data()
        if len(results) < 1:
            logging.error("NO DATA SCRAPED. EXITING...")
            return

        df = pd.DataFrame(results)

        logging.info("GENERATING FINAL OUTPUT...")
        df.to_csv(output_filename, encoding="utf-8", quotechar='"', quoting=csv.QUOTE_ALL, index=False)
        logging.info("\n✅ Scraping completed. Data saved.")

def run():
    scraper = Scraper()
    scraper.start_scraper()


if __name__ == "__main__":
    run()
    logging.info("ALL DONE")
