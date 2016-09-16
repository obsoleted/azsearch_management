# Azure Search Management Tools
Scripts to assist with the management of Azure Search service configuration.
Potential uses:
- Providing the basis for source controlled search service configuration
- Assisting with the migration to a new Azure Search pricing tier

The scripts are written assuming an Azure Search resource has already been created. Automation of Azure Search resource creation is not handled here. But can be done in various ways, [ARM](https://azure.microsoft.com/en-us/documentation/articles/resource-group-overview/) template deployment for example.


## Azure Search Concepts
For a more detailed explanation of Azure Search please see the current documentation [here](https://azure.microsoft.com/en-us/documentation/articles/search-what-is-azure-search/)
- Indexes - Store of documents that are searchable
- Data Sources - Originators of data that can be pulled from to populate indexes. (e.g. an Azure SQL Table or DocumentDB Collection)
- Indexers - Essentially the data pull definition linking a data source to an index.
- Keys - Access keys that can be used to manage or query the service (**This this script does not currently save or recreate the same key configuration**)

# Usage

## Saving/Snapshotting

1. Create an Azure Search resource ([link](https://azure.microsoft.com/en-us/documentation/articles/search-create-service-portal/))
1. Configure the resource by [creating indexes](https://azure.microsoft.com/en-us/documentation/articles/search-what-is-an-index/) and [adding data](https://azure.microsoft.com/en-us/documentation/articles/search-what-is-data-import/)
   - *Note:* These scripts only save/provision configuration related to data pulling (i.e. data sources and indexes)
1. Note an admin key and the url of the search resource
1. Run the [save_azsearch.py](./save_azsearch.py) script supplying the key and url. Optionally specify an output file or the configuration will be printed to the console
   ```sh
   python save_azsearch.py -k F6D1EEEEAC2A4D00DB1A5DB8C2DF09BC -u https://azsearchmanagement.search.windows.net -o azsearchmgmnt.json
   ```

   - The output of a successful run of this script will be the json configuration of the search resource. It will contain the indexes, data sources and indexers currently configured. But it will **not** contain the connectionstring/secrets associated with the data sources.
1. If you have datasources create a json file containing the configuration for each (see below for more on the format of this information)

### Data Source Configuration File

The data source configuration file is expected to be a json file containing an array of objects with the following properties;
- type - the type of datasource being described (e.g. 'azuresql' or 'documentdb')
- sources - Array of strings each of which is the name of a data source that uses this connection information (e.g. 'datasource1')
- connectionString - The connection string to be by the search service when pulling data from the source. This string will specify the credentials needed when accessing the data source such as username and password for SQL or key for DocumentDB.
```json
[
    {
        "type": "azuresql",
        "sources": ["datasource1"],
        "connectionString": "Server=tcp:{AZURE_SQL_DB_SERVER_NAME}.database.windows.net,1433;Initial Catalog={AZURE_SQL_DB_NAME};Persist Security Info=False;User ID={SQL_USERNAME};Password={SQL_USER_PASSWORD};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
    },
    {
        "type": "documentdb",
        "sources": ["datasource2"],
        "connectionString": "AccountEndpoint=https://{AZURE_DOCDB_NAME}.documents.azure.com:443/;AccountKey={AZURE_DOCDB_ACCESS_KEY};Database={AZURE_DOCDB_DB_NAME};"
    }
]
```

## Applying Configuration

**Requirements:** The saved resource and data source configuration files created in the above process.

1. Get the admin key and url for the Azure Search instance you want to configure
1. Run the [provision_azsearch.py](./provision_azsearch.py) script supplying the key, url, resource configuration file, the data source configuration file and the behavior mode you want for the script.

  - The behavior mode applies to how the script deals with indexes, data sources, and indexers that already exist in the search instance.

    | Mode | Description |
    | ---- | ----------- |
    | *skip*  | the script will *skip* applying any configuration to it. |
    | *update* | the script will attempt to *update* the configuration item (may cause failures depending on type of update and item type) |
    | *delete* | the script will first delete the item then create a new one matching the specified configuration |

  - example:

  ```sh
  python provision_azsearch.py -k F6D1EEEEAC2A4D00DB1A5DB8C2DF09BC - https://azsearchmanagement.search.windows.net -c azsearchmgmnt.json -d azsearchmgmnt_datasources.json -b skip
  ```

### Purge Option

The provision script can also be run with the `-p` flag. This runs the script in "purge" mode where it will first delete all the indexes, data sources and indexers in the search instance. This option is useful for removing items that were created manually but you do not want saved.



# Implementation

The scripts are relatively simple and make requests against the Azure Search Service REST endpoint described [here](https://msdn.microsoft.com/library/dn798935.aspx).

## Errors

For the most part there is no error handling in the scripts. If the service returns an error, it is simply printed to the console and the script exits. I've found the information contained in the errors to be good enough to not want to invest more here.
