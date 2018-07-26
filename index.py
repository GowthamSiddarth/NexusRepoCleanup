import argparse, logging, re, requests, os, subprocess, itertools
from urllib.parse import urlparse


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


def get_components(host, repository_name, component_name):
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

        components = [component for component in list(itertools.chain(*components)) if
                      component['name'] == component_name]
        logger.info("%d components found in the repo %s for %s" % (len(components), repository_name, component_name))
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
    parser.add_argument('-c', '--component', help="Name of the component whose assets are to be deleted", required=True)
    parser.add_argument('-k', '--keep', help="Number of assets/components to preserve after cleanup", required=True)
    parser.add_argument('--host', help="Host address of nexus repository", default="http://192.168.113.192:15921")
    parser.add_argument('-u', '--username', help="Username of the nexus repository admin", default="admin")
    parser.add_argument('-p', '--password', help="Password of the nexus repository admin", default="admin123")

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

    if repository_format == 'docker':
        logger.info("Using nexus-cli to un-tag extra blobs")
        create_nexus_credentials_at_workspace(args['host'], args['username'], args['password'], args['repository'])
        subprocess.call(['nexus-cli', 'image', 'delete', '-name', args['component'], '-keep', str(args['keep'])])
    elif repository_format == 'maven2':
        logger.info("Using Nexus REST APIs to delete extra components")
        components = get_components(args['host'], args['repository'], args['component'])
        extra_components = sorted(components, key=lambda component: component.get('version'))[:-args['keep']]
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
