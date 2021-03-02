import sys, argparse, os
from pathlib import Path
from threading import Thread
import json
import socket

from dotenv import load_dotenv

from AgentBase.Utils.Validation import check_model, get_check_path, get_check_IPv4, get_check_port, get_check_password
from AgentBase.Utils.Logging import logger

from ProducerAgent.distiller_interaction import Distiller, CompressionParams
from ProducerAgent.filewatcher import FileCreationWatcher
from ProducerAgent.redismanager import RedisConnectionManager
from ProducerAgent.yamlEditor import YamlEditor


def main():
    run(parse_args())


def run(args):
    try:
        AGENT_ID = 'MainTest'
        verbosity = args.verbose
        # Set to 5 for todo messages while developing
        logger.setLevel(5)
        #logger.setLevel(verbosity)

        logger.info('Verbosity set to display info messages.')
        logger.debug('Verbosity set to display debug messages.')
        logger.distiller('Verbosity set to display messages from distiller')
        logger.todo('Verbosity set to display todo messages')

        model, yaml_path, data_path, distiller_path, redis_host, redis_port, redis_password = load_and_check_params(args)

        add_compress_classifier_to_path(distiller_path)

        yaml_test = YamlEditor(yaml_path)
        yaml_test.print()



        print(yaml_test.yaml_object.get('pruners').get('fc_pruner'))

        modification_name = 'test'
        modification_path = ['pruners', 'fc_pruner', 'final_sparsity']

        yaml_test.add_modification_path(modification_name, modification_path)


        yaml_test.set_value_by_id('test', 0.99)

        print(yaml_test.yaml_object.get('pruners').get('fc_pruner'))

        test_path = yaml_test.write_yaml()
        print(test_path)

        yaml_path = test_path

        redis_conn = RedisConnectionManager(AGENT_ID, redis_host, port=redis_port, db=0, password=redis_password)

        watcher = FileCreationWatcher()
        watcher.add_redis_to_event_handler(redis_conn)

        watcher_thread = Thread(target=watcher.run, daemon=True)
        watcher_thread.start()

        distiller_params = CompressionParams(model, data_path, yaml_path, epochs=2, lr=0.3, j=6, deterministic=True)
        compressor = Distiller(distiller_params)
        compressor.run()

        watcher.terminate()
        watcher_thread.join()
        logger.setLevel(5)
        if watcher.path is None:
            raise ValueError('No path for checkpoint!')
        logger.debug('!! ------------------------------------------------------ !!')
        logger.debug('Checkpoint path: {}'.format(watcher.path))
        logger.debug('!! ------------------------------------------------------ !!')

        watcher = FileCreationWatcher()
        watcher.add_redis_to_event_handler(redis_conn)
        watcher_thread = Thread(target=watcher.run, daemon=True)
        watcher_thread.start()

        distiller_onnx_params = CompressionParams(model, data_path, yaml_path, epochs=2, lr=0.3, j=6, deterministic=True, onnx='test_model.onnx', resume_from=watcher.path)
        onnx_generator = Distiller(distiller_onnx_params)
        onnx_generator.run()

        watcher.terminate()
        watcher_thread.join()
        logger.setLevel(0)
        redis_onnx = str(os.path.abspath(redis_conn.get_onnx().decode('utf-8')))
        print('ONNX path FROM REDIS: {}'.format(redis_onnx))
        logger.debug('ONNX path: {}'.format(watcher.onnx_path))

        data_for_consumer = json.dumps({'Agent_ID': AGENT_ID, 'Model-UUID': str(compressor.onnx_id), 'ONNX': redis_onnx, 'Sender_IP': get_lan_ip(), 'User': 'sam'})
        redis_conn.publish_model(data_for_consumer)

        redis_conn.listen_blocking(lambda msg: print(msg), lambda _: True)
        print('Got response from Benchmarker')
        
        #watcher = FileCreationWatcher()
        #watcher.run()
        #print('LOG DIR: {}'.format(logdir))

    except ValueError as v:
        logger.exception("Value error caught in run(args) with message: {}".format(v))
    except Exception as e:
        print("Caught exception: {}".format(e))

def get_lan_ip():
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
    if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), 
    s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, 
    socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


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
        redis_password = get_check_password('REDIS_PASSWORD', args.redis_password)

        return model, yaml_path, data_path, distiller_path, redis_host, redis_port, redis_password


def setup_args(parser):
    args = parser.add_argument_group('Core parameters')
    args.add_argument('--verbose', type=int, required=False, default=30, nargs='?',
                                const=20, help='Set the verbosity level, 20 for INFO, 10 for DEBUG. Default is 30: WARN')
    args.add_argument('-m', '--model', help='Specifies the model to be used', required=True, type=str)
    args.add_argument('-d', '--data', help='Specifies the data directory', required=False, type=str)
    args.add_argument('-y', '--yaml', help='Specifly the .yaml file to use', required=True, type=str)
    args.add_argument('--redis', help='Specifies the redis host ip', required=False, default=None, type=str)
    args.add_argument('--redis_port', help='Specifies the redis host port', required=False, default=6379, type=int)
    args.add_argument('--redis_password', help='The password for the redis db', required=False, default=None, type=str)
    args.add_argument('--distiller',help='Specifies the Distiller root directory', required=False, default=None, type=str)
    args.add_argument('--yaml_spec', help='A yaml file to specify the nodes in the schedule to modify', required=False, type=str)
    return parser

def parse_args():
    parser = argparse.ArgumentParser(description='CLI for Producer.')
    return setup_args(parser).parse_args()


if __name__ == "__main__":
    sys.exit(main() or 0)
    