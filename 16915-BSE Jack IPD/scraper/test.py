import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# BSE Derivatives URL
BASE_URL = "https://www.bseindia.com/markets/Derivatives/DeriReports/DeriHistoricalConsolidate.aspx"

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Referer': BASE_URL,
    'Origin': 'https://www.bseindia.com',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# Date range: Start from 2022-01-01 and fetch data month by month until today
start_date = datetime(2025, 1, 1)
today = datetime.today()

# Open CSV file for writing
with open("BSE_Derivatives_Data.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    
    # Write CSV Header
    writer.writerow(["scrape_datetime", "instrument_type", "date", "number_of_trades", "volume", "notional_turnover", "premium_turnover"])

    # Create a session to maintain cookies
    session = requests.Session()

    # Loop through each month
    while start_date < today:
        # Set the date range for one month
        from_date = start_date.strftime('%d/%m/%Y')
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        # New logic: End date should be the 1st day of the next month
        to_date = next_month.strftime('%d/%m/%Y')

        # Perform GET request to fetch the page
        response = session.get(BASE_URL, headers=headers)
        if response.status_code != 200:
            print("❌ Failed to load the page!")
            exit()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract Segment and Instrument dropdown options
        segment_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlsegment")
        segment_options = {opt.get("value"): opt.text.strip() for opt in segment_dropdown.find_all("option") if opt.get("value")}

        instrument_dropdown = soup.find("select", id="ContentPlaceHolder1_ddlIntrument")
        instrument_options = {opt.get("value"): opt.text.strip() for opt in instrument_dropdown.find_all("option") if opt.get("value")}

        # Extract hidden input values
        def get_hidden_value(name):
            input_tag = soup.find("input", {"name": name})
            return input_tag["value"] if input_tag else ""

        viewstate = get_hidden_value("__VIEWSTATE")
        eventvalidation = get_hidden_value("__EVENTVALIDATION")
        viewstategenerator = get_hidden_value("__VIEWSTATEGENERATOR")

        # Iterate over all segment and instrument combinations
        for segment, segment_name in segment_options.items():
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

                print(f"📡 Fetching data for Segment: {segment_name}, Instrument: {instrument_name} From Date: {from_date} to {to_date}...")

                # Send POST request
                response = session.post(BASE_URL, headers=headers, data=data)

                # ✅ Check if request was successful
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

                                # Write row to CSV file
                                writer.writerow([
                                    datetime.utcnow().isoformat() + "Z",  # Scrape datetime in ISO format
                                    instrument_name,  # Instrument type
                                    trade_date,
                                    num_trades,
                                    volume,
                                    notional_turnover,
                                    premium_turnover
                                ])
                                print(f"📡 ✅ Data saved for Segment: {segment_name}, Instrument: {instrument_name} From Date: {from_date} to {to_date}...")


                    else:
                        print(f"⚠️ No data table found for {segment_name} - {instrument_name}")

                else:
                    print(f"❌ Failed to fetch data for {segment_name} - {instrument_name}")

        # Move to the next month
        start_date = next_month

print("✅ Data extraction completed! Check 'BSE_Derivatives_Data.csv'.")


