import time
import random
import pyotp

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def random_sleep(min_seconds=2, max_seconds=5):
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)


def generate_current_otp(OTP_SECRET):
    """Generate and return the current OTP and seconds remaining."""
    totp = pyotp.TOTP(OTP_SECRET)
    current_otp = totp.now()
    interval = totp.interval  # Typically 30 seconds
    current_time = time.time()
    seconds_remaining = interval - (int(current_time) % interval)

    print(f"OTP: {current_otp}")
    print(f"Time left: {seconds_remaining} sec")

    return current_otp, seconds_remaining


def get_title(url: str) -> str:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        return driver.title
    finally:
        driver.quit()


def get_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-software-rasterizer")
    # chrome_options.add_argument("--ignore-certificate-errors")
    # chrome_options.add_argument("--incognito")

    driver = webdriver.Chrome(options=chrome_options)
    return driver




def truckstop_login(username, password, secret):

    token = None

    driver = get_driver()

    try:
        login(driver, username, password)
        
        enter_otp(driver, secret)
        
        # Try localStorage first
        token = driver.execute_script("return localStorage.getItem('token');")
        
        print('token:', token)

    except Exception as e:
        print(f"Login failed: {e}")
    
    finally:
        driver.quit()

    return token


def login(driver, username, password):

    driver.get("https://main.truckstop.com")
    print("TruckStop website opened.")
    time.sleep(30)

    # if url changed to auth.truckstop ....
    # print('check driver url: ', driver.url)

    # Wait for username field to be visible and input username
    username_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "username"))
    )
    username_field.send_keys(username)
    print("Username entered.")
    random_sleep()

    # Wait for password field to be visible and input password
    password_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "password"))
    )
    password_field.send_keys(password)
    print("Password entered.")
    random_sleep()

    # Wait for the checkbox to be clickable
    checkbox = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@class="mdc-checkbox mdc-checkbox--touch"]'))
    )

    # Check if the checkbox is selected based on the value attribute
    checkbox_value = checkbox.get_attribute("value")
    if checkbox_value != "true":  # If not checked
        checkbox.click()
        print("Checkbox checked.")
    else:
        print("Checkbox was already checked.")

    # Wait for login button to be clickable and click it
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
    )
    login_button.click()
    print("Login button clicked.")

    random_sleep()
 
 
def enter_otp(driver, secret):
    """Wait for the OTP field, enter the OTP, and submit."""
    try:
        otp_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "passcode"))
        )
        print("✅ OTP field found.")
    except TimeoutException:
        print("⚠️ OTP field not found directly. Trying alternative flow...")
        otp_field = handle_authenticator_flow(driver)
        if not otp_field:
            raise Exception('OTP field not found')

    # Common logic: OTP generation and form submission
    current_otp, seconds_remaining = generate_current_otp(secret)

    if seconds_remaining <= 10:
        print("⌛ OTP is about to expire. Waiting for next one...")
        time.sleep(15)
        current_otp, seconds_remaining = generate_current_otp(secret)

    print(f"✅ Using OTP valid for next {seconds_remaining} seconds.")
    otp_field.send_keys(current_otp)
    print("✅ OTP entered.")

    try:
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        submit_button.click()
        print("✅ OTP submitted.")

        time.sleep(40)

        # Check for error message after OTP submission
        try:
            error_heading = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Sorry, there was an issue.')]"))
            )
            print("⚠️ Error message appeared after OTP submit.")

        except TimeoutException:
            print("✅ No error message after OTP submit.")

    except TimeoutException:
        print("❌ Submit button not found or not clickable.")
        raise Exception('Submit button not found or not clickable.')




# async def handle_change_device(driver):
#     # 🔹 Check for error message immediately after clicking submit
#     try:
#         cancel_btn = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.XPATH, '//*[@id="cancel"]'))
#         )
#         cancel_btn.click()
#         print("🟡 Invalid passcode found! 'Change Device' clicked.")
#         await random_sleep()
#         otp_field = await handle_authenticator_flow(driver)
#         if not otp_field:
#             return
#         return
#     except TimeoutException:
#         print("✅ No error message found, continuing...")


def handle_authenticator_flow(driver):
    """Handle the Authenticator App flow to reach the OTP field."""
    try:
        totp_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "mfa-type-list-button-TOTP"))
        )
        totp_button.click()
        print("✅ 'Authenticator App' button clicked.")
        random_sleep()

        log_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        log_button.click()
        print("🔁 Login button clicked after selecting Authenticator.")
        random_sleep()

        otp_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "passcode"))
        )
        print("✅ OTP field found after fallback.")
        return otp_field

    except TimeoutException:
        print("❌ Could not complete Authenticator App flow.")
        return None
