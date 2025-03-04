import os
import time
import json
import logging
import random
import csv
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

# Constants
BASE_URL = "https://index.dongchedi.com/dzx_index/analyze/trend"
JOB_NAME = "16800 Dongchedi Index Scrape using Requests"
output_filename = os.path.join(
    "16800-Dongchedi Index",
    JOB_NAME.split("using")[0].strip().lower().replace(" ", "-") + "-sample.csv",
)
SCRAPE_DATETIME = datetime.now(timezone.utc)


def retry_on_failure(func):
    """Decorator to retry failed requests."""
    def wrapper(*args, **kwargs):
        MAX_ATTEMPTS = 3
        attempts = MAX_ATTEMPTS
        while attempts > 0:
            try:
                time.sleep(random.uniform(1.5, 2.5))  # Shorter delay for speed
                response = func(*args, **kwargs)
                if response and response.status_code == 200:
                    return response
                else:
                    logging.error(
                        f"Request failed. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts."
                    )
                    attempts -= 1
                    time.sleep(5)
            except Exception as e:
                logging.error(
                    f"An error occurred - Exception: {e}. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts."
                )
                attempts -= 1
                time.sleep(5)
        logging.warning(f"All attempts failed. Unable to make successful request.")
        return None

    return wrapper


class Scraper:
    def __init__(self, historical=False):
        self.MASTER_LIST = []
        self.HISTORICAL = historical
        self.CLIENT = self.make_session()
        self.setup_logging()

    def setup_logging(self):
        """Sets up logging configuration."""
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
            datefmt="%d-%b-%y %H:%M:%S",
        )
        logging.info(f"STARTING SCRAPE... {JOB_NAME} | HISTORICAL: {self.HISTORICAL}")
        time.sleep(2)

    def make_session(self, headers=None):
        """Creates a session with default headers."""
        session = requests.Session()
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Referer": "https://index.dongchedi.com/",
            "Accept": "application/json",
        }
        session.headers.update(headers or default_headers)
        return session

    @retry_on_failure
    def make_request(self, url, params=None):
        """Performs an HTTP GET request."""
        return self.CLIENT.get(url, params=params, timeout=60)
    
    def get_rank_type(self, brand_id, series_id):
        params = {
            'outter_brand_id': brand_id,
            'series_id': series_id,
        }
        try:
            response = self.CLIENT.get("https://index.dongchedi.com/dzx_index/menu/rank_type", 
                                       params=params,  timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 0 and "menu" in data.get("data", {}):
                    menu_list = data["data"]["menu"]
                    if menu_list and len(menu_list) > 0:
                        rank_type = menu_list[0]["value"] + "榜单"
                       
                        return rank_type
                    else:
                        logging.warning("Menu list is empty. No rank type available.")
                        return None
                else:
                    logging.error("Invalid response format.")
            else:
                logging.error(f"Request failed with status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error fetching rank type: {e}")

    def fetch_full_year_data(self, brand_id, brand_name, series_id, series_name, year):
        """Fetches a full year's data in one API call and processes it."""
        rank_type = self.get_rank_type(brand_id, series_id)
        params = {
            "date": f"{year}-01-01",  # Fetch full year data
            "province": "全国",
            "rank_type": {rank_type},
            "sub_rank_type": "",
            "id_list": series_id if series_id != -1 else brand_id,
            "name_list": brand_name,
        }

        response = self.make_request(BASE_URL, params=params)

        if not response:
            logging.error(f"❌ Request failed for {year} - {brand_name} - {series_name}")
            return

        data = response.json()

        x_axis = data["data"].get("x_axis", [])
        chart_data = data["data"].get("chart_data", [])

        if not chart_data or not x_axis:
            return  # Skip if no data

        values = chart_data[0].get("value", [])

        if len(x_axis) != len(values):
            return  # Skip if mismatch in data length

        for i in range(len(x_axis)):
            self.MASTER_LIST.append(
                {
                    "scrape_datetime": SCRAPE_DATETIME.isoformat(),
                    "data_date": x_axis[i],
                    "brand": brand_name,
                    "model": series_name,
                    "value": values[i],
                }
            )

        logging.info(f"✅ Data for {year} - {brand_name} - {series_name} saved successfully.")

    def generate_years_list(self):
        """Generates a list of years to scrape from."""
        current_year = SCRAPE_DATETIME.year
        start_year = 2021 if self.HISTORICAL else current_year  # If historical, scrape from 2021
        return list(range(current_year, start_year - 1, -1))  # Latest year first

    def scrape_data(self):
        """Loops through all years, then all brands & models for each year."""
        json_path = os.path.join(os.path.dirname(__file__), "brands.json")

        with open(json_path, "r", encoding="utf-8") as file:
            BRANDS_DATA = json.load(file)

        years = self.generate_years_list()

        # **PRIORITIZE LATEST YEAR FIRST**
        for year in years:
            for brand in BRANDS_DATA:
                brand_name = brand["outter_brand_name"]
                brand_id = brand["outter_brand_id"]

                for series in brand["series"]:
                    series_id = series["series_id"]
                    series_name = series["series_name"]

                    self.fetch_full_year_data(brand_id, brand_name, series_id, series_name, year)

    def start_scraper(self):
        """Runs the scraper and saves results."""
        self.scrape_data()
        self.save_results()

    def save_results(self):
        """Saves extracted data to CSV."""
        if not self.MASTER_LIST:
            logging.error("NO DATA SCRAPED. EXITING...")
            return

        df = pd.DataFrame(self.MASTER_LIST)

        logging.info("GENERATING FINAL OUTPUT...")
        df.to_csv(
            output_filename,
            encoding="utf-8",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            index=False,
        )

        logging.info(f"📂 Data saved to {output_filename}")


def run(historical=False):
    scraper = Scraper(historical=historical)
    scraper.start_scraper()


if __name__ == "__main__":
    run(historical=True)  # Change to `False` for recent data only
    logging.info("ALL DONE")
