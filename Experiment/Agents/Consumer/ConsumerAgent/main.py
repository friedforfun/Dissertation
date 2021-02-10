import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from ConsumerAgent.Utils.Logging import logger
from ConsumerAgent.Utils.Validation import get_check_path, get_check_IPv4, get_check_port, get_check_password

def main():
    run(parse_args())


def run(args):
    try:
        data_path, openvino_path, redis_host, redis_port, redis_password = load_and_check_params(args)


    except Exception as e:
        print("Caught exception: {}".format(e))


def setup_args(parser):
    args = parser.add_argument_group('Core parameters')
    args.add_argument('--verbose', type=int, required=False, default=30, nargs='?',
                                const=20, help='Set the verbosity level, 20 for INFO, 10 for DEBUG. Default is 30: WARN')
    args.add_argument('--redis', help='Specifies the redis host ip', required=False, default=None, type=str)
    args.add_argument('--redis_port', help='Specifies the redis host port', required=False, default=6379, type=int)
    args.add_argument('--redis_password', help='The password for the redis db', required=False, default=None, type=str)
    args.add_argument('--openvino',help='Specifies the Openvino root directory', required=False, default=None, type=str)
    args.add_argument('-d', '--data', help='Specifies the testng data directory', required=False, type=str)
    return parser

def parse_args():
    parser = argparse.ArgumentParser(description='CLI settings for consumber agent')
    return setup_args(parser).parse_args()

def load_and_check_params(args):
    env_path = Path('.env')
    load_dotenv(dotenv_path=env_path)

    data_path = get_check_path('DATASET_ROOT', args.data)
    logger.info('Data path OK')
    openvino_path = get_check_path('OPENVINO_ROOT', args.openvino)
    logger.info('Distiller path OK')
    redis_host = get_check_IPv4('REDIS_HOST', args.redis)
    logger.info('Redis host IP ok')
    redis_port = get_check_port('REDIS_PORT', args.redis_port)
    logger.info('Redis port ok')
    redis_password = get_check_password('REDIS_PASSWORD', args.redis_password)

    return data_path, openvino_path, redis_host, redis_port, redis_password


if __name__ == "__main__":
    sys.exit(main() or 0)
