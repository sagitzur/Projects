import requests
import pandas as pd
import json
import openpyxl
from flask import Flask, render_template_string, request
import logging
import matplotlib.pyplot as plt
import io
import base64
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.font_manager as fm
from bidi.algorithm import get_display

# Use the Agg backend for Matplotlib
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# Dictionary to store manufacturer and model information
manufacturers_models = {
    "Hyundai": {"manufacturer": 21, "model": 10291},
    "KIA": {"manufacturer": 48, "model": 10720},
    "Toyota": {"manufacturer": 19, "model": 10238}
}

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
        self.all_items = []  # Clear previous items
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
                "company": item.get("line_2", "טרייד מוביל"),
                "city": item.get("city", ""),
                "model": item.get("row_1",""),
                "submodel": item.get("row_2", ""),
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
                "pricelist_link_url": item.get("pricelist_link_url", ""),
                "images_urls": item.get("images_urls", []) if isinstance(item.get("images_urls"), list) else []
            }
            more_details = item.get("more_details", [])
            for detail in more_details:
                if detail["name"] == "month":
                    filtered_item["Start Month"] = detail["value"]

            filtered_items.append(filtered_item)
        df = pd.DataFrame(filtered_items)
        #print(df.head())
        df["kilometers"] = df["kilometers"].apply(lambda x: int(str(x).replace(',', '')))
        df["price"] = df["price"].apply(lambda x: int(str(x).replace(',', '').replace(' ₪', '')) if str(x).replace(',', '').replace(' ₪', '').isdigit() else "N/A")
        df["year"] = df["year"].apply(lambda x: int(x) if str(x).isdigit() else 0)
        df["images_urls"] = df["images_urls"].apply(
            lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else '[]'
        )
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.drop_duplicates(inplace=True)
            df.dropna(subset=['model', 'submodel', 'city'], inplace=True)
            df = df[df['model'].str.strip() != '']
            df = df[df['submodel'].str.strip() != '']
            df = df[df['city'].str.strip() != '']
            df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']

            worksheet.auto_filter.ref = worksheet.dimensions

            def apply_conditional_formatting(column, start_color, mid_color, end_color):
                color_scale = openpyxl.formatting.rule.ColorScaleRule(
                    start_type='min', start_color=start_color,
                    mid_type='percentile', mid_value=50, mid_color=mid_color,
                    end_type='max', end_color=end_color
                )
                worksheet.conditional_formatting.add(f'{column}2:{column}{len(df) + 1}', color_scale)

            apply_conditional_formatting('G', '00FF00', 'FFFF00', 'FF0000')
            apply_conditional_formatting('H', 'FF0000', 'FFFF00', '00FF00')
            apply_conditional_formatting('F', 'FF0000', 'FFFF00', '00FF00')

        print(f"Data has been saved to '{filename}'.")

@app.route('/linear_regression', methods=['POST'])
def linear_regression():
    df = pd.read_excel('yad2_vehicles.xlsx')
    df = df[pd.to_numeric(df['price'], errors='coerce').notnull()]
    df.loc[:, 'price'] = df['price'].astype(int)
    df = df[df['price'] != "N/A"]

    # Filter according to the selected status
    filtered_df = df.copy()
    for column in request.form:
        if column in df.columns:
            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(request.form[column], na=False, case=False, regex=False)]

    if filtered_df.empty:
        return render_template_string("""
        <html>
            <head>
                <title>Linear Regression</title>
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
            </head>
            <body>
                <div class="container">
                    <h1 class="my-4">Linear Regression: Price vs Kilometers</h1>
                    <p>No data available for the selected filters.</p>
                    <button class="btn btn-primary mt-4" onclick="window.close()">Close</button>
                </div>
            </body>
        </html>
        """)

    X = filtered_df[['price']]
    y = filtered_df['kilometers']
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    plt.figure(figsize=(10, 6))
    plt.scatter(filtered_df['price'], filtered_df['kilometers'], color='blue', label='Data points')
    plt.plot(filtered_df['price'], y_pred, color='red', linewidth=2, label='Linear regression line')
    plt.xlabel('Price')
    plt.ylabel('Kilometers')
    plt.title('Linear Regression: Kilometers vs Price')
    plt.legend()

    # Set font properties for Hebrew characters
    prop = fm.FontProperties(family='Arial')

    for i, txt in enumerate(filtered_df['submodel']):
        mixed_text = f"{txt}, {filtered_df['city'].iloc[i]}, {filtered_df['year'].iloc[i]}"
        display_text = get_display(mixed_text)  # Correct the direction of mixed Hebrew and English text
        plt.annotate(display_text, (filtered_df['price'].iloc[i], filtered_df['kilometers'].iloc[i]), fontproperties=prop)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()  # Close the plot to avoid GUI issues
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return render_template_string("""
    <html>
        <head>
            <title>Linear Regression</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        </head>
        <body>
            <div class="container">
                <h1 class="my-4">Linear Regression: Kilometers vs Price</h1>
                <img src="data:image/png;base64,{{ plot_url }}" class="img-fluid" />
                <button class="btn btn-primary mt-4" onclick="window.close()">Close</button>
            </div>
        </body>
    </html>
    """, plot_url=plot_url)

@app.route('/', methods=['GET', 'POST'])
def display_data():
    selected_manufacturer = request.form.get('manufacturer', 'Hyundai')
    selected_model = manufacturers_models[selected_manufacturer]

    base_url = "https://gw.yad2.co.il/feed-search-legacy/vehicles/cars"
    params = {
        "manufacturer": selected_model["manufacturer"],
        "model": selected_model["model"],
        "year": "2022-2024",
        "km": "-1-50001",
        "max_items_per_page": 2000,
        "page": 1
    }
    # delete engineval if model is Toyota
    if (params["manufacturer"] != manufacturers_models["Toyota"]["manufacturer"]):
        params["engineval"] = "1598-1598"
    scraper = Yad2CarScraper(base_url, params)
    scraper.scrape()
    scraper.save_to_json("yad2_vehicles.json")
    scraper.save_to_excel("yad2_vehicles.xlsx")

    df = pd.read_excel('yad2_vehicles.xlsx')

    return render_template_string("""
    <html>
        <head>
            <title>Yad2 Vehicles Data</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.css">
            <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
            <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
            <script>
                $(document).ready(function() {
                        // Setup - add a text input to each footer cell
                        $('#data-table tfoot th').each(function() {
                            var title = $(this).text();
                            $(this).html('<input type="text" placeholder="Search ' + title + '" />');
                        });
                        var table = $('#data-table').DataTable({
                            footerCallback: function(row, data, start, end, display) {
                                // Apply the search
                                this.api().columns().every(function() {
                                    var that = this;
                                    $('input', this.footer()).on('keyup change clear', function() {
                                        if (that.search() !== this.value) {
                                            that.search(this.value).draw();
                                        }
                                    });
                                });
                            },
                        drawCallback: function(settings) {
                            $('#data-table tbody tr').each(function() {
                                var price = parseInt($(this).find('td:eq(7)').text().replace(' ₪', '').replace(',', ''));
                                if (price > 150000) {
                                    $(this).find('td:eq(7)').css('background-color', '#FF0000');
                                } else if (price > 100000) {
                                    $(this).find('td:eq(7)').css('background-color', '#FFFF00');
                                } else {
                                    $(this).find('td:eq(7)').css('background-color', '#00FF00');
                                }

                                var kilometers = parseInt($(this).find('td:eq(6)').text().replace(',', ''));
                                if (kilometers > 50000) {
                                    $(this).find('td:eq(6)').css('background-color', '#FF0000');
                                } else if (kilometers > 20000) {
                                    $(this).find('td:eq(6)').css('background-color', '#FFFF00');
                                } else {
                                    $(this).find('td:eq(6)').css('background-color', '#00FF00');
                                }
                            });

                            $('[data-toggle="tooltip"]').tooltip();

                            $('.info-text, .search-text').on('click', function() {
                                var content = $(this).data('content');
                                $('#modalContent').text(content);
                                $('#infoModal').modal('show');
                            });
                            
                            $('.image-urls').on('click', function() {
                                var imagesData = $(this).attr('data-images');
                                try {
                                    var images = JSON.parse(imagesData);
                                    if (!Array.isArray(images)) {
                                        return;
                                    }
                                    var modalBody = $('#imageModal .modal-body');
                                    modalBody.empty();
                                    images.forEach(function(url) {
                                        modalBody.append(`
                                            <div class="mb-3">
                                                <img src="${url}" class="img-fluid" />
                                            </div>
                                        `);
                                    });
                                    $('#imageModal').modal('show');
                                } catch (e) {
                                    console.error('JSON parse error:', e);
                                }
                            });
                        }
                    });
                });
            </script>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                }
                .container {
                    margin: 0 auto;
                    padding: 0;
                    width: 95%;
                }
                tfoot input {
                    width: 100%;
                    padding: 3px;
                    box-sizing: border-box;
                }
                table {
                    width: 100%;
                    margin: 0;
                    padding: 0;
                }
                .dataTables_wrapper .dataTables_filter {
                    float: right;
                    text-align: left;
                }
                .dataTables_wrapper .dataTables_length {
                    float: left;
                }
                .dataTables_wrapper .dataTables_info {
                    float: left;
                }
                .dataTables_wrapper .dataTables_paginate {
                    float: right;
                }
                .info-text, .search-text {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 150px;
                    cursor: pointer;
                }
                .info-text::after, .search-text::after {
                    content: '...';
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="my-4">Yad2 Vehicles Data</h1>
                <form method="post">
                    <div class="form-group">
                        <label for="manufacturer">Select Manufacturer:</label>
                        <select class="form-control" id="manufacturer" name="manufacturer" onchange="this.form.submit()">
                            {% for manufacturer in manufacturers_models.keys() %}
                            <option value="{{ manufacturer }}" {% if manufacturer == selected_manufacturer %}selected{% endif %}>{{ manufacturer }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </form>
                <button class="btn btn-info my-4" id="linearRegressionBtn">Show Linear Regression</button>
                <table id="data-table" class="display table table-striped table-bordered">
                    <thead>
                        <tr>
                            {% for column in df.columns %}
                            <th>{{ column }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tfoot>
                        <tr>
                            {% for column in df.columns %}
                            <th>{{ column }}</th>
                            {% endfor %}
                        </tr>
                    </tfoot>
                    <tbody>
                        {% for row in df.iterrows() %}
                        <tr>
                            {% for cell, column in zip(row[1], df.columns) %}
                            {% if column == 'images_urls' %}
                            <td class="image-urls" data-images="{{ cell }}" style="cursor: pointer;"> View Images</td>
                            {% elif column in ['info_text', 'search_text'] %}
                            <td class="{{ column }}" data-toggle="tooltip" title="{{ cell }}" data-content="{{ cell }}">...</td>
                            {% else %}
                            <td>{{ cell }}</td>
                            {% endif %}
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="modal fade" id="infoModal" tabindex="-1" role="dialog" aria-labelledby="infoModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="infoModalLabel">Details</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body" id="modalContent">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
                                  
            <div class="modal fade" id="imageModal" tabindex="-1" role="dialog" aria-labelledby="imageModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="imageModalLabel">Images</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                document.getElementById('linearRegressionBtn').addEventListener('click', function() {
                    var formData = new FormData();
                    $('#data-table tfoot input').each(function() {
                        var column = $(this).attr('placeholder').replace('Search ', '');
                        var value = $(this).val();
                        if (value) {
                            formData.append(column, value);
                        }
                    });

                    fetch('/linear_regression', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.text())
                    .then(html => {
                        var newWindow = window.open();
                        newWindow.document.write(html);
                    });
                });
            </script>
        </body>
    </html>
    """, df=df, manufacturers_models=manufacturers_models, selected_manufacturer=selected_manufacturer, zip=zip)

if __name__ == "__main__":
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True)
