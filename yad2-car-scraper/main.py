import requests
import json
from datetime import datetime
import pandas as pd
import time
from typing import List, Dict, Optional, Tuple
import logging

class Yad2CarScraper:
    def __init__(self):
        # Updated to match the website's actual API endpoint
        self.base_url = "https://gw.yad2.co.il/feed-search-legacy/vehicles/cars"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,he;q=0.8',
            'Origin': 'https://www.yad2.co.il',
            'Referer': 'https://www.yad2.co.il/vehicles/cars',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        # Set up debug logging
        self.logger = self._setup_logger()
        self.debug = True  # Enable debug mode

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('Yad2CarScraper')
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _construct_query_params(self, manufacturer: str, model: str, year_range: Optional[Tuple[int, int]] = None, page: int = 1) -> Dict:
        """Construct query parameters based on actual website requests"""
        params = {
            'category': 'cars',
            'subCategory': 'private',
            'manufacturer': manufacturer,
            'model': model,
            'page': page,
        }
        
        if year_range:
            start_year, end_year = year_range
            params.update({
                'year_from': str(start_year),
                'year_to': str(end_year)
            })
            
        return params

    def _extract_car_details(self, item: Dict) -> Dict:
        """Extract car details with better error handling and logging"""
        try:
            # Log the raw item for debugging
            self.logger.debug(f"Processing item: {json.dumps(item, ensure_ascii=False)}")
            
            details = {
                'title': item.get('title', ''),
                'price': item.get('price', {}).get('value', 0),
                'year': item.get('year', ''),
                'hand': item.get('hand', ''),
                'engine_size': item.get('engine_size', ''),
                'kilometers': item.get('kilometers', {}).get('value', ''),
                'gearbox': item.get('gearbox', ''),
                'area': item.get('area', ''),
                'city': item.get('city', ''),
                'listing_id': item.get('id', ''),
                'date_added': item.get('date', ''),
                'url': f"https://www.yad2.co.il/item/{item.get('id', '')}"
            }
            
            # Log extracted details
            self.logger.debug(f"Extracted details: {json.dumps(details, ensure_ascii=False)}")
            
            return details
        except Exception as e:
            self.logger.error(f"Error extracting car details: {str(e)}")
            return {}

    def scrape_cars(self, 
                    manufacturers_models: List[tuple], 
                    year_range: Optional[Tuple[int, int]] = None,
                    max_pages: int = 5) -> pd.DataFrame:
        all_cars = []
        session = requests.Session()
        
        for manufacturer, model in manufacturers_models:
            self.logger.info(f"Scraping listings for {manufacturer} {model}")
            page = 1
            
            while page <= max_pages:
                try:
                    # Construct parameters
                    params = self._construct_query_params(manufacturer, model, year_range, page)
                    self.logger.debug(f"Query parameters: {params}")
                    
                    # Make the request
                    response = session.get(
                        self.base_url,
                        headers=self.headers,
                        params=params,
                        timeout=10
                    )
                    
                    # Log request details
                    self.logger.debug(f"Request URL: {response.url}")
                    self.logger.debug(f"Response status: {response.status_code}")
                    self.logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        # Log raw response for debugging
                        self.logger.debug(f"Response content: {response.text[:1000]}...")
                        
                        try:
                            data = response.json()
                            self.logger.debug(f"JSON data structure: {json.dumps(data.keys(), ensure_ascii=False)}")
                            
                            # Try different possible paths in the JSON structure
                            items = (data.get('data', {}).get('feed', {}).get('feed_items', []) or
                                   data.get('data', {}).get('items', []) or
                                   data.get('items', []))
                            
                            if not items:
                                self.logger.info(f"No items found in response structure")
                                self.logger.debug(f"Available data keys: {data.keys()}")
                                break
                            
                            for item in items:
                                car_details = self._extract_car_details(item)
                                if car_details:
                                    car_details['manufacturer'] = manufacturer
                                    car_details['model'] = model
                                    all_cars.append(car_details)
                            
                            self.logger.info(f"Scraped {len(items)} items from page {page}")
                            page += 1
                            time.sleep(2)
                            
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse JSON response: {str(e)}")
                            self.logger.debug(f"Raw response: {response.text[:500]}...")
                            break
                            
                    else:
                        self.logger.error(f"Request failed with status code: {response.status_code}")
                        self.logger.debug(f"Response content: {response.text[:500]}...")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error during scraping: {str(e)}")
                    break
        
        df = pd.DataFrame(all_cars)
        if df.empty:
            self.logger.warning("No data was collected. DataFrame is empty.")
        else:
            self.logger.info(f"Collected {len(df)} total listings")
        return df

def main():
    scraper = Yad2CarScraper()
    
    cars_to_scrape = [
        ('hyundai', 'tucson'),
    ]
    
    year_range = (2018, 2024)
    
    df = scraper.scrape_cars(
        manufacturers_models=cars_to_scrape,
        year_range=year_range,
        max_pages=3
    )
    
    if not df.empty:
        scraper.save_to_csv(df)
    else:
        print("No data was collected. Please check the logs for details.")

if __name__ == "__main__":
    main()