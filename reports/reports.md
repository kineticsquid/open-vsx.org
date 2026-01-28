# Open VSX Reports
Reports and supporting scripts for graphing availability and activity at open-vsx.org and collecting metadata of all extensions on Open VSX and the VS Code Marketplace. Some scripts and Jupyter notebooks require different kinds of access tokens.

## Jupyter Notebooks

Many of these notebooks require access tokens or secrets of some form. They should be defined in an `.env` file in the same folder in this form.
```
OPEN_VSX_ACCESS_TOKEN='****************'
GITHUB_ACCESS_TOKEN='****************'
REDIS_HOST='redis-**************.cloud.redislabs.com'
REDIS_PORT=*****
REDIS_PW='****************'
GMAIL_ID='fred@flintstones.com'
GMAIL_PW='****************'
TARGET_EMAIL='wilma@flintstones.com'
BETTER_STACK_TOKEN='****************'
```

### `graph_availability_trends.ipynb`
Graphs site availability based on data from Better Stack, née Better Uptime. Requires an access key from the IT Team.

### `graph_most_active.ipynb`
Uses admin reports from open-vsx.org/admin/report API to graph activity by month. Requires an Open VSX access token with admin level authority.
- Users publishing the most extensions
- Namespaces with the most extensions
- Namespaces with the most extension versions
- Most downloaded extensions

### `graph_trends.ipynb`
Graphs total downloads, extensions and publishers by month. Requires an access token with admin level authority.

## Python Scripts

### `get_availability_data.py`
Script to collect availability data from open-vsx endpoints monitored by Better Stack. Used by a `graph_availability_trends.ipynb` to graph availability. Requires a Better Stack access token. 

### `get_open_vsx_admin_reports.py`
Script to collect activity data from Open VSX admin reports. Used by `graph_most_active.ipynb` and `graph_trends.ipynb`. Requires an Open VSC access token with admin level authority.

### `aggregate_all_extension_metadata.py`
Script that takes as input metadata for all Open VSX extensions, `open_vsx_extensions.json`, metadata for all VS Code Marketplace extensions, `vs_code_extensions.json` and license information for the VS Code Marketplace extensions, `vs_code_licenses.json`, and does a join on namespace/publisher.extension to produce a large spreadsheet with the collected metadata of extensions across both marketplaces. It outputs `all_extensions_metadata.csv`. Run `get_all_open_vsx_extensions.py` to produce the `open_vsx_extensions.json` file. Run `get_all_vs_marketplace_extensions.py` to produce the `vs_code_extensions.json` file. Run `get_vs_license_info.py` to produce the `vs_code_licenses.json` file. Then run this script. The logic is separated into the separate scripts because the processing can take some time. There are occasional sleep() statements to help prevent 429 errors. 

### `get_all_open_vsx_extensions.py`
Script to collect metadata on all Open VSX extensions. Outputs meta is two formats, `open_vsx_extensions.json` and `open_vsx_extensions.tsv`. Script output is input to `aggregate_all_extension_metadata.py`.

### `get_all_vs_marketplace_extensions.py`
Script to collect metadata on all VS Code Marketplace extensions. Outputs meta is two formats, `vs_code_extensions.json` and `vs_code_extensions.tsv`. Script output is input to `aggregate_all_extension_metadata.py`.

### `get_vs_license_info.py`
Script to collect license information for VS Code Marketplace extensions. This is a separate script because the VS Code metadata doesn't include license information. That information has to be retrieved from an associated license file asset. Input is `vs_code_extensions.json` file. Output is `vs_code_licenses.json`. Script output is input to `aggregate_all_extension_metadata.py`.

