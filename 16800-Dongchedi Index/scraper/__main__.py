"""
This is the main entrypoint to the scraper.

Do not modify this file, instead write your code in `scraper.py` and treat the `run` function as your entrypoint.
"""
import argparse
import logging
import os
from scraper import run

JOB_NAME = "Dongchedi Index Scraper"
output_filename = os.path.join("16800-Dongchedi Index", JOB_NAME.lower().replace(" ", "-") + "-data.csv")

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Scrape Dongchedi Index Data.')
    parser.add_argument('filename', type=str, nargs='?', default=output_filename,
                        help=f'Output filename for scraped data (default: {output_filename}).')
    return parser

def main():
    args = get_parser().parse_args()
    logging.info(f"Starting scraper with output file: {args.filename}")
    run()
    logging.info("Scraper completed successfully.")

if __name__ == "__main__":
    main()
