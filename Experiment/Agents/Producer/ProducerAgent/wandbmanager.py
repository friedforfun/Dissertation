import wandb
import sys
import argparse
import json
from ProducerAgent.distiller_interaction import Distiller, CompressionParams
from ProducerAgent.redismanager import RedisConnectionManager

import random
from dotenv import load_dotenv
from pathlib import Path
from ProducerAgent.Utils.Validation import get_check_path


model = 'resnet20_cifar'
data_path = '/home/sam/Projects/distiller/datasets/cifar10'
yaml_path = '/home/sam/Projects/distiller/examples/agp-pruning/resnet20_filters.schedule_agp.yaml'


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-lr', '--learning_rate', nargs=1, type=float)

    return parser.parse_args()

LOGS_PATH = '/home/sam/Projects/Dissertation/Experiment/Agents/Producer/'

param_defaults = {
    'learning_rate': 0.3,
    'epochs': 180
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


def log_wandb(data):
    metrics_dict = json.loads(data)
    metrics_dict.accuracy = random.uniform(0.80, 0.99)
    metrics_dict.latency = random.uniform(9.8, 11)
    metrics = {'Accuracy': metrics_dict.get('accuracy'), 'Loss': metrics_dict.get('loss'), 'Latency (ms)': metrics_dict.get('latency'), 'Throughput': metrics_dict.get('throughput')}
    wandb.log(metrics)


def run(args):
    try:
        learning_rate = args.learning_rate[0]
        epochs = args.epochs[0]

        distiller_params = CompressionParams(model, data_path, yaml_path, epochs=epochs, lr=learning_rate, j=6, deterministic=True)
        compressor = Distiller(distiller_params)
        watcher = compressor.run()

        if watcher.path is None:
            raise ValueError('No path for checkpoint!')
        print('Checkpoint path: {}'.format(watcher.path))

        distiller_onnx_params = CompressionParams(model, data_path, yaml_path, epochs=epochs, lr=learning_rate, j=6, deterministic=True, onnx='test_model.onnx', resume_from=watcher.path)


        compressor = Distiller(distiller_onnx_params)

        watcher = compressor.run()

        print('ONNX path: {}'.format(watcher.onnx_path))

        #! Send onnx model path to redis and block until results come back

        r_conn = RedisConnectionManager('Test_agent', '192.168.86.108', port=6379, db=0)
        consumer_data = json.dumps({'Agent_name': 'Test_agent', 'Model-UUID': str(compressor.onnx_id), 'ONNX': watcher.onnx_path})

        r_conn.publish(consumer_data)

        r_conn.listen_blocking(log_wandb)

        metrics = {'accuracy': random.uniform(0.80, 0.99), 'loss': None, 'latency (ms)': random.uniform(9.8, 11), 'Throughput': None}
        wandb.log(metrics)



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


if __name__ == '__main__':
   sys.exit(main() or 0)