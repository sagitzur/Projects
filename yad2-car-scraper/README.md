# Yad2 Car Scraper

A Python script to scrape used car listings from Yad2.co.il based on manufacturer, model, and year range.

## Features
- Scrape multiple car models simultaneously
- Filter by year range
- Export results to CSV
- Detailed logging
- Rate limiting to respect server resources

## Requirements
- Python 3.7+
- requests
- pandas

## Installation
```bash
git clone [your-repo-url]
cd yad2-car-scraper
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt