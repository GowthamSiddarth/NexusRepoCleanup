import argparse, logging, re, requests, os, subprocess, itertools
from urllib.parse import urlparse


def get_task_id(host, task_name):
    logger.info("Started executing get_task_id()")

    get_tasks_api = host + '/service/rest/beta/tasks?type=blobstore.compact'
    try:
        while True:
            response = requests.get(get_tasks_api)
            response.raise_for_status()

            data = response.json()
            tasks = data['items']
            for task in tasks:
                logger.debug("task_name passed as arg: %s, current task_name: %s", (task_name, task['name']))
                if task['name'] == task_name:
                    return task['id']

            continuation_token = data['continuationToken']
            if continuation_token is None:
                break

            get_tasks_api = host + '/service/rest/beta/tasks?type=blobstore.compact' + '&continuationToken=' + continuation_token
    except requests.exceptions.RequestException as e:
        logger.error("Exception occurred: " + str(e))
        return None

    logger.info("Finished executing get_task_id")
    return None


def compact_blob_store(host, task_name):
    logger.info("Started executing compact_blob_store()")

    task_id = get_task_id(host, task_name)
    logger.debug("task_id returned as " + str(task_id))

    if task_id is not None:
        task_run_api = host + '/service/rest/beta/tasks/' + task_id + '/run'
        try:
            response = requests.get(task_run_api)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("Exception occurred: " + str(e))

    logger.info("Finished executing compact_blob_store")


def delete_extra_components(host, username, password, extra_components):
    logger.info("Started executing delete_extra_components()")

    parsed_url = urlparse(url=host)
    component_del_base_api = parsed_url.scheme + '://' + username + ':' + password + '@' + parsed_url.netloc + '/service/rest/beta/components'
    for extra_component in extra_components:
        component_del_api = component_del_base_api + '/' + extra_component['id']
        logger.debug("Calling API to delete component: " + component_del_api)
        try:
            response = requests.delete(component_del_api)
            response.raise_for_status()

            logger.debug("API Response: " + str(response))
        except requests.exceptions.RequestException as e:
            logger.error("Exception occurred: " + str(e))

    logger.info("delete_extra_components function execution finished")


def get_matching_components_by_name(components, component_name):
    if component_name is None:
        logger.info("Component Name is None, hence returning all components\' names")
        return set([component['name'] for component in components])
    else:
        for component in components:
            logger.debug(
                "Component Name passed as arg: %s, Current Component Name: %s" % (component_name, component['name']))
            if component['name'] == component_name:
                logger.debug("Match found for Component Name %s" % component_name)
                return [component_name]

        logger.debug("No Match found for component name %s" % component_name)
        return []


def group_by_components(components, component_name):
    logger.info("Started executing group_by_components()")

    components_group = {}
    for component in components:
        if component_name is None or component_name == component['name']:
            components_group[component['name']] = components_group.get(component['name'], []) + \
                                                  [{'id': component['id'], 'version': component['version']}]

    logger.debug("Components Group:" + str(components_group))
    logger.info("Finished executing group_by_components")
    return components_group


def get_components(host, repository_name, component_name, repository_format):
    logger.info("Started executing get_components()")

    get_components_api, components = host + '/service/rest/beta/components?repository=' + repository_name, []
    try:
        while True:
            response = requests.get(get_components_api)
            response.raise_for_status()

            data = response.json()
            components.append(data['items'])
            continuation_token = data['continuationToken']
            if continuation_token is None:
                break

            get_components_api = host + '/service/rest/beta/components?repository=' + repository_name + '&continuationToken=' + continuation_token

        if repository_format == 'docker':
            logger.info("repository_format is docker")
            components = get_matching_components_by_name(list(itertools.chain(*components)), component_name)
            logger.info("%d components found in repo %s for %s" % (len(components), repository_name, component_name))
        elif repository_format == 'maven2':
            logger.info("repository_format is maven2")
            components = group_by_components(list(itertools.chain(*components)), component_name)
            logger.info("%d components found in repo %s for %s" % (len(components), repository_name, component_name))
            return components
    except requests.exceptions.RequestException as e:
        logger.error("Exception occurred: " + str(e))
        return None


def create_nexus_credentials_at_workspace(host, username, password, repository):
    logger.info("Started executing create_nexus_credentials_at_workspace()")

    workspace = os.getcwd()
    nexus_data = {'nexus_host': '"%s"' % host,
                  'nexus_username': '"%s"' % username,
                  'nexus_password': '"%s"' % password,
                  'nexus_repository': '"%s"' % repository}
    file = open(workspace + '/.credentials', "w")
    file.write(str(nexus_data))
    file.close()

    logger.info("create_nexus_credentials_at_workspace function execution finished")


def get_repository_format(host, repository_name):
    logger.info("Started executing get_repository_type()")

    get_repositories_api = host + '/service/rest/beta/repositories'
    try:
        response = requests.get(get_repositories_api)
        response.raise_for_status()

        repositories = response.json()
        for repository in repositories:
            logger.debug("Repository: " + str(repository))
            if repository['name'] == repository_name:
                logger.debug("Repository Name match found")
                return repository['format']

        logger.warning("No repository found with given name: " + str(repository_name))
    except requests.exceptions.RequestException as e:
        logger.error("Exception occurred: " + str(e))

    return None


def validate_args(args):
    logger.info("Started executing validate_args()")

    args['host'] = args['host'].strip('/')
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    logger.info("validate_args function execution finished")
    return args['keep'].isdigit() and re.match(regex, args['host'])


def parse_args():
    logger.info("Started executing parse_args()")

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repository', help="Name of the repository to be cleaned", required=True)
    parser.add_argument('-c', '--component', help="Name of the component whose assets are to be deleted")
    parser.add_argument('-k', '--keep', help="Number of assets/components to preserve after cleanup", required=True)
    parser.add_argument('--host', help="Host address of nexus repository", default="http://192.168.113.192:15921")
    parser.add_argument('-u', '--username', help="Username of the nexus repository admin", default="admin")
    parser.add_argument('-p', '--password', help="Password of the nexus repository admin", default="admin123")
    parser.add_argument('-t', '--task', help="Name of blobstore compact task", default="BlobStoreCleanUp")

    logger.info("parse_args function execution finished")
    return vars(parser.parse_args())


def main(logger):
    logger.info("Started executing main function")

    args = parse_args()
    logger.debug("Arguments parsed are: " + str(args))

    args_valid = validate_args(args)
    if not args_valid:
        logger.error("Arguments passed are not valid. Use -h for help")
        return
    else:
        args['keep'] = 10 if int(args['keep']) > 10 else int(args['keep'])

    repository_format = get_repository_format(args['host'], args['repository'])
    if repository_format is None:
        logger.info("Repository Format returned is None. Returning execution from here!")
        return
    else:
        logger.info("Repository Format of %s is %s" % (args['repository'], repository_format))

    components = get_components(args['host'], args['repository'], args['component'], repository_format)
    if repository_format == 'docker':
        logger.info("Using nexus-cli to un-tag extra blobs")
        create_nexus_credentials_at_workspace(args['host'], args['username'], args['password'], args['repository'])
        for component in components:
            logger.debug("Component to be cleaned using nexus-cli: %s", component)
            subprocess.call(['nexus-cli', 'image', 'delete', '-name', component, '-keep', str(args['keep'])])

        compact_blob_store(args['host'], args['task'])
    elif repository_format == 'maven2':
        logger.info("Using Nexus REST APIs to delete extra components")
        for component in components.keys():
            extra_components = sorted(components[component], key=lambda component: component.get('version'))[
                               :-args['keep']]
            delete_extra_components(args['host'], args['username'], args['password'], extra_components)

    logger.info("Main function execution finished.")


def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


if __name__ == '__main__':
    logger = init_logger()
    logger.info("Logger Initialized...Calling main function")
    main(logger)
    logger.info("Returned from main execution. Ending Program!")
