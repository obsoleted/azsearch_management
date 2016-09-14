"""Save the configuration (indexes, indexers, datasources) of an azure search instance

-------------------------------------
How to use
-------------------------------------

python save_azsearch.py -k <AZURE_SEARCH_ADMIN_KEY> -u <AZURE_SEARCH_URL> [-o <SEARCH_CONFIG_OUTPUTFILE>] [-a <API_VERSION>]

Will result in the indexes, indexers and datasources being retrived from the
specified azure instance and either printed out to standard out or saved to
specified configuration file (-o option). The output format will be json in
the following format:

    {
        "indexers": [ ... ],
        "indexes": [ ... ],
        "datasources": [ ... ]
    }

"""

import os
import sys
import json
import requests
import getopt


def usage():
    print 'Usage: %s -k <AZURE_SEARCH_ADMIN_KEY> -u <AZURE_SEARCH_URL> [-o <SEARCH_CONFIG_OUTPUTFILE>] [-a <API_VERSION>]' % os.path.basename(sys.argv[0])

if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hk:u:o:a:",["help","key=","url=","output=","apiversion="])

    except getopt.GetoptError:
        usage()
        sys.exit(2)


    key = ""
    url = ""
    apiversion = "2015-02-28"
    configoutputfilename = ""

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

        elif o in ("-k", "--key"):
            key = a

        elif o in ("-u", "--url"):
            url = a

        elif o in ("-o", "--output"):
            configoutputfilename = a

        elif o in ("-a", "--apiversion"):
            apiversion = a


    if url == "" or key == "":
        usage()
        sys.exit(2)


    print 'Key = %s, URL = %s' % (key, url)

    search_configuration = {}

    payload = { 'api-version': apiversion}
    headers = { "api-key": key }

    for configtype in ['indexes', 'indexers', 'datasources']:
        response = requests.get(url + '/' + configtype, params=payload, headers=headers)
        response.raise_for_status()
        search_configuration[configtype] = response.json()['value']
        response.close()

    configurationjson = json.dumps(search_configuration, indent=2)
    if configoutputfilename == "":
        print configurationjson
    else:
        searchconfigoutputfile = open(configoutputfilename, 'w')
        searchconfigoutputfile.write(configurationjson)
        searchconfigoutputfile.close()
