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
        filtered_items = []
        for item in self.all_items:
            filtered_item = {
            #"line_1": item.get("line_1", ""),
            "company": item.get("line_2", "טרייד מוביל"),
            #"line_3": item.get("line_3", None),
            "city": item.get("city", ""),
            "model": item.get("row_1",""),
            "submodel": item.get("row_2", ""),
            #"row_3": item.get("row_3", [2022, "יד ראשונה", "ק״מ 37,700"]),
            "year": item.get("year", 0),
            "hand": item.get("Hand_text", ""),
            "kilometers": item.get("kilometers", 0),
            "price": item.get("price", 0),
            "contact_name": item.get("contact_name", ""),
            "info_text": item.get("info_text", ""),
            "search_text": item.get("search_text", ""),
            "date": item.get("date", ""),
            "date_added": item.get("date_added", ""),
            "OwnerID_text": item.get("OwnerID_text", ""),
            "pricelist_link_url": item.get("pricelist_link_url", "")
            }
            # Extract more_details
            more_details = item.get("more_details", [])
            for detail in more_details:
                #if detail["name"] == "kilometers":
                #    filtered_item["kilometers"] = detail["value"]
                #elif detail["name"] == "engineType":
                #    filtered_item["engineType"] = detail["value"]
                #elif detail["name"] == "gearBox":
                #    filtered_item["gearBox"] = detail["value"]
                #elif detail["name"] == "color":
                #    filtered_item["color"] = detail["value"]
                #elif detail["name"] == "month":
                if detail["name"] == "month":
                    filtered_item["Start Month"] = detail["value"]

            filtered_items.append(filtered_item)
        df = pd.DataFrame(filtered_items)
        df["kilometers"] = df["kilometers"].apply(lambda x: int(str(x).replace(',', '')))
        df["price"] = df["price"].apply(lambda x: int(str(x).replace(',', '').replace(' ₪', '')) if str(x).replace(',', '').replace(' ₪', '').isdigit() else "N/A")
        df["year"] = df["year"].apply(lambda x: int(x) if str(x).isdigit() else 0)

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.drop_duplicates(inplace=True)
            df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']

            # Add autofilter to header
            worksheet.auto_filter.ref = worksheet.dimensions

            # Define a function to apply conditional formatting
            def apply_conditional_formatting(column, start_color, mid_color, end_color):
                color_scale = openpyxl.formatting.rule.ColorScaleRule(
                    start_type='min', start_color=start_color,
                    mid_type='percentile', mid_value=50, mid_color=mid_color,
                    end_type='max', end_color=end_color
                )
                worksheet.conditional_formatting.add(f'{column}2:{column}{len(df) + 1}', color_scale)

            # Apply conditional formatting for kilometers, price, and year
            apply_conditional_formatting('G', '00FF00', 'FFFF00', 'FF0000')
            apply_conditional_formatting('H', 'FF0000', 'FFFF00', '00FF00')
            apply_conditional_formatting('F', 'FF0000', 'FFFF00', '00FF00')

        print(f"Data has been saved to '{filename}'.")

if __name__ == "__main__":
    base_url = "https://gw.yad2.co.il/feed-search-legacy/vehicles/cars"
    params = {
        "manufacturer": 21,
        "model": 10291,
        "year": "2022-2024",
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
