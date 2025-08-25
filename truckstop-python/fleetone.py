import time
import random
import csv
import json
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
    chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


class Fleet:
    """
    Fleet class for interacting with FleetOne website
    https://apps.fleetone.com (Wex)
    
    MC # 1288880 - SALS GLOBAL TRANSPORT LLC
    MC # 1560727 - Inter Prime Cargo INC
    MC # 001679 - JRC TRANSPORTATION SERVICES LLC
    MC # 186013 - SUREWAY TRANSPORTATION
    """
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.provider = "Fleet"
    
    def init(self):
        """Initialize browser and login to FleetOne"""
        try:
            if self.driver:
                self.driver.quit()
            
            self.driver = get_driver()
            
            # Navigate to login page
            self.driver.get("https://apps.fleetone.com/FleetDocs/User/Login")
            random_sleep(2, 4)
            
            # Enter username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "UserName"))
            )
            username_field.send_keys(self.username)
            print("Username entered.")
            random_sleep()
            
            # Enter password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "Password"))
            )
            password_field.send_keys(self.password)
            print("Password entered.")
            random_sleep()
            
            # Click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fleet-primary"))
            )
            login_button.click()
            print("Login button clicked.")
            
            # Wait for navigation to complete
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.current_url != "https://apps.fleetone.com/FleetDocs/User/Login"
            )
            
            print("Fleet Logged In")
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
                
                # Find and fill the MC search field
                mc_search_field = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "mcSearch"))
                )
                mc_search_field.clear()
                mc_search_field.send_keys(mc_number)
                random_sleep()
                
                # Click search button
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnSearch"))
                )
                search_button.click()
                print("Search button clicked.")
                
                # Wait for the response and check for status using EXACT same logic as JS
                status = self._check_response_status_exact_js_logic()
                
                print(f'Fleet Search Response for {mc_number}: {status}')
                
                # Create result data
                data = {
                    'provider': self.provider,
                    'mcNumber': mc_number,
                    'isSupported': status,
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
    
    def _check_response_status_exact_js_logic(self):
        """
        Check the response status using EXACT same logic as JavaScript version
        This intercepts the network response like the JS version does
        
        Returns:
            int: 1 for Approve, 2 for Review, 0 for Decline/No result
        """
        try:
            # Wait for the specific network response like JS version
            # In Selenium, we need to wait for the table to update after the AJAX call
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Add extra wait for AJAX to complete
            time.sleep(3)
            
            # Get network logs to find the AJAX response
            logs = self.driver.get_log('performance')
            
            # Look for the specific AJAX response
            ajax_response_data = None
            for log in logs:
                if 'get_credit_lookup_paginate' in str(log):
                    print(f"Found AJAX log: {log}")
                    # Try to extract the response data
                    try:
                        log_data = json.loads(log['message'])
                        if 'message' in log_data and 'method' in log_data['message']:
                            if log_data['message']['method'] == 'Network.responseReceived':
                                request_id = log_data['message']['params']['requestId']
                                # Get the response body
                                response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                if response_body and 'body' in response_body:
                                    ajax_response_data = response_body['body']
                                    print(f"AJAX response data: {ajax_response_data[:200]}...")
                                    break
                    except:
                        continue
            
            # If we can't get the AJAX response, fall back to table HTML
            if not ajax_response_data:
                print("Could not get AJAX response, using table HTML")
                table_element = self.driver.find_element(By.TAG_NAME, "table")
                ajax_response_data = table_element.get_attribute('innerHTML')
            
            # Use EXACT same logic as JavaScript version
            # Extract the value of the 'title' attribute from the first column of the first row
            containsApprove = 'Approve' in ajax_response_data
            containsDecline = 'Decline' in ajax_response_data
            containsReview = 'Review' in ajax_response_data
            
            # Debug: Print what we found
            print(f"containsApprove: {containsApprove}")
            print(f"containsDecline: {containsDecline}")
            print(f"containsReview: {containsReview}")
            
            # Same priority order as JS: Approve first, then Review, then default to 0
            if containsApprove:
                status = 1
            elif containsReview:
                status = 2
            else:
                status = 0
                
            return status
                
        except TimeoutException:
            print("Timeout waiting for search results")
            return 0
        except Exception as e:
            print(f"Error checking response status: {e}")
            return 0
    
    def _check_response_status_js_style(self):
        """
        Check the response status using the same logic as the JavaScript version
        This matches the exact logic from fleetone.js
        
        Returns:
            int: 1 for Approve, 2 for Review, 0 for Decline/No result
        """
        try:
            # Wait for the table data to load (similar to waiting for response in JS)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Get the page source to check for status keywords (equivalent to responseBody.table_data)
            page_source = self.driver.page_source
            
            # Use the exact same logic as JavaScript version
            containsApprove = 'Approve' in page_source
            containsDecline = 'Decline' in page_source
            containsReview = 'Review' in page_source
            
            # Same priority order as JS: Approve first, then Review, then default to 0
            if containsApprove:
                status = 1
            elif containsReview:
                status = 2
            else:
                status = 0
                
            return status
                
        except TimeoutException:
            print("Timeout waiting for search results")
            return 0
        except Exception as e:
            print(f"Error checking response status: {e}")
            return 0
    
    def _check_response_status(self):
        """
        Check the response status from the search results (legacy method)
        
        Returns:
            int: 1 for Approve, 2 for Review, 0 for Decline/No result
        """
        try:
            # Wait for the table data to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Get the page source to check for status keywords
            page_source = self.driver.page_source
            
            # Check for specific status indicators in the HTML
            if 'title=Approve' in page_source or 'title="Approve"' in page_source:
                return 1
            elif 'Request Review' in page_source:
                return 2
            elif 'title=Review' in page_source or 'title="Review"' in page_source:
                return 2
            elif 'title=Decline' in page_source or 'title="Decline"' in page_source:
                return 0
            elif 'Approve' in page_source:
                return 1
            elif 'Review' in page_source:
                return 2
            elif 'Decline' in page_source:
                return 0
            else:
                return 0
                
        except TimeoutException:
            print("Timeout waiting for search results")
            return 0
        except Exception as e:
            print(f"Error checking response status: {e}")
            return 0


def save_results_to_csv(results, filename="fleetone_results.csv"):
    """Save results to CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['provider', 'mcNumber', 'isSupported', 'date', 'status_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                # Add status text for better readability
                status_text = {
                    1: "APPROVE",
                    2: "REVIEW", 
                    0: "DECLINE",
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
    
    # Initialize Fleet instance
    fleet = Fleet("muzafar.1995@hotmail.com", "Factoring12345")
    
    try:
        # Login
        if fleet.init():
            # Perform lookups
            results = fleet.do_lookup(mc_numbers)
            
            # Print results
            print("\n📊 Results:")
            for result in results:
                status_text = {
                    1: "✅ APPROVE",
                    2: "⚠️ REVIEW", 
                    0: "❌ DECLINE",
                    None: "❓ ERROR"
                }.get(result['isSupported'], "❓ UNKNOWN")
                print(f"MC: {result['mcNumber']}, Status: {status_text}, Date: {result['date']}")
            
            # Save to CSV
            print("\n💾 Saving results to CSV...")
            save_results_to_csv(results)
            
        else:
            print("Failed to login")
    
    finally:
        # Always close the browser
        fleet.close() 