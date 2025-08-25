import time
import random
import csv
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime


def random_sleep(min_seconds=1, max_seconds=3):
    """Add random delay between actions"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)


def get_driver():
    """Initialize and return Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Enable network logging
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # Uncomment below for headless mode
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


class Otr:
    """
    OTR Solutions class for interacting with OTR Factoring portal
    https://portal.otrsolutions.com (OTR Factoring)
    
    MC # 1288880 - SALS GLOBAL TRANSPORT LLC
    MC # 1560727 - Inter Prime Cargo INC
    MC # 001679 - JRC TRANSPORTATION SERVICES LLC
    MC # 186013 - SUREWAY TRANSPORTATION
    """
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.provider = "otr"
        self.session = requests.Session()
    
    def init(self):
        """Initialize browser and login to OTR Solutions"""
        try:
            if self.driver:
                self.driver.quit()
            
            self.driver = get_driver()
            
            # Navigate to login page
            self.driver.get("https://portal.otrsolutions.com")
            random_sleep(2, 4)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '[type="email"]'))
            )
            email_field.send_keys(self.username)
            print("Email entered.")
            random_sleep()
            
            # Enter password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '[type="password"]'))
            )
            password_field.send_keys(self.password)
            print("Password entered.")
            random_sleep()
            
            # Click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "dx-button-text"))
            )
            login_button.click()
            print("Login button clicked.")
            
            # Wait for navigation to complete
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.current_url != "https://portal.otrsolutions.com"
            )
            
            print("OTR logged in")
            
            # Get cookies for API requests
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing browser: {e}")
    
    def do_lookup(self, mc_numbers, retries=3):
        """
        Perform credit lookup for multiple MC numbers
        Uses exact same logic as JavaScript version
        
        Args:
            mc_numbers (list): List of MC numbers to lookup
            retries (int): Number of retry attempts
            
        Returns:
            list: List of dictionaries with lookup results
        """
        results = []
        
        for mc_number in mc_numbers:
            try:
                print(f"Looking up MC number: {mc_number}")
                
                # Step 1: Search for customer using API (same as JS)
                customer_data = self._search_customer_api(mc_number)
                
                if not customer_data:
                    print(f"No customer found for MC {mc_number}")
                    data = {
                        'provider': self.provider,
                        'mcNumber': mc_number,
                        'isSupported': 0,
                        'date': datetime.now()
                    }
                    results.append(data)
                    continue
                
                # Step 2: Perform credit check using API (same as JS)
                approved = self._credit_check_api(customer_data['PKey'])
                
                print(f'OTR Search Response for {mc_number}: {approved}')
                
                # Create result data
                data = {
                    'provider': self.provider,
                    'mcNumber': mc_number,
                    'isSupported': 1 if approved else 0,
                    'date': datetime.now()
                }
                
                results.append(data)
                
                # Add delay between searches
                random_sleep(2, 4)
                
            except Exception as e:
                print(f"Error looking up MC number {mc_number}: {e}")
                # Add failed result
                data = {
                    'provider': self.provider,
                    'mcNumber': mc_number,
                    'isSupported': None,
                    'date': datetime.now(),
                    'error': str(e)
                }
                results.append(data)
        
        return results
    
    def _search_customer_api(self, mc_number):
        """
        Search for customer using API (same as JavaScript version)
        
        Args:
            mc_number (str): MC number to search for
            
        Returns:
            dict: Customer data or None if not found
        """
        try:
            # Same API call as JavaScript version
            url = f"https://portal.otrsolutions.com/Broker/GetCustomerListAsync"
            params = {
                'skip': 0,
                'take': 15,
                'sort': '[{"selector":"Name","desc":false}]',
                'filter': f'[["Name","contains","{mc_number}"],"or",["McNumber","contains","{mc_number}"]]',
                'searchValue': mc_number
            }
            
            headers = {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US;q=0.9,en;q=0.8",
                "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "x-requested-with": "XMLHttpRequest"
            }
            
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            json_data = response.json()
            
            # Find the record with matching MC number (same as JS)
            record = None
            if 'data' in json_data:
                for item in json_data['data']:
                    if item.get('McNumber') == mc_number:
                        record = item
                        break
            
            return record
            
        except Exception as e:
            print(f"Error searching customer API: {e}")
            return None
    
    def _credit_check_api(self, p_key):
        """
        Perform credit check using API (same as JavaScript version)
        
        Args:
            p_key (str): Customer PKey
            
        Returns:
            bool: True if approved, False if not
        """
        try:
            # Same API call as JavaScript version
            url = "https://portal.otrsolutions.com/Broker/CreditCheckAsync"
            
            headers = {
                "accept": "*/*",
                "accept-language": "en-PH,en-US;q=0.9,en;q=0.8",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "x-requested-with": "XMLHttpRequest"
            }
            
            data = {
                'customerPKey': p_key
            }
            
            response = self.session.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            json_data = response.json()
            
            # Same logic as JavaScript: approved if text doesn't contain "Not"
            if 'data' in json_data and 'text' in json_data['data']:
                approved = "Not" not in json_data['data']['text']
                return approved
            
            return False
            
        except Exception as e:
            print(f"Error in credit check API: {e}")
            return False


def save_results_to_csv(results, filename="otrsolutions_results.csv"):
    """Save results to CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['provider', 'mcNumber', 'isSupported', 'date', 'status_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                # Add status text for better readability
                status_text = {
                    1: "APPROVED",
                    0: "DECLINED",
                    None: "ERROR"
                }.get(result['isSupported'], "UNKNOWN")
                
                row = result.copy()
                row['status_text'] = status_text
                writer.writerow(row)
        
        print(f"✅ Results saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Example MC numbers from the comments
    mc_numbers = [
        "1288880",  # SALS GLOBAL TRANSPORT LLC
        "1560727",  # Inter Prime Cargo INC
        "001679",   # JRC TRANSPORTATION SERVICES LLC
        "186013"    # SUREWAY TRANSPORTATION
    ]
    
    # Initialize OTR instance with your credentials
    otr = Otr("contact@prostarfreight.com", "Factoring12345!")
    
    try:
        # Login
        if otr.init():
            # Perform lookups
            results = otr.do_lookup(mc_numbers)
            
            # Print results
            print("\n📊 Results:")
            for result in results:
                status_text = {
                    1: "✅ APPROVED",
                    0: "❌ DECLINED",
                    None: "❓ ERROR"
                }.get(result['isSupported'], "❓ UNKNOWN")
                print(f"MC: {result['mcNumber']}, Status: {status_text}, Date: {result['date']}")
                
                if 'error' in result:
                    print(f"    Error: {result['error']}")
            
            # Save to CSV
            print("\n💾 Saving results to CSV...")
            save_results_to_csv(results)
            
        else:
            print("Failed to login")
    
    finally:
        # Always close the browser
        otr.close() 