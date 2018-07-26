import argparse, logging


def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def init():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repository', help="Name of the repository to be cleaned", required=True)
    parser.add_argument('-k', '--keep', help="Number of assets/components to preserve after cleanup", required=True)
    parser.add_argument('--host', help="Host address of nexus repository", default="http://192.168.113.192:15921")
    parser.add_argument('-u', '--username', help="Username of the nexus repository admin", default="admin")
    parser.add_argument('-p', '--password', help="Password of the nexus repository admin", default="admin123")
    return vars(parser.parse_args())


def main():

    args = init()
    print(args)


if __name__ == '__main__':
    main()
