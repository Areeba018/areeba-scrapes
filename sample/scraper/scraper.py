import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
import logging
import csv

import requests
import pandas as pd
from bs4 import BeautifulSoup


base_url = f"https://www.covers.com/sport/football/nfl/odds"
job_name = "16494 Covera Ryan GPD Scrape using requests"
output_filename = (
    job_name.split("using")[0].strip().lower().replace(" ", "-") + "-sample.csv"
)
scrape_datetime = datetime.now(tz=timezone.utc)

headers = {
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
                    logging.error(
                        f"Request failed. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts."
                    )
                    attempts -= 1
                    time.sleep(10)
            except Exception as e:
                logging.error(
                    f"An error occurred - Exception: {e}. Retrying {MAX_ATTEMPTS - attempts + 1}/{MAX_ATTEMPTS} attempts."
                )
                attempts -= 1
                time.sleep(10)
        logging.warning(
            f"All attempts failed. Unable to make successful request. URL: {args[1]}"
        )
        return None

    return wrapper


class Scraper:
    def __init__(self):
        self.MASTER_LIST = []
        self.CLIENT = None

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

        logging.info(f"STARTING SCRAPE... {job_name}")
        time.sleep(2)

    def make_session(self, headers=None):
        s = requests.Session()
        if headers is not None:
            s.headers.update(headers)

        return s

    @retry_on_failure
    def make_request(self, url, method="GET", data=None):
        res = None
        if method == "GET":
            res = self.CLIENT.get(url, timeout=60)
        elif (method == "POST") and (data is not None):
            res = self.CLIENT.post(url, data=data, timeout=60)
        return res

    def scrape_data(self, base_url: str):
        pass

    def start_scraper(self):
        page_url = f"{base_url}"
        self.scrape_data(page_url)


def run(filename: str):
    scraper = Scraper()
    scraper.start_scraper()

    results = scraper.MASTER_LIST
    if len(results) < 1:
        logging.error("NO DATA SCRAPED. EXITING...")
        return

    df = pd.DataFrame(results)
    logging.info("GENERATING FINAL OUTPUT...")
    df.to_csv(
        filename,
        encoding="utf-8",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
        index=False,
    )


if __name__ == "__main__":
    run(filename=output_filename)
    logging.info("ALL DONE")
