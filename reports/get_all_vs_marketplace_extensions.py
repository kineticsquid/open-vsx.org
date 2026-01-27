"""
Script to collect metadata on all extensions published on VS Code Marketplace. Outputs 
both a JSON and a CSV file. Note, this relies on interfaces that are not fully documented 
and are subject to change. 
"""

import requests
import json
from datetime import datetime
import time
import re

CSV_FILE_NAME = 'vs_code_extensions.csv'
JSON_FILE_NAME = 'vs_code_extensions.json'

def get_ms_info(ext):
    extension_name = ext['extensionName']
    publisher_name = ext['publisher']['publisherName']
    display_name = ext['displayName'].replace(',', ' ')
    latest_version = ext['versions'][0]['version']
    last_updated = ext['versions'][0]['lastUpdated']

    try:
        repo = [prop for prop in ext['versions'][0]['properties'] if prop['key'] == 'Microsoft.VisualStudio.Services.Links.Source'][0]['value']
    except Exception:
        repo = None

    try:
        pricing = [prop for prop in ext['versions'][0]['properties'] if prop['key'] == 'Microsoft.VisualStudio.Services.Content.Pricing'][0]['value']
    except Exception:
        pricing = None
    
    return extension_name, publisher_name, display_name, latest_version, last_updated, repo, pricing

def convert_date_str(input_str):
    date_str = input_str[0:input_str.find('T')]
    date = datetime.strptime(date_str, '%Y-%m-%d')
    return_str = date.strftime("%-m/%-d/%Y")
    return return_str

def get_all_extensions_old():
    MS_API_URL = 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery'
    MS_HEADERS = {
        'content-type': 'application/json',
        'accept': 'application/json;api-version=3.0-preview.1',
        'accept-encoding': 'gzip'
    }
    # Looks like 1000 is the max page size
    get_all_extensions_payload = {
        "assetTypes": [
            "Microsoft.VisualStudio.Services.Icons.Default",
            "Microsoft.VisualStudio.Services.Icons.Branding",
            "Microsoft.VisualStudio.Services.Icons.Small"
        ],
        "filters": [
            {
                "criteria": [
                    {
                        "filterType": 8,
                        "value": "Microsoft.VisualStudio.Code"
                    },
                    {
                        "filterType": 10,
                        "value": "target:\"Microsoft.VisualStudio.Code\" "
                    },
                    {
                        "filterType": 12,
                        "value": "37888"
                    }
                ],
                "direction": 2,
                "pageSize": 1000,
                "pageNumber": 1,
                "sortBy": 4,
                "sortOrder": 0,
                "pagingToken": None
            }
        ],
        # "flags": 870
        "flags": 914
    }
    all_extensions = []
    total_all_versions = 0
    while True:
        response = requests.post(MS_API_URL, headers=MS_HEADERS, data=json.dumps(get_all_extensions_payload))
        response.raise_for_status()
        time.sleep(5)
        vsx_results = response.json()
        extensions = vsx_results['results'][0]['extensions']
        # for extension in extensions:
        #     license = get_license(extension)
        #     extension['license'] = license
        all_extensions = all_extensions + extensions
        print(f'Retrieved {len(extensions)} new extensions. {len(all_extensions)} total extensions.')
        if len(extensions) == 0:
            break
        else:
            get_all_extensions_payload['filters'][0]['pageNumber'] = get_all_extensions_payload['filters'][0]['pageNumber'] + 1

    return all_extensions


def get_all_extensions():
    MS_API_URL = 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery'
    MS_HEADERS = {
        'content-type': 'application/json',
        'accept': 'application/json;api-version=3.0-preview.1',
        'accept-encoding': 'gzip'
    }

    # Standard VS Code Marketplace Categories
    # "Other" is essentially a catch-all that can be large, so we process it last.
    CATEGORIES = [
        "Azure", "Data Science", "Debuggers", "Education", "Extension Packs",
        "Formatters", "Keymaps", "Language Packs", "Linters", "Machine Learning",
        "Notebooks", "Programming Languages", "SCM Providers", "Snippets",
        "Testing", "Themes", "Visualization", "Other"
    ]

    # Use a dictionary keyed by Extension ID to automatically deduplicate
    all_extensions_dict = {}

    for category in CATEGORIES:
        print(f"--- Scraping Category: {category} ---")
        page_number = 1

        while True:
            payload = {
                "assetTypes": [
                    "Microsoft.VisualStudio.Services.Icons.Default",
                    "Microsoft.VisualStudio.Services.Icons.Branding",
                    "Microsoft.VisualStudio.Services.Icons.Small"
                ],
                "filters": [
                    {
                        "criteria": [
                            {
                                "filterType": 8,
                                "value": "Microsoft.VisualStudio.Code"
                            },
                            {
                                "filterType": 10,
                                "value": "target:\"Microsoft.VisualStudio.Code\" "
                            },
                            {
                                "filterType": 12,
                                "value": "37888"
                            },
                            # Add the Category Filter (Type 5)
                            {
                                "filterType": 5,
                                "value": category
                            }
                        ],
                        "direction": 2,  # Descending
                        "pageSize": 1000,
                        "pageNumber": page_number,
                        "sortBy": 4,  # Sort by Install Count
                        "sortOrder": 0,
                        "pagingToken": None
                    }
                ],
                "flags": 914
            }

            try:
                response = requests.post(MS_API_URL, headers=MS_HEADERS, data=json.dumps(payload))
                response.raise_for_status()
                data = response.json()

                # Check if 'results' exists and has data
                if 'results' not in data or not data['results']:
                    break

                extensions = data['results'][0].get('extensions', [])

                if not extensions:
                    break

                new_count = 0
                for ext in extensions:
                    # Use extensionId as the unique key
                    ext_id = ext.get('extensionId')
                    if ext_id and ext_id not in all_extensions_dict:
                        all_extensions_dict[ext_id] = ext
                        new_count += 1

                print(
                    f"  Page {page_number}: Found {len(extensions)} exts ({new_count} unique new). Total Unique: {len(all_extensions_dict)}")

                # Increase page number
                page_number += 1

                # Sleep to be nice to the API
                time.sleep(5)

            except Exception as e:
                print(f"Error on {category} page {page_number}: {e}")
                break

    return list(all_extensions_dict.values())

if __name__ == '__main__':

    all_extensions = get_all_extensions()
    # Output CSV File
    csv_file = open(CSV_FILE_NAME, 'w')
    csv_file.write("MS Publisher (Namespace), MS Extension, MS DisplayName, MS Version, MS Date, Repo\n")
    for ext in all_extensions:
        ms_extension_name, ms_publisher_name, ms_display_name, ms_latest_version, ms_last_updated, ms_repo, ms_pricing = get_ms_info(ext)
        csv_file.write("%s, %s, %s, %s, %s, %s\n" % (
                ms_publisher_name,
                ms_extension_name,
                ms_display_name,
                ms_latest_version,
                convert_date_str(ms_last_updated),
                ms_repo
                ))
    # Output JSON File
    json_file = open(JSON_FILE_NAME, 'w')
    json_file.write(json.dumps(all_extensions, indent=4))
    json_file.close()