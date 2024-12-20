import requests
import pandas as pd
import json
import openpyxl

class Yad2CarScraper:
    def __init__(self, base_url, params):
        self.base_url = base_url
        self.params = params
        self.all_items = []

    def fetch_page(self, page_number):
        self.params["page"] = page_number
        response = requests.get(self.base_url, params=self.params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}")
            return None

    def scrape(self):
        data = self.fetch_page(1)
        if data:
            data_page = data['data']
            pagination = data_page.get("pagination", {})
            current_page = pagination.get("current_page", 1)
            last_page = pagination.get("last_page", 1)
            items_per_page = pagination.get("max_items_per_page", 40)
            total_items = pagination.get("total_items", 0)
            
            print(f"Current Page: {current_page}")
            print(f"Last Page: {last_page}")
            print(f"Items per Page: {items_per_page}")
            print(f"Total Items: {total_items}")
            
            items = data.get("data", {}).get("feed", {}).get("feed_items", [])
            self.all_items.extend(items)

            for page_number in range(2, last_page + 1):
                data = self.fetch_page(page_number)
                if data:
                    items = data.get("data", {}).get("feed", {}).get("feed_items", [])
                    self.all_items.extend(items)
                    print(f"Processed page {page_number} with {len(items)} items.")
                else:
                    print(f"No data found on page {page_number}.")
        else:
            print("Failed to retrieve data from the first page.")

    def save_to_json(self, filename):
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(self.all_items, json_file, indent=4, ensure_ascii=False)
            print(f"JSON data has been saved to '{filename}'.")

    def save_to_excel(self, filename):
        df = pd.DataFrame(self.all_items)
        df.to_excel(filename, index=False)
        print(f"Data has been saved to '{filename}'.")

if __name__ == "__main__":
    base_url = "https://gw.yad2.co.il/feed-search-legacy/vehicles/cars"
    params = {
        "manufacturer": 21,
        "model": 10291,
        "year": "2022-2023",
        "engineval": "1598-1598",
        "km": "-1-50000",
        "max_items_per_page": 2000,
        "page": 1
    }

    scraper = Yad2CarScraper(base_url, params)
    scraper.scrape()
    scraper.save_to_json("yad2_vehicles.json")
    scraper.save_to_excel("yad2_vehicles.xlsx")

# Save the JSON data to a file
