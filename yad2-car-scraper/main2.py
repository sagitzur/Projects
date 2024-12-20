import requests
import json

# Define the base URL and headers
base_url = "https://gw.yad2.co.il/feed-search-legacy/vehicles/cars"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,he;q=0.8',
    'Origin': 'https://www.yad2.co.il',
    'Referer': 'https://www.yad2.co.il/vehicles/cars',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

# Define the parameters for the specific car model
params = {
    'manufacturer': 'Hyundai',  # Replace with desired manufacturer
    'model': 'Tuscon',        # Replace with desired model
    'price': '100000-500000',    # Example price range
    'year': '2022-2023',       # Example year range
}

# Send the GET request to the API
response = requests.get(base_url, headers=headers, params=params)

# Check if the request was successful
if response.status_code == 200:
    try:
        data = response.json()
        # Inspect the structure of the response
        print(json.dumps(data, indent=4))
        # Process the data as needed
    except ValueError:
        print('Failed to parse JSON response.')
        print(response.text)  # Print raw response for debugging
else:
    print(f'Failed to retrieve data: {response.status_code}')
