import sys, argparse, os
from pathlib import Path
from dotenv import load_dotenv
from .Utils.Validation import validate_path, check_model, validate_ipv4
from .Utils.Logging import logger

def main():
    run(parse_args())

def run(args):
    try:
        verbosity = args.verbose
        # Set to 5 for todo messages while developing
        logger.setLevel(1)
        #logger.setLevel(verbosity)

        logger.info('Verbosity set to display info messages.')
        logger.debug('Verbosity set to display debug messages.')
        logger.todo('Verbosity set to display todo messages')
        env_path = Path('..') / '.env'
        load_dotenv(dotenv_path=env_path)

        model = check_model(args.model)
        yaml_path = validate_path(args.yaml)

        data_path = get_check_path('DATASET_ROOT', args.data)
        distiller_path = get_check_path('DISTILLER_ROOT', args.distiller)
        redis_host = get_check_IPv4('REDIS_HOST', args.redis)

        # Add the compress_classifier.py parent folder to the path so we can import compress_classifier.py
        compress_path = distiller_path + '/examples/classifier_compression'
        sys.path.append(compress_path)

        #data_collector = DataCollector(path)
        #load = Thread(target=process_file, args=(data_collector,), daemon=True)
        #load.start()


def get_check_path(env_key, arg_data):
    env_data = os.getenv(env_key)
    if arg_data:
        return validate_path(arg_data)
    elif env_data:
        return validate_path(env_data)
    else:
        raise ValueError('Unspecified or invalid {}'.format(env_key))


def get_check_IPv4(env_key, arg_data):
    env_data = os.getenv(env_key)
    if arg_data:
        return validate_ipv4(arg_data)
    elif env_data:
        return validate_ipv4(env_data)
    else:
        raise ValueError('Unspecified or invalid {}'.format(env_key))


def parse_args():
    parser = argparse.ArgumentParser(description='CLI for Producer.')
    args = parser.add_argument_group('Core parameters')
    args.add_argument('-v', '--verbose', type=int, required=False, default=30, nargs='?',
                                const=20, help='Set the verbosity level, 20 for INFO, 10 for DEBUG. Default is 30: WARN')
    args.add_argument('-m', '--model', help='Specifies the model to be used', required=True, type=str)
    args.add_argument('-d', '--data', help='Specifies the data directory', required=True, type=str)
    args.add_argument('-y', '--yaml', help='Specifly the .yaml file to use', required=True, type=str)
    args.add_argument('-R', '--redis', help='Specifies the redis host ip', required=False, default=None, type=str)
    args.add_argument('-D', '--distiller',help='Specifies the Distiller root directory', required=False, default=None, type=str)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main() or 0)
    