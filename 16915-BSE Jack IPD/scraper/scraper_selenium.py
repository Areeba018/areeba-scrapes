import asyncio
from selenium_driverless import webdriver
from selenium_driverless.types.by import By

class Scraper:
    def __init__(self):
        self.driver = None

    async def setup_driver(self):
        """Initialize the WebDriver."""
        options = webdriver.ChromeOptions()
        options.headless = True  # Run in headless mode
        self.driver = await webdriver.Chrome(options=options)

    async def open_page(self):
        """Opens the BSE website."""
        url = "https://www.bseindia.com/markets/Derivatives/DeriReports/DeriHistoricalConsolidate.aspx"
        await self.driver.get(url)
        await asyncio.sleep(20)  # Wait for page to load completely
        print("✅ Page loaded successfully!")

    async def extract_dropdown_options(self, dropdown_id):
        """Finds a dropdown and extracts its options."""
        try:
            # Locate the dropdown element
            dropdown_element = await self.driver.find_element(By.ID, dropdown_id)
            
            # Get all option elements inside the dropdown
            options_elements = await dropdown_element.find_elements(By.TAG_NAME, "option")
            
            # Extract values and texts
            options = {await opt.get_attribute("value"): await opt.text for opt in options_elements if await opt.get_attribute("value")}
            
            print(f"✅ Dropdown '{dropdown_id}' options found:")
            for value, text in options.items():
                print(f"  - {value}: {text}")
            return options

        except Exception as e:
            print(f"❌ Error finding dropdown {dropdown_id}: {e}")
            return {}

    async def start_scraper(self):
        """Runs the scraper."""
        await self.setup_driver()
        await self.open_page()

        # Extract both dropdowns
        await self.extract_dropdown_options("ContentPlaceHolder1_ddlsegment")  # First dropdown
        await self.extract_dropdown_options("ContentPlaceHolder1_ddlIntrument")  # Second dropdown

        await self.driver.quit()  # Close the driver

async def run():
    scraper = Scraper()
    await scraper.start_scraper()

if __name__ == "__main__":
    asyncio.run(run())  # Run the async function
