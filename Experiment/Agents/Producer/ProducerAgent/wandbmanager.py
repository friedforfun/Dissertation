import wandb
import os
import sys
import argparse
from threading import Thread
import json
import socket
import uuid
from ProducerAgent.distiller_interaction import Distiller, CompressionParams
from ProducerAgent.redismanager import RedisConnectionManager
from ProducerAgent.filewatcher import FileCreationWatcher
from ProducerAgent.main import load_and_check_params, add_compress_classifier_to_path, setup_args
from AgentBase.Utils.Logging import logger
import random
from dotenv import load_dotenv
from pathlib import Path
from ProducerAgent.Utils.Validation import get_check_path

AGENT_ID = str(uuid.uuid4())
#AGENT_ID = 'wandbTest'

MODEL = 'resnet20_cifar'
DATA_PATH = '/home/sam/Projects/distiller/datasets/cifar10'
YAML_PATH = '/home/sam/Projects/distiller/examples/agp-pruning/resnet20_filters.schedule_agp.yaml'



def parse_args():

    parser = argparse.ArgumentParser()
    parser = setup_args(parser)
    args = parser.add_argument_group('WandB args')
    args.add_argument('-lr', '--learning_rate', nargs=1, type=float)

    return parser.parse_args()

LOGS_PATH = '/home/sam/Projects/Dissertation/Experiment/Agents/Producer/'

param_defaults = {
    'learning_rate': 0.3,
    'epochs': 1
}


wandb.init(config=param_defaults, project='Test-Compression')
config = wandb.config


def main():
    

    env_path = Path('.env')
    load_dotenv(dotenv_path=env_path)
    distiller_path = get_check_path('DISTILLER_ROOT', None)
    compress_path = distiller_path + '/examples/classifier_compression'
    sys.path.append(compress_path)
    run(parse_args())


def check_data(data):

    data = data.decode('utf-8')

    print('Checking data')

    metrics_dict = json.loads(data)
    
    if metrics_dict is None:
        return False

    # Sanity check make sure the data recived was sent by this agent.
    if metrics_dict.get('Agent_ID') == AGENT_ID:
        return True
    else:
        print('Got back bad data')
        return False

def log_wandb(data):
    #if check_data(data):
    data = data.decode('utf-8')
    metrics_dict = json.loads(data)
    print('METRICS: {}'.format(metrics_dict))
    metrics_dict['accuracy'] = random.uniform(0.80, 0.99)

    metrics = {'Accuracy': metrics_dict.get('accuracy'), 'latency': metrics_dict.get('Latency'), 'Throughput': metrics_dict.get('Throughput')}
    print('Logging wandb metrics')
    wandb.log(metrics)


def run(args):
    try:
        
        MODEL, YAML_PATH, DATA_PATH, DISTILLER_PATH, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD = load_and_check_params(args)
        add_compress_classifier_to_path(DISTILLER_PATH)

        learning_rate = args.learning_rate[0]
        epochs = 1
        j = 6 # data loading worker threads
        deterministic = True # make results deterministic with the same paramaters

        # Instantiate Redis Connection manager
        r_conn = RedisConnectionManager(AGENT_ID, REDIS_HOST, port=REDIS_PORT, db=0, password=REDIS_PASSWORD)

        # Instantiate File watcher & add reference to connection manager
        watcher = FileCreationWatcher()
        watcher.add_redis_to_event_handler(r_conn)
        watcher_thread = Thread(target=watcher.run, daemon=True)
        watcher_thread.start()

        # Set up distiller CLI params
        distiller_params = CompressionParams(MODEL, DATA_PATH, YAML_PATH, epochs=epochs, lr=learning_rate, j=j, deterministic=deterministic)
        
        # Start distiller & run
        compressor = Distiller(distiller_params)
        compressor.run()

        watcher.terminate()
        watcher_thread.join()

        # Check if checkpoint path is found
        if watcher.path is None:
            raise ValueError('No path for checkpoint!')
        print('Checkpoint path: {}'.format(watcher.path))
        checkpoint_abs_path = os.path.abspath(watcher.path)

        watcher = FileCreationWatcher()
        watcher.add_redis_to_event_handler(r_conn)
        watcher_thread = Thread(target=watcher.run, daemon=True)
        watcher_thread.start()

        # Run distiller again but start from checkpoint and export onnx
        distiller_onnx_params = CompressionParams(MODEL, DATA_PATH, YAML_PATH, epochs=epochs, lr=learning_rate, j=j, deterministic=deterministic, onnx='test_model.onnx', resume_from=watcher.path)
        compressor = Distiller(distiller_onnx_params)
        compressor.run()

        watcher.terminate()
        watcher_thread.join()

        redis_onnx = str(os.path.abspath(r_conn.get_onnx().decode('utf-8')))
        print('REDIS ONNX: {}'.format(redis_onnx))
        
        #onnx_abs_path = os.path.abspath(compressor.watcher.onnx_path)

        #print('ONNX path: {}'.format(watcher.onnx_path))
        #print('ABOLSUTE CHECKPOINT PATH: {}'.format(checkpoint_abs_path))
        #print('ABOLSUTE ONNC PATH: {}'.format(onnx_abs_path))
        #! Send onnx model path to redis and block until results come back

        consumer_data = json.dumps({'Agent_ID': AGENT_ID, 'Model-UUID': str(compressor.onnx_id), 'ONNX':redis_onnx, 'Sender_IP': get_lan_ip(), 'User': 'sam'})

        r_conn.publish_model(consumer_data)
        print('Model published.')
        r_conn.listen_blocking(log_wandb, lambda _: True)

        #metrics = {'accuracy': random.uniform(0.80, 0.99), 'loss': None, 'latency (ms)': random.uniform(9.8, 11), 'Throughput': None}
        #wandb.log(metrics)



    except TypeError as e:
        display_exception(e)
        wandb.alert(title="Sweep exception raised",
                    text="Check the types of the parameters.\n {}".format(e))
        sys.exit(1)
    except AttributeError as e:
        display_exception(e)
        wandb.alert(title="Sweep exception raised",
                    text="Check the attributes being called in script (line 66?) \n {}".format(e))
        sys.exit(1)
    except Exception as e:
        display_exception(e)
        wandb.alert(title="Sweep exception raised",
                    text="An exception was raised during this sweep. \n {}".format(e))
        sys.exit(1)


def display_exception(e):
    print('Exception encountered: ', e)
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(e).__name__, e.args)
    print(message)

def get_lan_ip():
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
    if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), 
    s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, 
    socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

if __name__ == '__main__':
   sys.exit(main() or 0)