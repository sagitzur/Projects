import requests
import pandas as pd
import json
import openpyxl
from flask import Flask, render_template_string
import logging

app = Flask(__name__)

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
            "pricelist_link_url": item.get("pricelist_link_url", ""),
            "images_urls": item.get("images_urls", []) if isinstance(item.get("images_urls"), list) else []
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
        df["images_urls"] = df["images_urls"].apply(
        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else '[]'
    )
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

@app.route('/')
def display_data():
    df = pd.read_excel('yad2_vehicles.xlsx')
    # Parse JSON strings in images_urls column
    # Clean and parse images_urls
    def clean_urls(x):
        try:
            if isinstance(x, str):
                # Parse JSON string from Excel
                urls = json.loads(x)
                # Ensure it's a list
                if isinstance(urls, list):
                    return urls
            return []
        except:
            print(f"Error parsing URLs: {x}")
            return []
    from html import escape
    #df['images_urls'] = df['images_urls'].apply(clean_urls)
    df['images_urls'] = df['images_urls'].apply(
        lambda urls: escape(json.dumps(urls)) if isinstance(urls, list) else urls
    )


    # Add debug logging
    app.logger.debug(f"First row images_urls: {df['images_urls'].iloc[1]}")
    
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
                            // Apply conditional formatting
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

                            // Initialize tooltips
                            $('[data-toggle="tooltip"]').tooltip();

                            // Initialize modals
                            $('.info-text, .search-text').on('click', function() {
                                var content = $(this).data('content');
                                $('#modalContent').text(content);
                                $('#infoModal').modal('show');
                            });
                            
                            $('.image-urls').on('click', function() {
    var imagesData = $(this).attr('data-images');
    var imagesData = $(this).attr('data-images');
    console.log('Raw data-images:', imagesData); // Debugging step
                                  
    try {
        var images = JSON.parse(imagesData);
        console.log('Parsed images:', images);
        
        if (!Array.isArray(images)) {
            console.error('Not an array:', images);
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
                tfoot input {
                    width: 100%;
                    padding: 3px;
                    box-sizing: border-box;
                }
                .dataTables_wrapper .dataTables_filter {
                    float: right;
                    text-align: right;
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
                            <td class="image-urls" data-images="{{ cell }}" style="cursor: pointer;">
    View Images)</td>
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

            <!-- Modal -->
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
                                  
            <!-- Modal for images -->
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
        </body>
    </html>
    """, df=df, zip=zip)

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
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True)

    
# Save the JSON data to a file
