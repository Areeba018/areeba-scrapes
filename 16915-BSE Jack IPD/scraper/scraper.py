import os
import time
import logging
import random
import csv
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://www.bseindia.com/markets/Derivatives/DeriReports/DeriHistoricalConsolidate.aspx"
JOB_NAME = "16915 BSE Jack IPD using requests"
output_filename = os.path.join(
    "16915-BSE Jack IPD",
    JOB_NAME.split("using")[0].strip().lower().replace(" ", "-") + "-sample.csv",
)
SCRAPE_DATETIME = datetime.now(timezone.utc)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%d-%b-%y %H:%M:%S",
)
logging.info(f"STARTING SCRAPE... {JOB_NAME}")

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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        }
        session.headers.update(headers or default_headers)
        return session

    @retry_on_failure
    def make_request(self, url, params=None):
        return self.CLIENT.get(url, params=params, timeout=60)

    def scrape_data(self):
        """Scrapes BSE Derivatives Data and writes to CSV file."""
        # Date range: Start from 2025-02-01 and fetch data month by month until today
        start_date = datetime(2025, 1, 1)
        today = datetime.today()

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_filename)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Open CSV file for writing
        with open(output_filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Write CSV Header
            writer.writerow(["scrape_datetime", "instrument_type", "date", "number_of_trades", "volume", "notional_turnover", "premium_turnover"])


            # Loop through each month
            while start_date < today:
                # Set the date range for one month
                from_date = start_date.strftime('%d/%m/%Y')
                next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
                to_date = min(next_month, today).strftime('%d/%m/%Y')

                _ = self.make_request('https://www.bseindia.com/')
                # Perform GET request to fetch the page
                time.sleep(random.uniform(2, 4))
                response = self.make_request(BASE_URL)
                if response.status_code != 200:
                    print("❌ Failed to load the page!")
                    exit()

                soup = BeautifulSoup(response.text, 'html.parser')
                # print(soup)

                # Extract hidden input values
                def get_hidden_value(soup, name):
                    input_tag = soup.find("input", {"name": name})
                    return input_tag["value"] if input_tag else ""

                viewstate = get_hidden_value(soup, "__VIEWSTATE")
                eventvalidation = get_hidden_value(soup, "__EVENTVALIDATION")
                viewstategenerator = get_hidden_value(soup, "__VIEWSTATEGENERATOR")

                # Print hidden values
                print("\n🔍 Hidden Values Found:")
                print(f"VIEWSTATE: {viewstate[:100]}...")  # Print first 100 chars for readability
                print(f"EVENTVALIDATION: {eventvalidation[:100]}...")
                print(f"VIEWSTATEGENERATOR: {viewstategenerator}\n")

                # Extract Segment and Instrument dropdown options
                # segment_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlsegment")
                # segment_options = {opt.get("value"): opt.text.strip() for opt in segment_dropdown.find_all("option") if opt.get("value")}
                # instrument_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlIntrument")
                # instrument_options = {opt.get("value"): opt.text.strip() for opt in instrument_dropdown.find_all("option") if opt.get("value")}
               
                filters = [
                    {"segment_name":"Index Derivative","segment_code": "ID", "segments":  {"Index Futures": "IF", "Index Options": "IO"}},
                    {"segment_name":"Equity Derivative","segment_code": "ED", "segments":  {"Equity Futures": "SF", "Index Options": "SO"}},
                ]


                for filter in filters:
                    for instrument, code in filter["segments"].items():
                        # Prepare data payload
                        data = {
                            'ctl00$ContentPlaceHolder1$ddlsegment': filter['segment_name'],
                            'ctl00$ContentPlaceHolder1$ddlIntrument': code,
                            'ctl00$ContentPlaceHolder1$ddlUnderLine': '0',
                            'ctl00$ContentPlaceHolder1$txtDate': from_date,
                            'ctl00$ContentPlaceHolder1$txtTodate': to_date,
                            'ctl00$ContentPlaceHolder1$btnGo': 'Go',
                            '__VIEWSTATE': viewstate,
                            '__VIEWSTATEGENERATOR': viewstategenerator,
                            '__EVENTVALIDATION': eventvalidation,
                        }

                        print(f"📡 Fetching data for Segment: {filter['segment_name']}, Instrument: {instrument} From Date: {from_date} to {to_date}...")

                        # Send POST request
                        time.sleep(random.uniform(2, 3))
                        response = self.CLIENT.post(BASE_URL, headers=self.CLIENT.headers, data=data)

                        # ✅ Check if request was successful
                        if response.status_code == 200:
                            bs = BeautifulSoup(response.text, 'html.parser')
                            # Find table with data
                            table = bs.find("table", {"width": "100%"})

                            if table:
                                rows = table.find_all("tr")[1:]  # Skip header row

                                for row in rows:
                                    cols = row.find_all("td")

                                    # Ensure row has valid data (ignoring duplicate headers)
                                    if len(cols) >= 5 and "Trade DateNum" not in cols[0].text:
                                        trade_date = cols[0].text.strip()
                                        num_trades = cols[1].text.strip().replace(',', '')  # Remove commas
                                        volume = cols[2].text.strip().replace(',', '')  # Remove commas
                                        notional_turnover = cols[3].text.strip().replace(',', '')  # Remove commas
                                        premium_turnover = cols[4].text.strip().replace(',', '')  # Remove commas

                                        # Append data to MASTER_LIST for later processing
                                        self.MASTER_LIST.append([
                                            SCRAPE_DATETIME.isoformat(),
                                            instrument,  # Instrument type
                                            trade_date,
                                            num_trades,
                                            volume,
                                            notional_turnover,
                                            premium_turnover
                                        ])
                                        print(f"📡 ✅ Data saved for Segment: {filter['segment_name']}, Instrument: {instrument} From Date: {from_date} to {to_date}...")
                            

                            else:
                                print(f"⚠️ No data table found for {filter['segment_name']} - {instrument}")
                            
                            # for next requuest
                            viewstate = get_hidden_value(bs, "__VIEWSTATE")
                            eventvalidation = get_hidden_value(bs, "__EVENTVALIDATION")
                            viewstategenerator = get_hidden_value(bs, "__VIEWSTATEGENERATOR")
                            print(f"VIEWSTATE: {viewstate[:100]}...")


                        else:
                            print(f"❌ Failed to fetch data for {filter['segment_name']} - {instrument} From Date: {from_date} to {to_date}...")
                            time.sleep(random.uniform(60, 120))
                            self.CLIENT = self.make_session()
                # Move to the next month
                start_date = next_month

        print("✅ Data extraction completed! Check 'BSE_Derivatives_Data.csv'.")

    def start_scraper(self):
        """Runs the scraper"""
        self.scrape_data()


def run(filename: str):
    scraper = Scraper(historical=True)
    scraper.start_scraper()

    results = scraper.MASTER_LIST
    if len(results) == 0:
        logging.error("NO DATA SCRAPED. EXITING...")
        return

    # Define columns explicitly
    columns = ["scrape_datetime", "instrument_type", "date", "number_of_trades", "volume", "notional_turnover", "premium_turnover"]

    # Create DataFrame with specified columns
    df = pd.DataFrame(results, columns=columns)
    logging.info("GENERATING FINAL OUTPUT...")

    # Write DataFrame to CSV with headers and no extra index column
    df.to_csv(
        filename,
        encoding="utf-8",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
        index=False,  # Ensure index is not written to the CSV
    )


if __name__ == "__main__":
    run(filename=output_filename)  # Change to `False` for recent data only
    logging.info("ALL DONE")

