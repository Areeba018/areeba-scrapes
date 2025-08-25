# import requests
# import csv
# from bs4 import BeautifulSoup
# from datetime import datetime, timedelta

# # BSE Derivatives URL
# BASE_URL = "https://www.bseindia.com/markets/Derivatives/DeriReports/DeriHistoricalConsolidate.aspx"

# # Headers to mimic a real browser
# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
#     'Referer': BASE_URL,
#     'Origin': 'https://www.bseindia.com',
#     'Content-Type': 'application/x-www-form-urlencoded',
# }

# # Date range: Start from 2025-02-01 and fetch data month by month until today
# start_date = datetime(2025, 2, 1)
# today = datetime.today()

# # Open CSV file for writing
# with open("BSE_Derivatives_Data.csv", "w", newline="", encoding="utf-8") as file:
#     writer = csv.writer(file)
    
#     # Write CSV Header
#     writer.writerow(["scrape_datetime", "instrument_type", "date", "number_of_trades", "volume", "notional_turnover", "premium_turnover"])

#     # Create a session to maintain cookies
#     session = requests.Session()

#     # Loop through each month
#     while start_date < today:
#         # Set the date range for one month
#         from_date = start_date.strftime('%d/%m/%Y')
#         next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
#         to_date = min(next_month, today).strftime('%d/%m/%Y')

#         # Perform GET request to fetch the page
#         response = session.get(BASE_URL, headers=headers)
#         if response.status_code != 200:
#             print("❌ Failed to load the page!")
#             exit()

#         soup = BeautifulSoup(response.text, 'html.parser')
#         # print(soup)  # Print the entire page HTML (for debugging)

#         # Extract hidden input values
#         def get_hidden_value(name):
#             input_tag = soup.find("input", {"name": name})
#             return input_tag["value"] if input_tag else ""

#         viewstate = get_hidden_value("__VIEWSTATE")
#         eventvalidation = get_hidden_value("__EVENTVALIDATION")
#         viewstategenerator = get_hidden_value("__VIEWSTATEGENERATOR")

#         # Print hidden values
#         print("\n🔍 Hidden Values Found:")
#         print(f"VIEWSTATE: {viewstate[:100]}...")  # Print first 100 chars for readability
#         print(f"EVENTVALIDATION: {eventvalidation[:100]}...")
#         print(f"VIEWSTATEGENERATOR: {viewstategenerator}\n")

#         # Extract Segment and Instrument dropdown options
#         segment_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlsegment")
#         segment_options = {opt.get("value"): opt.text.strip() for opt in segment_dropdown.find_all("option") if opt.get("value")}

#         instrument_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlIntrument")
#         instrument_options = {opt.get("value"): opt.text.strip() for opt in instrument_dropdown.find_all("option") if opt.get("value")}

#         # Iterate over all segment and instrument combinations
#         for segment, segment_name in segment_options.items():
#             for instrument, instrument_name in instrument_options.items():
#                 # Prepare data payload
#                 data = {
#                     'ctl00$ContentPlaceHolder1$ddlsegment': segment,
#                     'ctl00$ContentPlaceHolder1$ddlIntrument': instrument,
#                     'ctl00$ContentPlaceHolder1$ddlUnderLine': '0',
#                     'ctl00$ContentPlaceHolder1$txtDate': from_date,
#                     'ctl00$ContentPlaceHolder1$txtTodate': to_date,
#                     'ctl00$ContentPlaceHolder1$btnGo': 'Go',
#                     '__VIEWSTATE': viewstate,
#                     '__VIEWSTATEGENERATOR': viewstategenerator,
#                     '__EVENTVALIDATION': eventvalidation,
#                 }

#                 print(f"📡 Fetching data for Segment: {segment_name}, Instrument: {instrument_name} From Date: {from_date} to {to_date}...")

#                 # Send POST request
#                 response = session.post(BASE_URL, headers=headers, data=data)

#                 # ✅ Check if request was successful
#                 if response.status_code == 200:
#                     soup = BeautifulSoup(response.text, 'html.parser')

#                     # Find table with data
#                     table = soup.find("table", {"width": "100%"})

#                     if table:
#                         rows = table.find_all("tr")[1:]  # Skip header row

#                         for row in rows:
#                             cols = row.find_all("td")

#                             # Ensure row has valid data (ignoring duplicate headers)
#                             if len(cols) >= 5 and "Trade DateNum" not in cols[0].text:
#                                 trade_date = cols[0].text.strip()
#                                 num_trades = cols[1].text.strip().replace(',', '')  # Remove commas
#                                 volume = cols[2].text.strip().replace(',', '')  # Remove commas
#                                 notional_turnover = cols[3].text.strip().replace(',', '')  # Remove commas
#                                 premium_turnover = cols[4].text.strip().replace(',', '')  # Remove commas

#                                 # Write row to CSV file
#                                 writer.writerow([
#                                     datetime.utcnow().isoformat() + "Z",  # Scrape datetime in ISO format
#                                     instrument_name,  # Instrument type
#                                     trade_date,
#                                     num_trades,
#                                     volume,
#                                     notional_turnover,
#                                     premium_turnover
#                                 ])
#                                 print(f"📡 ✅ Data saved for Segment: {segment_name}, Instrument: {instrument_name} From Date: {from_date} to {to_date}...")

#                     else:
#                         print(f"⚠️ No data table found for {segment_name} - {instrument_name}")

#                 else:
#                     print(f"❌ Failed to fetch data for {segment_name} - {instrument_name} From Date: {from_date} to {to_date}...")

#         # Move to the next month
#         start_date = next_month

# print("✅ Data extraction completed! Check 'BSE_Derivatives_Data.csv'.")


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
    JOB_NAME.split("using")[0].strip().lower().replace(" ", "-") + "-test.csv",
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Referer': BASE_URL,
            'Origin': 'https://www.bseindia.com',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        session.headers.update(headers or default_headers)
        return session

    @retry_on_failure
    def make_request(self, url, params=None):
        """Performs an HTTP GET request."""
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

            # Create a session to maintain cookies
            session = self.CLIENT

            # Loop through each month
            while start_date < today:
                # Set the date range for one month
                from_date = start_date.strftime('%d/%m/%Y')
                next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
                to_date = min(next_month, today).strftime('%d/%m/%Y')

                # Perform GET request to fetch the page
                response = self.make_request(BASE_URL)
                if response.status_code != 200:
                    print("❌ Failed to load the page!")
                    exit()

                soup = BeautifulSoup(response.text, 'html.parser')
                print(soup)

                # Extract hidden input values
                def get_hidden_value(name):
                    input_tag = soup.find("input", {"name": name})
                    return input_tag["value"] if input_tag else ""

                viewstate = get_hidden_value("__VIEWSTATE")
                eventvalidation = get_hidden_value("__EVENTVALIDATION")
                viewstategenerator = get_hidden_value("__VIEWSTATEGENERATOR")

                # Extract Segment dropdown options
                segment_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlsegment")
                segment_options = {opt.get("value"): opt.text.strip() for opt in segment_dropdown.find_all("option") if opt.get("value")}

                # Iterate over all segments and fetch related instruments
                for segment, segment_name in segment_options.items():
                    print(f"Fetching instruments for Segment: {segment_name}")
                    
                    # Extract instruments for the current segment
                    instrument_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlIntrument")
                    instrument_options = {opt.get("value"): opt.text.strip() for opt in instrument_dropdown.find_all("option") if opt.get("value")}

                    # Iterate over each instrument for the current segment
                    for instrument, instrument_name in instrument_options.items():
                        # Prepare data payload
                        data = {
                            'ctl00$ContentPlaceHolder1$ddlsegment': segment,
                            'ctl00$ContentPlaceHolder1$ddlIntrument': instrument,
                            'ctl00$ContentPlaceHolder1$ddlUnderLine': '0',
                            'ctl00$ContentPlaceHolder1$txtDate': from_date,
                            'ctl00$ContentPlaceHolder1$txtTodate': to_date,
                            'ctl00$ContentPlaceHolder1$btnGo': 'Go',
                            '__VIEWSTATE': viewstate,
                            '__VIEWSTATEGENERATOR': viewstategenerator,
                            '__EVENTVALIDATION': eventvalidation,
                        }

                        # Send POST request for the current segment and instrument combination
                        response = session.post(BASE_URL, headers=session.headers, data=data)

                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')

                            # Find table with data
                            table = soup.find("table", {"width": "100%"})

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
                                        self.MASTER_LIST.append([datetime.utcnow().isoformat() + "Z",  # Scrape datetime in ISO format
                                                                instrument_name,  # Instrument type
                                                                trade_date,
                                                                num_trades,
                                                                volume,
                                                                notional_turnover,
                                                                premium_turnover])

                                        print(f"Data saved for Segment: {segment_name}, Instrument: {instrument_name} From Date: {from_date} to {to_date}...")

                            else:
                                print(f"⚠️ No data table found for {segment_name} - {instrument_name}")

                        else:
                            print(f"❌ Failed to fetch data for {segment_name} - {instrument_name} From Date: {from_date} to {to_date}...")

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
