import json
import requests
import time

from reports.auto_publishing_compare import ext_entry

# URL for the EclipseFdn auto-publish allow-list
API_ENDPOINT = "https://open-vsx.org/api"
OUTPUT_FILE = 'namespaces_and_extension_names.json'
OPEN_VSX_EXTENSIONS_FILE = 'open_vsx_extensions.json'

def load_json_file(filepath):
    """Safely loads local JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def get_with_retries(url):
    retry_count = 0
    done = False
    response = None
    while not done:
        try:
            response = requests.get(url, timeout=10)
            done = True
        except Exception as e:
            print(f"Error retrieving {url}: {e}")
            retry_count += 1
            if retry_count > 5:
                done = True
            else:
                print(f"Retry #{retry_count} in 5 seconds...")
                time.sleep(5)
    return response

def main():

    openvsx_extensions = load_json_file(OPEN_VSX_EXTENSIONS_FILE)
    if not openvsx_extensions:
        print(f"No Open VSX data found: {OPEN_VSX_EXTENSIONS_FILE}. Exiting.")
        return

    print("Processing Open VSX extensions...")
    ovsx_extension_names = {}
    ovsx_namespaces = {}
    for ext in openvsx_extensions:
        namespace = ext.get('namespace')
        name = ext.get('name')
        if ovsx_namespaces.get(namespace):
            ovsx_namespaces[namespace] = ovsx_namespaces.get(namespace).append(name)
        else:
            ovsx_namespaces[namespace] = [name]
        if ovsx_extension_names.get(name):
            ovsx_extension_names[name] = ovsx_extension_names.get(name).append(namespace)
        else:
            ovsx_extension_names[name] = [namespace]
        namespace_url = f"{API_ENDPOINT}/{namespace}"
        response = get_with_retries(namespace_url)
        results = response.json()
        if not results['verified']:
            if not ovsx_namespaces.get(namespace):
                ovsx_namespaces[namespace] = results['extensions']

    results = {'namespaces': ovsx_namespaces, 'names': ovsx_extension_names}
    f = open(OUTPUT_FILE, 'w')
    f.write(json.dumps(f, indent=4))
    f.close()
if __name__ == "__main__":
    main()