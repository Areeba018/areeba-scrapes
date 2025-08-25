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
# Use Selenium Wire to capture network requests
from seleniumwire import webdriver
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
        # chrome_options.add_argument("--headless")

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
            
            # Wait for redirect to complete
            time.sleep(5)
            current_url = self.browser.current_url
            print(f"[DEBUG] Current URL after wait: {current_url}")
            
            # Check if we need to handle callback
            if "login" in current_url.lower() or "signin" in current_url.lower():
                print("[DEBUG] Still on login page, checking for callback handling...")
                
                # Look for any callback-related elements
                try:
                    # Check for callback URL in the page
                    callback_elements = self.browser.find_elements(By.CSS_SELECTOR, 'a[href*="callback"], a[href*="redirect"], button[onclick*="callback"]')
                    if callback_elements:
                        print(f"[DEBUG] Found {len(callback_elements)} callback elements")
                        for element in callback_elements:
                            try:
                                print(f"[DEBUG] Clicking callback element: {element.text}")
                                element.click()
                                time.sleep(3)
                                break
                            except Exception as e:
                                print(f"[DEBUG] Error clicking callback element: {e}")
                    
                    # Check for any continue/proceed buttons
                    continue_buttons = self.browser.find_elements(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"], button:contains("Continue"), button:contains("Proceed")')
                    for button in continue_buttons:
                        if any(word in button.text.lower() for word in ["continue", "proceed", "go", "next", "submit"]):
                            print(f"[DEBUG] Clicking continue button: {button.text}")
                            button.click()
                            time.sleep(3)
                            break
                            
                except Exception as e:
                    print(f"[DEBUG] No callback elements found: {e}")
                
                # Check URL again after callback handling
                time.sleep(3)
                current_url = self.browser.current_url
                print(f"[DEBUG] Current URL after callback handling: {current_url}")
            
            print("[DEBUG] Checking login status...")

        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            raise
        print("[DEBUG] Login complete. You can now inspect the browser window.")
        
        # Check if login was successful by looking for successful API requests
        print("[DEBUG] Checking for successful API requests...")
        time.sleep(3)
        
        # Look for successful API requests in the captured network traffic
        successful_requests = []
        for request in self.browser.requests:
            if request.response and 'api-gateway.triumphbcap.com' in request.url:
                if request.response.status_code == 200:
                    successful_requests.append(request.url)
                    print(f"[DEBUG] Found successful API request: {request.url}")
        
        if successful_requests:
            print(f"[DEBUG] Login successful - found {len(successful_requests)} successful API requests")
        else:
            print("[DEBUG] No successful API requests found - login may have failed")
        
        self._extract_bearer_token_from_network()

    def _extract_bearer_token_from_network(self):
        print("[DEBUG] Extracting bearer token from network requests...")
        try:
            # Look for API requests in the captured network traffic
            for request in self.browser.requests:
                if request.response and 'api-gateway.triumphbcap.com' in request.url:
                    print(f"[DEBUG] Found API request: {request.url}")
                    print(f"[DEBUG] Request headers: {dict(request.headers)}")
                    print(f"[DEBUG] Response status: {request.response.status_code}")
                    
                    # Look for authorization header in request
                    if 'Authorization' in request.headers:
                        auth_header = request.headers['Authorization']
                        print(f"[DEBUG] Found Authorization header: {auth_header[:20]}...")
                        self.bearer_token = auth_header.replace('Bearer ', '')
                        return
                    
                    # Look for authorization in response headers
                    if hasattr(request.response, 'headers') and 'authorization' in request.response.headers:
                        auth_header = request.response.headers['authorization']
                        print(f"[DEBUG] Found Authorization in response: {auth_header[:20]}...")
                        self.bearer_token = auth_header.replace('Bearer ', '')
                        return
                    
                    # Look for cookies that might contain auth tokens
                    if hasattr(request, 'cookies'):
                        for cookie in request.cookies:
                            if 'token' in cookie.name.lower() or 'auth' in cookie.name.lower():
                                print(f"[DEBUG] Found auth cookie: {cookie.name}")
                                self.bearer_token = cookie.value
                                return
            
            # If no token found in network requests, try to get from browser storage
            print("[DEBUG] No token found in network requests, trying browser storage...")
            storage_script = """
            const token = window.localStorage.getItem('token') || 
                         window.sessionStorage.getItem('token') ||
                         window.localStorage.getItem('accessToken') ||
                         window.sessionStorage.getItem('accessToken') ||
                         window.localStorage.getItem('authToken') ||
                         window.sessionStorage.getItem('authToken');
            return token;
            """
            browser_token = self.browser.execute_script(storage_script)
            if browser_token:
                print(f"[DEBUG] Found token in browser storage: {browser_token[:20]}...")
                self.bearer_token = browser_token
                return
            
            print("[DEBUG] No authorization headers found in network requests")
            self.bearer_token = None
            
        except Exception as e:
            print(f"[DEBUG] Error extracting token from network: {e}")
            self.bearer_token = None

    def close(self):
        """Close the browser"""
        if self.browser:
            try:
                self.browser.quit()
            except Exception as e:
                pass

    def do_lookup(self, mc_numbers):
        print("[DEBUG] Starting credit check lookup using API approach...")
        results = []

        # Get the bearer token and capture the correct API request format
        print("[DEBUG] Extracting bearer token and capturing correct API format...")
        time.sleep(3)  # Wait for login to complete
        
        # First, navigate to credit check page and trigger a real search
        try:
            self.browser.get("https://www.mytriumph.com/creditcheck")
            time.sleep(3)
            
            # Wait for search input
            search_input = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="credit-search-type-ahead-input"]'))
            )
            
            # Clear and enter a test MC number
            search_input.clear()
            search_input.send_keys("001679")
            time.sleep(2)
            
            # Click search button to trigger the correct API call
            search_button = self.browser.find_element(By.CSS_SELECTOR, 'button[data-testid="credit-search-button"]')
            search_button.click()
            time.sleep(5)
            
            # Now capture the correct API request
            captured_request = None
            for request in self.browser.requests:
                if (request.response and 
                    'api-gateway.triumphbcap.com' in request.url and 
                    'risk-entity/search' in request.url):
                    captured_request = request
                    print(f"[DEBUG] Captured correct API request: {request.url}")
                    print(f"[DEBUG] Request headers: {dict(request.headers)}")
                    print(f"[DEBUG] Request body: {request.body}")
                    break
            
            if captured_request:
                self.captured_headers = captured_request.headers
                self.captured_body = captured_request.body
                print("[DEBUG] Successfully captured correct API request")
            else:
                print("[DEBUG] No correct API request captured")
                
        except Exception as e:
            print(f"[DEBUG] Error capturing correct API request: {e}")
        
        self._extract_bearer_token_from_network()
        
        for mc_number in mc_numbers:
            approved = False
            try:
                print(f"[DEBUG] Checking MC {mc_number} via API...")
                
                # API endpoint and payload structure
                api_url = "https://api-gateway.triumphbcap.com/credits/creditcheck/risk-entity/search"
                
                # Request payload structure - match exactly what works in browser
                payload = {
                    "searchTerm": mc_number,
                    "pagination": {
                        "includeTotalCount": True,
                        "page": 1,
                        "size": 10
                    },
                    "searchableFields": ["MC", "FF", "legalName", "dBAName", "OtherName"]
                }
                
                print(f"[DEBUG] API URL: {api_url}")
                print(f"[DEBUG] Request payload: {payload}")
                
                # Make API call using the captured request format
                try:
                    import requests
                    
                    # Use the captured headers if available
                    if hasattr(self, 'captured_headers') and self.captured_headers:
                        headers = dict(self.captured_headers)
                        print(f"[DEBUG] Using captured headers: {headers}")
                    else:
                        headers = {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }
                        if self.bearer_token:
                            headers['Authorization'] = f'Bearer {self.bearer_token}'
                            print(f"[DEBUG] Using bearer token: {self.bearer_token[:20]}...")
                        else:
                            print("[DEBUG] No bearer token found")
                    
                    print(f"[DEBUG] Making API call with headers: {headers}")
                    
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    print(f"[DEBUG] Response status: {response.status_code}")
                    print(f"[DEBUG] Response headers: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        api_response = response.json()
                        print(f"[DEBUG] API Response: {api_response}")
                    else:
                        print(f"[DEBUG] Error response: {response.text}")
                        api_response = {'error': response.text, 'status': response.status_code}
                        
                except Exception as e:
                    print(f"[DEBUG] Python requests error: {e}")
                    api_response = {'error': str(e)}
                
                # API call is now made with Python requests above
                print(f"[DEBUG] API Response: {api_response}")
                
                if api_response and 'error' in api_response:
                    print(f"[DEBUG] API Error: {api_response['error']}")
                    if 'status' in api_response:
                        print(f"[DEBUG] HTTP Status: {api_response['status']}")
                    if 'response' in api_response:
                        print(f"[DEBUG] Error Response: {api_response['response']}")
                    
                    # If it's a 403 Forbidden, try to refresh the page and get a new token
                    if api_response.get('status') == 403:
                        print("[DEBUG] 403 Forbidden - trying to refresh authentication...")
                        self.browser.refresh()
                        time.sleep(3)
                        # Extract token again and retry
                        self._extract_bearer_token_from_network()
                        print(f"[DEBUG] Retry with new token: {self.bearer_token[:20] if self.bearer_token else 'None'}...")
                
                if api_response and 'results' in api_response:
                    results_data = api_response['results']
                    print(f"[DEBUG] Found {len(results_data)} results")
                    
                    for result in results_data:
                        print(f"[DEBUG] Processing result: {result}")
                        
                        # Check if this result matches our MC number
                        docket = result.get('docket', '')
                        if mc_number in docket or mc_number in result.get('legalName', ''):
                            print(f"[DEBUG] Found matching result for MC {mc_number}")
                            
                            # Extract credit status
                            credit_status = result.get('creditStatus', '').upper()
                            print(f"[DEBUG] Credit status: {credit_status}")
                            
                            # Determine approval based on credit status
                            if credit_status == "GREEN":
                                approved = True
                                print(f"[DEBUG] MC {mc_number} is APPROVED (GREEN status)")
                            elif credit_status in ["RED", "DENIED", "REJECTED"]:
                                approved = False
                                print(f"[DEBUG] MC {mc_number} is DENIED ({credit_status} status)")
                            else:
                                print(f"[DEBUG] MC {mc_number} has unknown status: {credit_status}")
                            
                            break
                    else:
                        print(f"[DEBUG] No matching result found for MC {mc_number}")
                elif api_response and 'totalResults' in api_response:
                    # Handle case where results might be empty but totalResults exists
                    print(f"[DEBUG] Total results: {api_response.get('totalResults', 0)}")
                    if api_response.get('totalResults', 0) == 0:
                        print(f"[DEBUG] No results found for MC {mc_number}")
                else:
                    print(f"[DEBUG] No API response or invalid response for MC {mc_number}")
                    if api_response:
                        print(f"[DEBUG] API Response content: {api_response}")
                    
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

