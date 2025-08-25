"""
Triumph Credit Check Script
Converted from JavaScript to Python

https://www.mytriumph.com (Factoring)

MC # 1288880
SALS GLOBAL TRANSPORT LLC

MC # 1560727
Inter Prime Cargo INC

MC # 001679
JRC TRANSPORTATION SERVICES LLC

MC # 186013
SUREWAY TRANSPORTATION
"""

import time
import json
import requests
import pyotp
from datetime import datetime
# Use regular Selenium with JavaScript execution
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


class Triumph:
    def __init__(self, username, password, totp_secret):
        self.username = username
        self.password = password
        self.totp_secret = totp_secret
        self.browser = None
        self.page = None
        self.bearer_token = None
        self.provider = "triumph"

    def init(self):
        print("[DEBUG] Starting browser...")
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Uncomment the line below to run in headless mode
        chrome_options.add_argument("--headless")

        if self.browser:
            self.browser.quit()

        try:
            self.browser = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.page = self.browser
            print("[DEBUG] Chrome started successfully.")
        except Exception as e:
            print(f"[ERROR] Error starting Chrome: {e}")
            print("[ERROR] Please make sure Chrome is installed and chromedriver is in PATH")
            raise

        print("[DEBUG] Navigating to Triumph...")
        try:
            self.page.get("http://www.mytriumph.com")
        except Exception as e:
            print(f"[ERROR] Could not navigate to Triumph: {e}")
            raise

        wait = WebDriverWait(self.page, 60)
        try:
            print("[DEBUG] Waiting for email field...")
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="email"]')))
            print("[DEBUG] Email field found.")
            email_field.send_keys(self.username)
            print(f"[DEBUG] Entered email: {self.username}")

            print("[DEBUG] Waiting for password field...")
            password_field = self.page.find_element(By.CSS_SELECTOR, '[data-testid="password"]')
            print("[DEBUG] Password field found.")
            password_field.send_keys(self.password)
            print(f"[DEBUG] Entered password: {'*' * len(self.password)}")

            print("[DEBUG] Waiting for login button...")
            login_button = self.page.find_element(By.CSS_SELECTOR, '[data-testid="login"]')
            print("[DEBUG] Login button found. Clicking...")
            login_button.click()

            print("[DEBUG] Checking for 2FA...")
            time.sleep(5)
            try:
                totp_selectors = [
                    'input[type="text"]',
                    'input[placeholder*="code"]',
                    'input[placeholder*="Code"]',
                    'input[name*="code"]',
                    'input[name*="totp"]',
                    'input[type="number"]',
                    'input[autocomplete="one-time-code"]'
                ]
                totp_field = None
                for selector in totp_selectors:
                    try:
                        totp_field = self.page.find_element(By.CSS_SELECTOR, selector)
                        if totp_field.is_displayed():
                            print(f"[DEBUG] 2FA field found with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"[DEBUG] 2FA selector {selector} not found: {e}")
                        continue
                if totp_field:
                    print("[DEBUG] 2FA field found, entering TOTP...")
                    totp = pyotp.TOTP(self.totp_secret)
                    current_otp = totp.now()
                    print(f"[DEBUG] Generated TOTP: {current_otp}")
                    totp_field.clear()
                    totp_field.send_keys(current_otp)
                    print("[DEBUG] TOTP entered.")
                    try:
                        submit_button = self.page.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                        print("[DEBUG] 2FA submit button found. Clicking...")
                        submit_button.click()
                    except Exception as e:
                        print(f"[DEBUG] 2FA submit button not found: {e}. Sending ENTER key.")
                        from selenium.webdriver.common.keys import Keys
                        totp_field.send_keys(Keys.RETURN)
                    print("[DEBUG] 2FA submitted, waiting for login...")
                    time.sleep(5)
                else:
                    # Save the page source for inspection if 2FA field is not found
                    with open('2fa_page.html', 'w', encoding='utf-8') as f:
                        f.write(self.page.page_source)
                    print("[DEBUG] 2FA input field not found. Saved current page HTML to 2fa_page.html. Please inspect this file to find the correct selector.")
            except Exception as e:
                print(f"[DEBUG] No 2FA field found: {e}")

            # Check if we're still on login page after callback
            current_url = self.browser.current_url
            print(f"[DEBUG] Current URL after callback: {current_url}")
            
            if "login" in current_url.lower() or "signin" in current_url.lower():
                print("[DEBUG] Still on login page after callback, trying to wait longer...")
                time.sleep(10)
                current_url = self.browser.current_url
                print(f"[DEBUG] Current URL after longer wait: {current_url}")
                
                # If still on login page, try to find and click any "Continue" or "Proceed" buttons
                try:
                    continue_buttons = self.browser.find_elements(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"], a[href*="triumph"]')
                    for button in continue_buttons:
                        if any(word in button.text.lower() for word in ["continue", "proceed", "go", "next"]):
                            button.click()
                            print("[DEBUG] Clicked continue button after callback")
                            time.sleep(3)
                            break
                except Exception as e:
                    print(f"[DEBUG] No continue button found: {e}")
            
            print("[DEBUG] Checking login status...")

        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            raise
        print("[DEBUG] Login complete. You can now inspect the browser window.")
        self._extract_bearer_token_from_network()

    def _extract_bearer_token_from_network(self):
        print("[DEBUG] Browser is already authenticated - no token needed!")
        # The browser session is already authenticated, no need for bearer token
        self.bearer_token = None

    def close(self):
        """Close the browser"""
        if self.browser:
            try:
                self.browser.quit()
            except Exception as e:
                pass

    def do_lookup(self, mc_numbers):
        print("[DEBUG] Starting credit check lookup...")
        results = []

        try:
            # Wait for the search input to be available
            WebDriverWait(self.browser, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="credit-search-type-ahead-input"]'))
            )
            print("[DEBUG] Credit check page loaded successfully")
        except Exception as e:
            print(f"[DEBUG] Error navigating to credit check page: {e}")
            return results
        
        for mc_number in mc_numbers:
            approved = False
            try:
                print(f"[DEBUG] Checking MC {mc_number}...")
                
                # Navigate back to credit check page for each MC number to ensure fresh start
                print(f"[DEBUG] Navigating to credit check page for MC {mc_number}...")
                self.browser.get("https://www.mytriumph.com/creditcheck")
                time.sleep(3)
                
                # Wait for search input to be available
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="credit-search-type-ahead-input"]'))
                )
                
                # Clear the search input first - use multiple methods to ensure it's cleared
                search_input = self.browser.find_element(By.CSS_SELECTOR, 'input[data-testid="credit-search-type-ahead-input"]')
                search_input.clear()
                time.sleep(1)
                
                # Verify the input is empty
                input_value = search_input.get_attribute('value')
                print(f"[DEBUG] Input value after clear: '{input_value}'")
                
                # Type the MC number one by one
                for digit in mc_number:
                    search_input.send_keys(digit)
                    time.sleep(0.1)  # Small delay between each character
                
                print(f"[DEBUG] Entered MC number: {mc_number}")
                
                # Step 1: Click the Search button to trigger search
                time.sleep(1)
                try:
                    search_button = self.browser.find_element(By.CSS_SELECTOR, 'button[data-testid="credit-search-button"]')
                    search_button.click()
                    print(f"[DEBUG] Search button clicked for MC {mc_number}")
                except Exception as e:
                    print(f"[DEBUG] Search button click failed: {e}")
                
                # Step 2: Wait for search results page to load
                time.sleep(3)
                print(f"[DEBUG] Waiting for search results page to load...")
                
                # Check if we're on the results page
                current_url = self.browser.current_url
                print(f"[DEBUG] Current URL: {current_url}")
                
                # Step 3: Click on the first search result (search-result-0)
                try:
                    # Wait for search results to appear
                    WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="credit-search-result-0"]'))
                    )
                    
                    # Click on the first search result
                    first_result = self.browser.find_element(By.CSS_SELECTOR, 'div[data-testid="credit-search-result-0"]')
                    print(f"[DEBUG] Found search result: {first_result.text}")
                    
                    # Click on the navigate-to-more-detail-link specifically
                    try:
                        detail_link = first_result.find_element(By.CSS_SELECTOR, 'span[data-testid="navigate-to-more-detail-link"]')
                        print(f"[DEBUG] Found detail link: {detail_link.text}")
                        self.browser.execute_script("arguments[0].click();", detail_link)
                        print(f"[DEBUG] Clicked on detail link for MC {mc_number}")
                    except Exception as e:
                        print(f"[DEBUG] Detail link not found, clicking on main result: {e}")
                        # Fallback: click on the main search result
                        self.browser.execute_script("arguments[0].click();", first_result)
                        print(f"[DEBUG] Clicked on first search result for MC {mc_number}")
                    
                    # Step 4: Wait for the credit status page to load
                    time.sleep(3)
                    print(f"[DEBUG] Waiting for credit status page to load...")
                    
                    # Check the new URL after clicking
                    new_url = self.browser.current_url
                    print(f"[DEBUG] URL after clicking result: {new_url}")
                    
                    # Now check for credit status on the result page
                    try:
                        # Look for the credit status label specifically
                        status_label = self.browser.find_element(By.CSS_SELECTOR, 'label.css-1dbjue5.e1svxd7x1')
                        status_text = status_label.text.strip()
                        print(f"[DEBUG] Found credit status: '{status_text}' for MC {mc_number}")
                        
                        # Check the status text (not hardcoded, dynamic based on actual status)
                        if "approved" in status_text.lower():
                            approved = True
                            print(f"[DEBUG] MC {mc_number} is APPROVED (status: {status_text})")
                        elif "denied" in status_text.lower() or "rejected" in status_text.lower():
                            approved = False
                            print(f"[DEBUG] MC {mc_number} is DENIED (status: {status_text})")
                        else:
                            print(f"[DEBUG] MC {mc_number} has unknown status: {status_text}")
                            
                    except Exception as e:
                        print(f"[DEBUG] Error finding credit status label: {e}")
                        # Fallback: try other selectors
                        try:
                            status_elements = self.browser.find_elements(By.CSS_SELECTOR, '[data-testid*="credit-status"], [class*="status"], [class*="credit"]')
                            for element in status_elements:
                                text = element.text.lower()
                                if "approved" in text or "green" in text:
                                    approved = True
                                    print(f"[DEBUG] MC {mc_number} is APPROVED (found on result page)")
                                    break
                                elif "denied" in text or "red" in text or "no buy" in text:
                                    approved = False
                                    print(f"[DEBUG] MC {mc_number} is DENIED (found on result page)")
                                    break
                        except Exception as e2:
                            print(f"[DEBUG] Fallback status check also failed: {e2}")
                        
                except Exception as e:
                    print(f"[DEBUG] No search result found for MC {mc_number}: {e}")
                    
            except Exception as error:
                print(f"[DEBUG] Error processing MC number {mc_number}: {error}")
                
            print(f'Triumph Search Response for MC {mc_number}: {approved}')
            data = {
                "provider": self.provider,
                "mcNumber": mc_number,
                "isSupported": 1 if approved else 0,
                "date": datetime.now()
            }
            results.append(data)
            
            # Now navigate back to credit check page for next MC number
            print(f"[DEBUG] Completed MC {mc_number}, moving to next...")
        return results


# Example usage
if __name__ == "__main__":
    # Replace with your actual credentials
    TRIUMPH_SECRET = "IWJCQDR2CKA3HXHR"
    
    # Actual credentials
    username = "support@loadportal.org"
    password = "vorxyq-Dekho8-jipwep"
    totp_secret = "IWJCQDR2CKA3HXHR"
    
    # MC numbers and company names to check
    mc_numbers = ["1288880", "1560727", "001679", "186013"]
    
    triumph = Triumph(username, password, totp_secret)
    
    try:
        triumph.init()
        results = triumph.do_lookup(mc_numbers)
        
        print("Results:")
        for result in results:
            print(f"MC {result['mcNumber']}: {'Approved' if result['isSupported'] else 'Not Approved'}")
            
    except Exception as e:
        print(f"Error: {e}")
    # Now close the browser
    triumph.close()
