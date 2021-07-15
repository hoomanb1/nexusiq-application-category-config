# Nexus IQ Application Category Management
Application categories within the IQ Server can be managed via the UI however, at scale this might be a little challenging to manage hundreds or thousands of applications on boarded to the IQ Server.

This little script allows the application categories to be managed via config as a code.

## Dependencies
The script only requires [requests](https://docs.python-requests.org/en/master/) package and can be installed via below command:

```
 pip3 install requests
```

 ## Configuration
 The script contains a configuration file to allow application categories to be defined and configured via this file. The structure of the configuration file contains 3 json objects:

```
{
  "applications": {},
  "organisations": [],
  "nexus-IQ": {}
}
```
The `applications` object contains an element called `apply: true / false` to allow this particular config to be turned on or off.

The `action: assign / delete` element defines what actions need to executed against the application categories. For example, application categories tags might need to be deleted from applications or assigned to applications.

The `application_categories` element contains all the application categories that needs to be actioned on.

```
"applications": {
    "apply": true,
    "action": "assign",
    "application_categories": [
      {
        "name": "test-10",
        "description": "some tests"
      },
      {
        "name": "test-11",
        "description": "some tests 02"
      }
    ]
  }
```

*Note:* The application config section takes action on all applications on boarded into the IQ Server. This can be turned on and off via the `apply` switch, in which case the entire config section will be skipped during the execution of the script.

The `organisations` element of the main config section contains an array objects of sub-organisations within the IQ Server and the application categories that need to be applied to applications under these organisations.

```
"organisations": [
   {
     "name": "Sandbox-01",
     "action": "assign",
     "application_categories": [
       {
         "name": "test-01",
         "description": "some tests"
       },
       {
         "name": "test-02",
         "description": "some tests 02"
       }
     ]
   },
   {
     "name": "Sandbox-02",
     "action": "assign",
     "application_categories": [
       {
         "name": "test-03",
         "description": "some tests"
       },
       {
         "name": "test-04",
         "description": "some tests 02"
       }
     ]
   }
 ]
```

Again the `action: assign / delete` element within this config block indicates what action needs to be applied to each applications of organisations.

The `nexus-IQ` element of the main config section contains Nexus IQ configuration.

```
"nexus-IQ": {
  "url": "http://localhost:8070",
  "username": "admin",
  "password": "admin"
}
```
*Note*: `username` and `password` section of the above config section can be replaced by the [Nexus IQ user token](https://help.sonatype.com/iqserver/managing/user-management/user-tokens).

## Executing the script

The script can be executed via the below command:

```
python3 assignappcategory.py
```
*Note:* Please be sure the `app_category_conf.json` is stored in the same directory of the script.  
