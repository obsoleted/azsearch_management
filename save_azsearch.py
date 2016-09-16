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
    print 'Usage: %s -k <AZURE_SEARCH_ADMIN_KEY> -u <AZURE_SEARCH_URL> [-o <SEARCH_CONFIG_OUTPUTFILE>] [-d <DATA_SOURCE_CONNECTION_CONFIG_FILE> ] [-a <API_VERSION>]' % os.path.basename(sys.argv[0])

if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hk:u:o:d:a:",["help","key=","url=","output=","datasourceconfig=","apiversion="])

    except getopt.GetoptError:
        usage()
        sys.exit(2)


    key = ""
    url = ""
    apiversion = "2015-02-28"
    config_output_filename = ""
    datasource_config_filename = ""

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

        elif o in ("-k", "--key"):
            key = a

        elif o in ("-u", "--url"):
            url = a

        elif o in ("-o", "--output"):
            config_output_filename = a

        elif o in ("-d", "--datsourceconfig"):
            datasource_config_filename = a

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

    if datasource_config_filename != "":
        # Data source connection configuration file specified so see if it exists
        if os.path.exists(datasource_config_filename):
            datasource_config_file = open(datasource_config_filename, 'r')
            existing_datasource_conn_configs = json.loads(datasource_config_file.read())
            datasource_config_file.close()
            print 'Checking existing data source connection config file against current datasources from the service-'
            print '  Checking for data sources missing from the file...'
            for dsin in search_configuration['datasources']:
                dsin_found = False
                for dsexisting in existing_datasource_conn_configs:
                    if dsexisting['type'] == dsin['type']:
                        if dsin['name'] in dsexisting['sources']:
                            dsin_found = True
                if not dsin_found:
                    print '    Data source %s with type %s was not found in the datasource connection config file %s' % (dsin['name'], dsin['type'], datasource_config_filename)

            print '  Checking for data sources that can be removed from the file (ones that are not on the service)...'
            for dsexisting in existing_datasource_conn_configs:
                for source in dsexisting['sources']:
                    dsexisting_found = False
                    for dsin in search_configuration['datasources']:
                        if dsin['type'] == dsexisting['type']:
                            if dsin['name'] == source:
                                dsexisting_found = True
                    if not dsexisting_found:
                        print '    Data source %s with type %s was present in the config file %s but not present on the service instance.' % (source, dsexisting['type'], datasource_config_filename)

        else:
            datasource_conn_configs = []
            for ds in search_configuration['datasources']:
                datasource_conn_configs.append({
                    'type': ds['type'],
                    'sources': [ds['name']],
                    'connectionString': '<REPLACE_WITH_CONNECTION_STRING>'
                })

            datasource_config_file = open(datasource_config_filename, 'w')
            datasource_config_file.write(json.dumps(datasource_conn_configs, indent=2))
            datasource_config_file.close()

            print 'Data souce connection configuratino file (%s) created. Please update with connection strings.' % (datasource_config_filename)
            # The data source connection config file didn't exist so we can create an empty one maybe


    configurationjson = json.dumps(search_configuration, indent=2)
    if config_output_filename == "":
        print configurationjson
    else:
        searchconfigoutputfile = open(config_output_filename, 'w')
        searchconfigoutputfile.write(configurationjson)
        searchconfigoutputfile.close()
