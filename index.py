import argparse, logging, re


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

    return args['keep'].isdigit() and re.match(regex, args['host'])


def parse_args():
    logger.info("Started executing parse_args()")

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repository', help="Name of the repository to be cleaned", required=True)
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
