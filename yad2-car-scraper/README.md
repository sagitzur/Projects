# Yad2 Car Scraper

A Python script to scrape used car listings from Yad2.co.il based on manufacturer, model, and year range, with a web interface for data visualization.

## Features
- Scrape multiple car models simultaneously
- Filter by year range
- Export results to JSON and Excel
- Detailed logging
- Rate limiting to respect server resources
- Web interface using Flask
- Linear regression analysis with data visualization

## Requirements
- Python 3.7+
- requests
- pandas
- openpyxl
- Flask
- matplotlib
- scikit-learn
- bidi

## Installation
```bash
git clone [your-repo-url]
cd yad2-car-scraper
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Usage
1. Run the Flask web server:
    ```bash
    python main.py
    ```
2. Open your web browser and go to `http://127.0.0.1:5000/`.
3. Select the manufacturer and model, then click "Show Linear Regression" to visualize the data.

## Files
- `main.py`: The main script to run the web server and handle scraping and data visualization.
- `requirements.txt`: List of required Python packages.
- `README.md`: This file.

## License
This project is licensed under the MIT License.