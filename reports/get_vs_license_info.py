"""
Script to retrieve license information for vs code extensions
"""

import requests
import json
import re

VS_CODE_EXTENSIONS_FILE_NAME = 'vs_code_extensions.json'
SLEEP_SECONDS = 1
LICENSE_FILE_NAME = 'vs_code_licenses.json'

def get_license(extension):
    # https://marketplace.visualstudio.com/items/ms-python.vscode-pylance/license
    license = "None"
    publisher = extension['publisher']['publisherName']
    extension_name = extension['extensionName']
    url = f"https://{publisher}.gallery.vsassets.io/_apis/public/gallery/publisher/{publisher}/extension/{extension_name}/latest/assetbyname/Microsoft.VisualStudio.Services.Content.License"
    response = requests.get(url)
    if response.status_code == 200:
        license_content = response.text
        if 'MICROSOFT SOFTWARE LICENSE TERMS' in license_content:
            license = 'Microsoft Commercial'
        elif 'MIT ' in license_content or 'MIT\n' in license_content:
            license = "MIT"
        elif 'Apache' in license_content:
            license = 'Apache'
        elif 'Eclipse Public License' in license_content:
            license = 'EPL'
        elif 'BSD ' in license_content or 'BSD\n' in license_content:
            license = 'BSD'
        elif 'MPL ' in license_content or 'Mozilla' in license_content:
            license = 'MPL'
        elif 'GNU LESSER' in license_content or 'GNU Lesser' in license_content:
            license = 'LGPL'
        elif 'GNU GENERAL' in license_content or 'GNU General' in license_content:
            license = 'GPL'
        elif 'GNU AFFERO' in license_content or 'GNU Affero' in license_content:
            license = 'AGPL'
        elif 'GPL ' in license_content or 'GPL\n' in license_content:
            license = 'GPL'
        elif 'ISC ' in license_content or 'ISC\n' in license_content:
            license = 'ISC'
        elif 'Creative Commons' in license_content or 'creativecommons.org' in license_content:
            license = 'Creative Commons'
        else:
            clean_text = re.sub(r'\s+', ' ', license_content)
            if len(clean_text) > 0:
                license = f'Other - {clean_text[:80]}'
            else:
                license = 'None'
    return license

extensions_file = open(VS_CODE_EXTENSIONS_FILE_NAME, 'r')
extensions = json.load(extensions_file)
extensions_file.close()
try:
    licenses_file = open(LICENSE_FILE_NAME, 'r')
    licenses = json.load(licenses_file)
    licenses_file.close()
except Exception as e:
    licenses = {}
try:
    count = 1
    processed = 1
    for extension in extensions:
        extension_id = f"{extension['publisher']['publisherName']}.{extension['extensionName']}"
        license = licenses.get(extension_id)
        if license is None or license['license'] is None:
            license = get_license(extension)
            licenses[extension_id] = {
                "license": license,
                "version": extension['versions'][0]['version']
            }
            print(f"{extension_id}: {license} - Processed {processed} extensions. {count} total extensions.")
            processed += 1
        count += 1
except Exception as e:
    print(e)
finally:
    # Output JSON File
    output_file = open(LICENSE_FILE_NAME, 'w')
    output_file.write(json.dumps(licenses, indent=4))
    output_file.close()