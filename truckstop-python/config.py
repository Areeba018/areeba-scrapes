"""
Configuration file for TruckStop and FleetOne automation
"""

# FleetOne Credentials
FLEETONE_USERNAME = "muzafar.1995@hotmail.com"     
FLEETONE_PASSWORD = "Factoring12345"             
# MC Numbers to lookup
MC_NUMBERS = [
    "1288880",  # SALS GLOBAL TRANSPORT LLC
    "1560727",  # Inter Prime Cargo INC
    "001679",   # JRC TRANSPORTATION SERVICES LLC
    "186013"    # SUREWAY TRANSPORTATION
]

# Browser settings
HEADLESS_MODE = False  # Set to True to run in headless mode
BROWSER_TIMEOUT = 10   # Timeout in seconds for web elements 