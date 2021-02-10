import sys, argparse, os
from pathlib import Path
from dotenv import load_dotenv
from ProducerAgent.Utils.Validation import check_model, get_check_path, get_check_IPv4, get_check_port
from ProducerAgent.Utils.Logging import logger
from ProducerAgent.distiller_interaction import Distiller, CompressionParams
from ProducerAgent.filewatcher import FileCreationWatcher
from ProducerAgent.redismanager import RedisConnectionManager



def main():
    run(parse_args())

def run(args):
    try:
        verbosity = args.verbose
        # Set to 5 for todo messages while developing
        logger.setLevel(5)
        #logger.setLevel(verbosity)

        logger.info('Verbosity set to display info messages.')
        logger.debug('Verbosity set to display debug messages.')
        logger.distiller('Verbosity set to display messages from distiller')
        logger.todo('Verbosity set to display todo messages')

        model, yaml_path, data_path, distiller_path, redis_host, redis_port = load_and_check_params(args)

        add_compress_classifier_to_path(distiller_path)

        redis_conn = RedisConnectionManager('MainTest', redis_host, port=redis_port, db=0)

        watcher = FileCreationWatcher()

        watcher.add_redis_to_event_handler(redis_conn)

        distiller_params = CompressionParams(model, data_path, yaml_path, epochs=2, lr=0.3, j=6, deterministic=True)
        compressor = Distiller(distiller_params, watcher)
        watcher = compressor.run()

        if watcher.path is None:
            raise ValueError('No path for checkpoint!')
        print('Checkpoint path: {}'.format(watcher.path))

        distiller_onnx_params = CompressionParams(model, data_path, yaml_path, epochs=2, lr=0.3, j=6, deterministic=True, onnx='test_model.onnx', resume_from=watcher.path)


        compressor = Distiller(distiller_onnx_params, watcher)

        watcher = compressor.run()

        print('ONNX path: {}'.format(watcher.onnx_path))
        #watcher = FileCreationWatcher()
        #watcher.run()
        #print('LOG DIR: {}'.format(logdir))

    except ValueError as v:
        logger.exception("Value error caught in run(args) with message: {}".format(v))
    except Exception as e:
        print("Caught exception: {}".format(e))


def add_compress_classifier_to_path(distiller_path):
    # Add the compress_classifier.py parent folder to the path so we can import compress_classifier.py
    compress_path = distiller_path + '/examples/classifier_compression'
    sys.path.append(compress_path)
    logger.debug('Added {} to system path'.format(compress_path))

def load_and_check_params(args):
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
        logger.info('Redis port ok')
        return model, yaml_path, data_path, distiller_path, redis_host, redis_port


def setup_args(parser):
    args = parser.add_argument_group('Core parameters')
    args.add_argument('--verbose', type=int, required=False, default=30, nargs='?',
                                const=20, help='Set the verbosity level, 20 for INFO, 10 for DEBUG. Default is 30: WARN')
    args.add_argument('-m', '--model', help='Specifies the model to be used', required=True, type=str)
    args.add_argument('-d', '--data', help='Specifies the data directory', required=True, type=str)
    args.add_argument('-y', '--yaml', help='Specifly the .yaml file to use', required=True, type=str)
    args.add_argument('--redis', help='Specifies the redis host ip', required=False, default=None, type=str)
    args.add_argument('--redis_port', help='Specifies the redis host port', required=False, default=6379, type=int)
    args.add_argument('--distiller',help='Specifies the Distiller root directory', required=False, default=None, type=str)
    return parser

def parse_args():
    parser = argparse.ArgumentParser(description='CLI for Producer.')
    return setup_args(parser).parse_args()


if __name__ == "__main__":
    sys.exit(main() or 0)
    