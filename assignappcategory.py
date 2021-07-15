import requests
from requests.auth import HTTPBasicAuth
import json
import random


def main():
    app_category_colors = ['light-red', 'light-green', 'light-blue', 'light-purple', 'dark-red',
                           'dark-green', 'dark-blue', 'dark-purple', 'orange', 'yellow']

    conf = open('app_category_conf.json')
    conf_data = json.load(conf)

    if conf_data.get('applications').get('apply') and conf_data.get('applications').get('action') == "assign":
        organisations = retrieve_organisations(conf_data)
        assign_tags_to_all(app_category_colors, conf_data, organisations, 'ROOT_ORGANIZATION_ID')

    if conf_data.get('applications').get('apply') and conf_data.get('applications').get('action') == "delete":
        delete_tags_from_all(conf_data, get_all_apps(conf_data))

    #
    if not conf_data.get('applications').get('apply'):
        organisations = retrieve_organisations(conf_data)

        orgs_in_scope = dict()
        for item in organisations.json().get('organizations'):
            for o in conf_data.get('organisations'):
                if item.get('name') == o.get('name'):
                    orgs_in_scope[item.get('id') + ':' + o.get('action')] = o.get('application_categories')

        for k, v in orgs_in_scope.items():
            key = k.split(':')
            if key[1] == 'delete':
                org_apps = find_apps_by_org(get_all_apps(conf_data), key[0])
                delete_tags_from_all(conf_data, org_apps)
            elif key[1] == 'assign':
                added_tag_ids = list()
                for it in v:
                    it['color'] = random.choice(app_category_colors)
                    r = create_app_category(conf_data, key[0], it)
                    if 'An application category with the same name already exists for organization' in r.text:
                        for otl in find_root_organisation_tag_list(organisations):
                            if otl.get('name') == it.get('name'):
                                it['rootTagId'] = otl.get('id')

                    if 'is already used as a name' in r.text:
                        print(it.get('name') + " is already used as name skipping...")
                        added_tag_ids.append({"tagId": find_tag_id_in_org(organisations, key[0], it.get('name'))})

                    if r.status_code == 200:
                        added_tag_ids.append({"tagId": r.json().get('id')})

                for mval in v:
                    if 'rootTagId' in mval:
                        added_tag_ids.append({"tagId": mval.get('rootTagId')})
                all_apps = find_apps_by_org(get_all_apps(conf_data), key[0])
                assign_tag_to_apps(added_tag_ids, all_apps, conf_data)
            else:
                print('action can only be assign or delete')
                exit()


def retrieve_organisations(conf_data):
    organisations = requests.get(sanitise_url(conf_data.get('nexus-IQ').get('url')) + 'api/v2/organizations',
                                 auth=HTTPBasicAuth(conf_data.get('nexus-IQ').get('username'),
                                                    conf_data.get('nexus-IQ').get('password')), verify=False)
    return organisations


def delete_tags_from_all(conf_data, apps):
    for application in apps:
        payload = {"id": application.get('id'), "publicId": application.get('publicId'),
                   "name": application.get('name'), "organizationId": application.get('organizationId'),
                   "applicationTags": []}
        headers = {"Content-Type": "application/json"}

        deleted = requests.put(
            sanitise_url(conf_data.get('nexus-IQ').get('url')) + 'api/v2/applications/' + application.get('id'),
            auth=HTTPBasicAuth(conf_data.get('nexus-IQ').get('username'),
                               conf_data.get('nexus-IQ').get('password')),
            json=payload, headers=headers, verify=False)

        if deleted.status_code == 200:
            print("Successfully deleted category to " + application.get('name') + " application")


def find_root_organisation_tag_list(organisations):
    for item in organisations.json().get('organizations'):
        if item.get('id') == 'ROOT_ORGANIZATION_ID':
            return item.get('tags')


def find_tag_id_in_org(organisations, org_id, tag_name):
    for item in organisations.json().get('organizations'):
        if item.get('id') == org_id:
            if len(item.get('tags')):
                for i in item.get('tags'):
                    if i.get('name') == tag_name:
                        return i.get('id')
    return None


def assign_tags_to_all(app_category_colors, conf_data, organisations, organisation_id):
    root_org_tag_list_name = list()
    conf_tag_list = list()
    root_org_full_tag_list = list()
    for item in organisations.json().get('organizations'):
        if item.get('id') == 'ROOT_ORGANIZATION_ID':
            root_org_full_tag_list = item.get('tags')
            for tl in item.get('tags'):
                root_org_tag_list_name.append(tl.get('name'))
            for ctl in conf_data.get('applications').get('application_categories'):
                conf_tag_list.append(ctl.get('name'))

    added_tag_ids = list()
    # existing_tag_ids = list()
    for config_tag in conf_tag_list:
        if config_tag not in root_org_tag_list_name:
            for t in conf_data.get('applications').get('application_categories'):
                if config_tag == t.get('name'):
                    t['color'] = random.choice(app_category_colors)
                    print(config_tag + " doesn't exist creating it now...")
                    result = create_app_category(conf_data, organisation_id, t)

                    if result.status_code == 200:
                        added_tag_ids.append({"tagId": result.json().get('id')})

                    if result.status_code == 400 and 'An application category with the same name' \
                                                     ' already exists for' in result.text:
                        print(result.text + ' ' + ' category tag -> ' + t.get('name') +
                              ' . Please choose a different category name')
                        exit()

        else:
            for it in root_org_full_tag_list:
                if it.get('name') == config_tag:
                    added_tag_ids.append({"tagId": it.get('id')})
                    # existing_tag_ids.append({"tagId": it.get('id')})

    apps = get_all_apps(conf_data)
    assign_tag_to_apps(added_tag_ids, apps, conf_data)
    # assign_tag_to_apps(bool(added_tag_ids) and added_tag_ids or existing_tag_ids, apps, conf_data)


def assign_tag_to_apps(added_tag_ids, apps, conf_data):
    for application in apps:
        payload = {"id": application.get('id'), "publicId": application.get('publicId'),
                   "name": application.get('name'), "organizationId": application.get('organizationId'),
                   "applicationTags": added_tag_ids}
        headers = {"Content-Type": "application/json"}

        assigned = requests.put(
            sanitise_url(conf_data.get('nexus-IQ').get('url')) + 'api/v2/applications/' + application.get('id'),
            auth=HTTPBasicAuth(conf_data.get('nexus-IQ').get('username'),
                               conf_data.get('nexus-IQ').get('password')),
            json=payload, headers=headers, verify=False)

        if assigned.status_code == 200:
            print('Successfully assigned category to ' + application.get('name') + " application")


def create_app_category(conf_data, organisation_id, t):
    result = requests.post(sanitise_url(conf_data.get('nexus-IQ').get('url')) +
                           'api/v2/applicationCategories/organization/' + organisation_id,
                           auth=HTTPBasicAuth(conf_data.get('nexus-IQ').get('username'),
                                              conf_data.get('nexus-IQ').get('password')),
                           json=t,
                           headers={"Content-Type": "application/json"},
                           verify=False)
    return result


def get_all_apps(conf_data):
    applications = requests.get(sanitise_url(conf_data.get('nexus-IQ').get('url')) + 'api/v2/applications',
                                auth=HTTPBasicAuth(conf_data.get('nexus-IQ').get('username'),
                                                   conf_data.get('nexus-IQ').get('password')), verify=False)
    apps = applications.json().get('applications')
    return apps


def find_apps_by_org(apps, org_id):
    app_list = list()
    for item in apps:
        if org_id == item.get('organizationId'):
            app_list.append({"id": item.get('id'), "publicId": item.get('publicId'), "name": item.get('name'),
                             "organizationId": org_id})
    return app_list


def sanitise_url(url):
    if url[-1] != '/':
        return url + '/'
    else:
        return url


if __name__ == '__main__':
    main()
