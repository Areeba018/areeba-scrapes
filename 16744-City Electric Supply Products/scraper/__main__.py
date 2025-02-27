"""
This is the main entrypoint to the scraper.

Do not modify this file, instead write your code in `scraper.py` and treat the `run` function as your entrypoint.
"""
import argparse
import csv
import logging
import os

import pandas as pd
from scraper import Scraper


JOB_NAME = "City Electric Supply Products"
output_filename = os.path.join("16744-City Electric Supply Products", JOB_NAME.lower().replace(" ", "-") + "-data.csv")


def run(filename: str):
    scraper = Scraper()
    scraper.start_scraper()
    
    results = scraper.MASTER_LIST
    if not results:
        logging.error("NO DATA SCRAPED. EXITING...")
        return
    
    df = pd.DataFrame(results)
    logging.info("GENERATING FINAL OUTPUT...")
    df.to_csv(
        filename,
        encoding="utf-8",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
        index=False,
    )

if __name__ == "__main__":
    run(filename=output_filename)
    logging.info("ALL DONE")
