"""
Script to collect metadata on all published extensions. Requires an access token 
from https://open-vsx.org/user-settings/tokens. Used by Jupyter notebooks.
"""
import requests
import os
import json
import time
from datetime import datetime

API_ENDPOINT = "https://open-vsx.org/"

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
JSON_FILENAME = 'extensions.json'
TSV_FILENAME = 'extensions.tsv'

url = API_ENDPOINT + 'api/-/search?size=100&token=%s' % ACCESS_TOKEN

def get_all_extensions():
    extensions = []
    done = False
    offset = 0
    while not done:
        search_url = url + '&offset=%s' % offset
        try:
            response = requests.get(search_url)
            results = response.json()
            extensions = extensions + results['extensions']
            offset = len(extensions) 
            print('Retrieved %s extensions' % len(extensions))
            if len(extensions) == results['totalSize']:
                done = True
        except Exception as e:
            print("%s: %s" % (datetime.now(), e))
            done = True
    
    count = 1
    all_extensions = []
    print("\n\nStarting: %s" % datetime.now())
    for extension in extensions:
        namespace_url = API_ENDPOINT + 'api/%s/%s?token=%s' % (extension['namespace'], extension['name'], ACCESS_TOKEN)
        retry_count = 5
        while retry_count > 0:
            try:
                response = requests.get(namespace_url)
                if response.status_code == 200:
                    break
                else:
                    raise Exception('%s: HTTP %s Error retrieving %s' % (datetime.now(), response.status_code,extension['url']))
            except Exception as e:
                print("%s: %s" % (datetime.now(), e))
                retry_count -= 1
                time.sleep(2)
        if retry_count == 0:
            print('Error retrieving %s' % extension['url'])
        else:
            results = response.json()
            all_extensions.append(results)
        if int(count/100) == count/100:
            print('Processed %s of %s.' % (count, len(extensions)))
        count += 1
    print("\n\nFinished %s API Calls: %s" % (count, datetime.now()))

    return(all_extensions)

def get_all_by_license():
    extensions_by_license = {}
    all_extensions = get_all_extensions()
    count = 1
    for extension in all_extensions:
        license = extension.get('license', 'None')
        if license in extensions_by_license:
            extensions_by_license[license].append(extension)
        else:
            extensions_by_license[license] = [extension]
        if int(count/100) == count/100:
            print('Processed %s of %s.' % (count, len(all_extensions)))
        count += 1

    return(dict(sorted(extensions_by_license.items())))

def write_json_file(extensions):
    f = open(JSON_FILENAME, 'w')
    f.write(json.dumps(extensions, indent=4))
    f.close()
    return

def write_tsv_file(extensions):
    f = open(TSV_FILENAME, 'w')
    columns = "Name\tNamespace\tVersions\tLogin Name\t"
    columns = columns + "Full Name\tLicense\tTimestamp\tDownloads\tReviews\tFiles\t"
    columns = columns + "PreRelease\tVerified\tUnrelated Publisher\tNamespace Access\tPreview\t"
    columns = columns + "Homepage\tRepo\tBugs\tBundled Extensions\n"
    f.write(columns)
    for e in extensions:
        row = "%s\t%s\t%s\t%s" % (e['name'], e['namespace'], len(e['allVersions']), e['publishedBy']['loginName'])
        row = "%s\t%s\t%s\t%s\t%s\t%s\t%s" % (row, e['publishedBy'].get('fullName', 'None'), e.get('license', 'None'), e['timestamp'], e['downloadCount'], e['reviewCount'], len(e['files']))
        row = "%s\t%s\t%s\t%s\t%s\t%s" % (row, e['preRelease'], e['verified'], e['unrelatedPublisher'], e['namespaceAccess'], e['preview'])
        row = "%s\t%s\t%s\t%s\t%s\n" % (row, e.get('homepage', 'None'), e.get('repository', 'None'), e.get('bugs', 'None'), len(e['dependencies']))
        f.write(row)
    f.close()

if __name__ == '__main__':
    extensions = get_all_extensions()
    write_json_file(extensions)
    write_tsv_file(extensions)


    


