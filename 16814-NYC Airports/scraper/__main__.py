"""
This is the main entrypoint to the scraper.

Do not modify this file, instead write your code in `scraper.py` and treat the `run` function as your entrypoint.
"""
import argparse
import logging
import os
from scraper import run

job_name = "Airport Security & Customs Wait Times Scraper"
output_filename = os.path.join("16814-NYC Airports", job_name.lower().replace(" ", "-") + "-data.csv")

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Scrape Airport Wait Times Data.')
    parser.add_argument('filename', type=str, nargs='?', default=output_filename,
                        help=f'Output filename for scraped data (default: {output_filename}).')
    return parser

def main():
    args = get_parser().parse_args()
    os.makedirs(os.path.dirname(args.filename), exist_ok=True)  # Ensure the directory exists
    logging.info(f"Starting scraper with output file: {args.filename}")
    run(args.filename)
    logging.info("Scraper completed successfully.")

if __name__ == "__main__":
    main()
