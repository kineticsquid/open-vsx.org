# Open VSX Reports
Reports and supporting scripts for graphing availability and activity at open-vsx.org and collecting metadata of all extensions on Open VSX and the VS Code Marketplace. Some scripts and Jupyter notebooks require different kinds of access tokens.

## Jupyter Notebooks

Many of these notebooks require access tokens or secrets of some form. They should be defined in an `.env` file in the same folder in this form.
```
OPEN_VSX_ACCESS_TOKEN='****************'
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
