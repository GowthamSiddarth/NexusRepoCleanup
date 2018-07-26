import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--repository', help="Name of the repository to be cleaned", required=True)
    parser.add_argument('-k', '--keep', help="Number of assets/components to preserve after cleanup", required=True)
    parser.add_argument('-h', '--host', help="Host address of nexus repository", default="http://192.168.113.192:15921")
    parser.add_argument('-u', '--username', help="Username of the nexus repository admin", default="admin")
    parser.add_argument('-p', '--password', help="Password of the nexus repository admin", default="admin123")
    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
