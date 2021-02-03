import sys, argparse, os
from pathlib import Path
from dotenv import load_dotenv
from ProducerAgent.Utils.Validation import check_model, get_check_path, get_check_IPv4, get_check_port
from ProducerAgent.Utils.Logging import logger


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
        env_path = Path('.env')
        load_dotenv(dotenv_path=env_path)

        model = check_model(args.model)
        logger.info('Model Ok')

        yaml_path = get_check_path(None, args.yaml)
        logger.info('yaml file Ok')

        data_path = get_check_path('DATASET_ROOT', args.data)
        logger.info('Data path OK')
        distiller_path = get_check_path('DISTILLER_ROOT', args.distiller)
        logger.info('Distiller path OK')
        redis_host = get_check_IPv4('REDIS_HOST', args.redis)
        logger.info('Redis host IP ok')
        redis_port = get_check_port('REDIS_PORT', args.redis_port)

        # Add the compress_classifier.py parent folder to the path so we can import compress_classifier.py
        compress_path = distiller_path + '/examples/classifier_compression'
        sys.path.append(compress_path)

        #data_collector = DataCollector(path)
        #load = Thread(target=process_file, args=(data_collector,), daemon=True)
        #load.start()
    except ValueError as v:
        logger.exception("Value error caught in run(args) with message: {}".format(v))
    except Exception as e:
        print("Caught exception: {}".format(e))


def parse_args():
    parser = argparse.ArgumentParser(description='CLI for Producer.')
    args = parser.add_argument_group('Core parameters')
    args.add_argument('--verbosity', type=int, required=False, default=30, nargs='?',
                                const=20, help='Set the verbosity level, 20 for INFO, 10 for DEBUG. Default is 30: WARN')
    args.add_argument('-mo', '--model', help='Specifies the model to be used', required=True, type=str)
    args.add_argument('-d', '--data', help='Specifies the data directory', required=True, type=str)
    args.add_argument('-y', '--yaml', help='Specifly the .yaml file to use', required=True, type=str)
    args.add_argument('-R', '--redis', help='Specifies the redis host ip', required=False, default=None, type=str)
    args.add_argument('-rp', '--redis_port', help='Specifies the redis host port', required=False, default='6379', type=str)
    args.add_argument('-i', '--distiller',help='Specifies the Distiller root directory', required=False, default=None, type=str)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main() or 0)
    