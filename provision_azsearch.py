"""Configure an azure search instance

-------------------------------------
How to use
-------------------------------------

python provision_azsearch.py -k <AZURE_SEARCH_ADMIN_KEY> -u <AZURE_SEARCH_URL> -c <SAVED_AZURE_search_resource> -d <DATA_SOURCE_CONFIG> [-b <skip|update|delete>]

"""

import os
import sys
import json
import requests
import getopt

def usage():
    print 'Usage: %s -k <AZURE_SEARCH_ADMIN_KEY> -u <AZURE_SEARCH_URL -c <SAVED_AZURE_search_resource> -d <DATA_SOURCE_CONFIG> [-b <skip|update|delete>] [-p]' % os.path.basename(sys.argv[0])
    print ''
    print '  -k, --key \n    Specifies the admin key for the azure search instance'
    print '  -u, --url \n    Specifies the url for the azre search instance'
    print '  -c, --savedconfig \n    Specifies the json file containig a saved Azure Search config'
    print '  -d, --datasourcecofnig \n    Specifies the json file containing data source configuration (i.e. connection string values)',
    print '  -a, --apiversion \n    Specifies the api version to use for azure search requests'
    print '  -b, --behavior \n    Specifies the behavior when encountering existing resources'
    print "        'skip' -- Skip the resource (leave it as is)"
    print "        'update' -- Attempt to update the resource in place (PUT)"
    print "        'delete' -- Delete the resource first then create it as specified"
    print '  -p, --purge \n    Delete all indexes, datasources and indexers in the instance before configuring'



def get_search_resource(url, admin_key, apiversion, resource):
    params = {'api-version': apiversion}
    headers = { 'api-key': admin_key }
    response = requests.get(url + '/' + resource, headers=headers, params=params)
    response.raise_for_status()
    result = response.json()['value']
    response.close()
    return result

def delete_search_resource(url, admin_key, apiversion, resource):
    return requestsaction_search_resource(requests.delete, url, admin_key, apiversion, resource, None)

def post_search_resource(url, admin_key, apiversion, resource, data):
    return requestsaction_search_resource(requests.post, url, admin_key, apiversion, resource, data)

def put_search_resource(url, admin_key, apiversion, resource, data):
    return requestsaction_search_resource(requests.put, url, admin_key, apiversion, resource, data)

def requestsaction_search_resource(requests_action, url, admin_key, apiversion, resource, data):
    params = {'api-version': apiversion}
    headers = { 'api-key': admin_key, "content-type": "application/json"}
    response = requests_action(url + "/" + resource, headers=headers, params=params, data=json.dumps(data))
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError,e:
        print "\n\nERROR\n\n"
        print "URL: " + response.url
        print "STATUS_CODE: " + str(response.status_code)
        print "REASON: " + response.reason
        print "TEXT: " + response.text
        raise e
    finally:
        response.close()

def main():
    INDEXES = "indexes"
    INDEXERS = "indexers"
    DATASOURCES = "datasources"
    ALL_CONFIG_TYPES = [INDEXES, DATASOURCES, INDEXERS]

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hk:u:c:d:a:b:p", ["help", "key=", "url=", "savedconfig=", "datasourceconfig=", "apiversion=", "behavior=", "purge"])

    except getopt.GetoptError:
        usage()
        sys.exit(2)


    key = ""
    url = ""
    apiversion = "2015-02-28"
    savedconfigfilename = ""
    datasourceconfigfilename = "datasourceconfigfilename"
    behavior = "skip"
    purge = False

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

        elif o in ("-k", "--key"):
            key = a

        elif o in ("-u", "--url"):
            url = a

        elif o in ("-c", "--savedconfig"):
            savedconfigfilename = a

        elif o in ("-d", "--datasourceconfig"):
            datasourceconfigfilename = a

        elif o in("-a", "--apiversion"):
            apiversion = a

        elif o in ("-b", "--behavior"):
            behavior = a

        elif o in ("-p", "--purge"):
            purge = True


    if url == "" or key == "" or savedconfigfilename == "" or datasourceconfigfilename == "":
        usage()
        sys.exit(2)

    if behavior not in ['skip', 'delete', 'update']:
        usage()
        sys.exit(2)

    print 'Key = %s, URL = %s, Saved config file = %s, Data config file = %s' % (key, url, savedconfigfilename, datasourceconfigfilename)

    existingconfigByType = {}
    for configtype in ALL_CONFIG_TYPES:
        existingconfigByType[configtype] = get_search_resource(url, key, apiversion, configtype)

    savedconfigfile = open(savedconfigfilename, 'r')
    savedconfig = json.loads(savedconfigfile.read())
    savedconfigfile.close()

    dsconfigfile = open(datasourceconfigfilename, 'r')
    dsconfig = json.loads(dsconfigfile.read())
    dsconfigfile.close()

    if purge:
        _ = raw_input("WARNING: About to delete all the configs for the Azure Search instance. ... Enter Ctrl+C to abort!")
        for configtype in ALL_CONFIG_TYPES:
            for existingconfig in existingconfigByType[configtype]:
                resource = "%s/%s" % (configtype, existingconfig['name'])
                sys.stdout.write("DELETING %s ... " % resource)
                delete_search_resource(url, key, apiversion, resource )
                print "OK"

    print "Inserting any matching datasource connection strings."
    for datasource in savedconfig[DATASOURCES]:
        for ds in dsconfig:
            if datasource['type'] == ds['type']:
                if datasource['name'] in ds['sources']:
                    print 'Updating datasource %s connectionString' % (datasource['name'])
                    datasource['credentials']['connectionString'] = ds['connectionString']
    print "\n"


    for configtype in  ALL_CONFIG_TYPES:
        print "Provisioning %s" % configtype
        existingconfignames = [exconfig['name'] for exconfig in existingconfigByType[configtype]]
        for config in savedconfig[configtype]:
            configname = config['name']
            resource = "%s/%s" % (configtype, configname)

            if configname in existingconfignames:
                if behavior == 'skip':
                    print "%s already exists, skipping." % resource
                    continue
                elif behavior == 'update':
                    sys.stdout.write("UPDATING %s ... " % resource)
                    put_search_resource(url, key, apiversion, resource, config)
                    print "OK"
                    continue
                elif behavior == 'delete':
                    sys.stdout.write("DELETING %s ... " % resource)
                    delete_search_resource(url, key, apiversion, resource)
                    print "OK"
            sys.stdout.write("CREATING %s ... " % resource)
            post_search_resource(url, key, apiversion, configtype, config)
            print "OK"
        print "\n\n"

    sys.exit()

if __name__ == "__main__":
    main()
