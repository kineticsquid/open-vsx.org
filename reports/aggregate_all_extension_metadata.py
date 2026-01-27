import json
import requests
import pandas as pd
from datetime import datetime

# URL for the EclipseFdn auto-publish allow-list
AUTO_PUBLISH_URL = "https://raw.githubusercontent.com/EclipseFdn/publish-extensions/refs/heads/master/extensions.json"
OUTPUT_FILE = ('all_extensions_metadata.csv')
VS_CODE_LICENSES_FILE = 'vs_code_licenses.json'
VS_CODE_EXTENSIONS_FILE = 'vs_code_extensions.json'
OPEN_VSX_EXTENSIONS_FILE = 'open_vsx_extensions.json'
MS_OWNED_NAMESPACES = ['ms-python',
                       'ms-toolsai',
                       'ms-vscode',
                       'ms-azuretools',
                       'dbaeumer',
                       'MS-CEINTL',
                       'vscjava',
                       'GitHub',
                       'ms-kubernetes-tools',
                       'ms-edgedevtools',
                       'ms-playwright',
                       'MS-SarifVSCode',
                       'msjsdiag'
                       ]


def get_vscode_installs(extension_data):
    """Helper to extract install count from the specific VS Code stats structure."""
    stats = extension_data.get('statistics', [])
    for stat in stats:
        if stat.get('statisticName') == 'install':
            return stat.get('value', 0)
    return 0


def load_json_file(filepath):
    """Safely loads local JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def fetch_auto_publish_set():
    """
    Fetches the remote JSON list from GitHub.
    Structure is a list of strings: ["$schema", "pub.ext1", "pub.ext2"...]
    Returns a set of lowercase IDs for O(1) lookup.
    """
    print(f"Fetching auto-publish list from GitHub...")
    try:
        response = requests.get(AUTO_PUBLISH_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        id_set = set()
        for item in data:
            # ensure item is a string and ignore the schema definition
            if isinstance(item, str) and item != "$schema":
                id_set.add(item.lower())

        return id_set
    except Exception as e:
        print(f"Warning: Could not fetch auto-publish list ({e}). Column will be False.")
        return set()


def main():
    # 1. Load Data Sources
    vscode_extensions = load_json_file(VS_CODE_EXTENSIONS_FILE)
    if not vscode_extensions:
        print(f"No VS Code data found: {VS_CODE_EXTENSIONS_FILE}. Exiting.")
        return
    openvsx_extensions = load_json_file(OPEN_VSX_EXTENSIONS_FILE)
    if not openvsx_extensions:
        print(f"No Open VSX data found: {OPEN_VSX_EXTENSIONS_FILE}. Exiting.")
        return
    vscode_licenses = load_json_file(VS_CODE_LICENSES_FILE)
    if not vscode_licenses:
        print(f"No VS Code licenses data found: {VS_CODE_LICENSES_FILE}. Exiting.")
        return
    auto_publish_ids = fetch_auto_publish_set()
    if len(auto_publish_ids) == 0:
        print("Auto-publish list is empty. Exiting.")

    # 2. Process VS Code Data
    print("Processing VS Code extensions...")
    vs_rows = []
    for ext in vscode_extensions:
        pub = ext['publisher']['publisherName']
        name = ext['extensionName']
        vscode_id = f"{pub}.{name}"
        last_Updated_str = ext['lastUpdated']
        last_Updated = datetime.fromisoformat(last_Updated_str)
        version = ext['versions'][0]['version']
        license_info = vscode_licenses.get(vscode_id)
        if license_info is not None:
            license = license_info.get('license')
        else:
            license = None
        vs_rows.append({
            'VS Code Publisher': pub,
            'VS Code Name': name,
            'VS Code Version': version,
            'VS Code Last-Updated': last_Updated,
            'VS Code License': license,
            'VS Code Installs': get_vscode_installs(ext),
            # Normalized key for joining
            'join_key': vscode_id.lower()
        })

    # 3. Process Open VSX Data
    print("Processing Open VSX extensions...")
    ovsx_rows = []
    for ext in openvsx_extensions:
        namespace = ext.get('namespace', '')
        name = ext.get('name', '')
        # Extract the specific publisher login name (e.g. "PolyMeilex" user vs "PolyMeilex" namespace)
        publisher = ext.get('publishedBy', {}).get('loginName', 'Unknown')
        ovsx_date_str = ext.get('timestamp')
        ovsx_date = datetime.fromisoformat(ovsx_date_str)
        ovsx_version = ext.get('version')

        if namespace and name:
            ovsx_rows.append({
                'Open VSX Namespace': namespace,
                'Open VSX Name': name,
                'Open VSX Publisher': publisher,
                'Open VSX Version': ovsx_version,
                'Open VSX Last-Updated': ovsx_date,
                'Open VSX Downloads': ext.get('downloadCount', 0),
                'Open VSX Verified': ext.get('verified'),
                'Open VSX License': ext.get('license'),
                # Normalized key for joining uses Namespace (where the extension lives)
                'join_key': f"{namespace}.{name}".lower()
            })

    # 4. Create DataFrames
    df_vs = pd.DataFrame(vs_rows)
    df_ovsx = pd.DataFrame(ovsx_rows)

    # 5. Merge DataFrames
    # Inner join finds the intersection of both registries
    merged_df = pd.merge(df_vs, df_ovsx, on='join_key', how='outer')

    ovsx_only = df_ovsx[~df_ovsx['join_key'].isin(df_vs['join_key'])]

    merged_df['Open VSX Auto-Publish'] = merged_df['join_key'].isin(auto_publish_ids)
    merged_df['Publish Lag'] = merged_df['VS Code Last-Updated'] - merged_df['Open VSX Last-Updated']
    merged_df['Publish Lag (Days)'] = merged_df['Publish Lag'].dt.days
    merged_df['Publish Lag (Days)'] = merged_df['Publish Lag (Days)'].clip(lower=0)
    merged_df['VS Code Last-Updated'] = merged_df['VS Code Last-Updated'].dt.strftime("%Y-%m-%d")
    merged_df['Open VSX Last-Updated'] = merged_df['Open VSX Last-Updated'].dt.strftime("%Y-%m-%d")
    merged_df['MS Owned Namespace'] = merged_df['Open VSX Namespace'].isin(MS_OWNED_NAMESPACES)

    # 7. Final Formatting
    final_cols = [
        'VS Code Publisher',
        'VS Code Name',
        'VS Code Installs',
        'VS Code Version',
        'VS Code Last-Updated',
        'Open VSX Namespace',
        'Open VSX Name',
        'MS Owned Namespace',
        'Open VSX Publisher',
        'Open VSX Version',
        'Open VSX Last-Updated',
        'Open VSX Downloads',
        'Open VSX Auto-Publish',
        'Publish Lag (Days)',
        'Open VSX Verified',
        'Open VSX License',
        'VS Code License'
    ]

    result_df = merged_df[final_cols]

    # Sort by VS Code Installs (Descending)
    result_df = result_df.sort_values(by=['VS Code Installs', 'Open VSX Downloads'], ascending=False)

    # Reset index for clean display
    result_df = result_df.reset_index(drop=True)

    # 8. Output
    print("-" * 30)
    print(f"Total matching extensions: {len(result_df)}")
    print(f"Auto-published extensions found: {result_df['Open VSX Auto-Publish'].sum()}")
    print("-" * 30)

    # Print top 10 rows
    print(result_df.head(10).to_string())

    # Optional: Save to CSV
    result_df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()