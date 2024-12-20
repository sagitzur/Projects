import requests
import pandas as pd
import json

# Base URL for the Yad2 API
base_url = "https://gw.yad2.co.il/feed-search-legacy/vehicles/cars"

# Parameters for the first page
params = {
    "manufacturer": 21,
    "model": 10291,
    "year": "2022-2023",
    "engineval": "1598-1598",
    "km": "-1-50000",
    "max_items_per_page": 2000,
    "page": 1  # Start with the first page
}

# Function to fetch data from a specific page
def fetch_page(page_number):
    params["page"] = page_number
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

# Initialize an empty list to store all items
all_items = []

# Fetch the first page to get pagination details
data = fetch_page(1)
if data:
    data_page = data['data']
    pagination = data_page.get("pagination", {})
    current_page = pagination.get("current_page", 1)
    last_page = pagination.get("last_page", 1)
    items_per_page = pagination.get("max_items_per_page", 40)
    total_items = pagination.get("total_items", 0)
    
    # Print pagination details
    print(f"Current Page: {current_page}")
    print(f"Last Page: {last_page}")
    print(f"Items per Page: {items_per_page}")
    print(f"Total Items: {total_items}")
    
    # Process the first page's items
    items = data.get("data", {}).get("feed", {}).get("feed_items", [])
    #print(items)
    all_items.extend(items)


    # Fetch and process additional pages if they exist
    for page_number in range(2, last_page + 1):
        data = fetch_page(page_number)
        if data:
            items = data.get("data", {}).get("feed", {}).get("feed_items", [])
            all_items.extend(items)
            print(f"Processed page {page_number} with {len(items)} items.")
        else:
            print(f"No data found on page {page_number}.")
else:
    print("Failed to retrieve data from the first page.")

with open("yad2_vehicles.json", "w", encoding="utf-8") as json_file:
        json.dump(all_items, json_file, indent=4, ensure_ascii=False)
        print("JSON data has been saved to 'yad2_vehicles.json'.")
#pretty_json = json.dumps(all_items, indent=4, ensure_ascii=False)
#print(pretty_json)

# Convert the list of items to a DataFrame
df = pd.DataFrame(all_items)
print(df)
# Save the DataFrame to an Excel file
df.to_excel("yad2_vehicles.xlsx", index=False)
print("Data has been saved to 'yad2_vehicles.xlsx'.")

# Save the JSON data to a file
