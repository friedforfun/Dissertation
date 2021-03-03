import wandb
import os
import sys
import io
import argparse
from threading import Thread
import json
import socket
import uuid
import logging
from ProducerAgent.distiller_interaction import Distiller, CompressionParams
from ProducerAgent.redismanager import RedisConnectionManager
from ProducerAgent.filewatcher import FileCreationWatcher
from ProducerAgent.yamlEditor import YamlEditorBuilder
from ProducerAgent.main import load_and_check_params, add_compress_classifier_to_path, setup_args
from AgentBase.Utils.Logging import logger



AGENT_ID = str(uuid.uuid4())
#AGENT_ID = 'wandbTest'

#MODEL = 'resnet56_cifar'
#DATA_PATH = '/home/sam/Projects/distiller/datasets/cifar10'
#ORIGINAL_YAML_PATH = '/home/sam/Projects/distiller/examples/agp-pruning/resnet20_filters.schedule_agp.yaml'
#ORIGINAL_YAML_PATH = 'example.yaml'

def parse_args():
    """Parse human supplied args

    Returns:
        Namespace: Known args
    """
    parser = argparse.ArgumentParser()
    parser = setup_args(parser)
    return parser.parse_known_args()[0]

#LOGS_PATH = '/home/sam/Projects/Dissertation/Experiment/Agents/Producer/'


wandb.init(project='Test-Compression')
config = wandb.config


def main():
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



def run(args):
    try:
        
        MODEL, ORIGINAL_YAML_PATH, DATA_PATH, DISTILLER_PATH, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD = load_and_check_params(args)
        add_compress_classifier_to_path(DISTILLER_PATH)

        # Configure yaml editor and wandb specific args
        yamlEditorBuilder = YamlEditorBuilder(args.yaml_spec)
        yamlEditor = yamlEditorBuilder.get_editor(ORIGINAL_YAML_PATH)

        wandb_arg_parser = argparse.ArgumentParser()
        args = wandb_arg_parser.add_argument_group('WandB args')
        wandb_arg_parser = yamlEditorBuilder.get_args(wandb_arg_parser)
        print('Parsing known wandb args')
        wandb_args = wandb_arg_parser.parse_known_args()[0]


        learning_rate = 0.1
        epochs = 70
        j = 6 # data loading worker threads
        deterministic = True # make results deterministic with the same paramaters

        # Set the value sent by wandb in the yaml file
        print('Setting yaml values')
        for k,v in vars(wandb_args).items():
            yamlEditor.set_value_by_id(k, v)
        
        # write it out
        YAML_PATH = yamlEditor.write_yaml()

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
        distiller_onnx_params = CompressionParams(MODEL, DATA_PATH, YAML_PATH, epochs=epochs, lr=learning_rate, j=j, deterministic=deterministic, onnx='test_model.onnx', resume_from=watcher.path, thinnify=True)
        compressor = Distiller(distiller_onnx_params)
        compressor.run()

        watcher.terminate()
        watcher_thread.join()
        

        redis_onnx = str(os.path.abspath(r_conn.get_onnx().decode('utf-8')))
        print('REDIS ONNX: {}'.format(redis_onnx))
        


        consumer_data = json.dumps({'Agent_ID': AGENT_ID, 'Model-UUID': str(compressor.onnx_id), 'ONNX':redis_onnx, 'Sender_IP': get_lan_ip(), 'User': 'sam'})

        r_conn.publish_model(consumer_data)
        print('Model published.')
        
        output_log = str(os.path.abspath(r_conn.get_output().decode('utf-8')))
        if output_log is None:
            raise ValueError("No output.log found")

        # find testing data accuracy from output.log 
        test_accuracy = None

        with open(output_log, 'r') as fh:
            for line in line_contains("==>", fh):
                read_accuracy = line

        # Record the final top1, top5 and loss
        test_accuracy = read_accuracy.rstrip().split()
        print(test_accuracy)

        # Use dummy values incase output.log parse fails
        upload_data = WandbLogger(-1.0, -1.0, -1.0)
        if test_accuracy is not None:
            top1 = float(test_accuracy[2])
            top5 = float(test_accuracy[4])
            loss = float(test_accuracy[6])
            upload_data = WandbLogger(top1, top5, loss)

        # Blocks until a result is sent by the benchmarker
        r_conn.listen_blocking(upload_data.log_wandb, lambda _: True)



    except TypeError as e:
        display_exception(e)
        wandb.alert(title="Sweep exception raised",
                    text="Check the types of the parameters.\n {}".format(e))
        sys.exit(10)
    except AttributeError as e:
        display_exception(e)
        wandb.alert(title="Sweep exception raised",
                    text="Check the attributes being called in script (line 66?) \n {}".format(e))
        sys.exit(11)
    except Exception as e:
        display_exception(e)
        wandb.alert(title="Sweep exception raised",
                    text="An exception was raised during this sweep. \n {}".format(e))
        sys.exit(12)



def line_contains(string, fh):
    for line in fh:
        if string in line:
            yield line


class OutCapture:
    def __init__(self):
        self.st = ''

    def write(self, o):
        self.st += str(o)

class WandbLogger:
    def __init__(self, top1, top5, loss):
        self.top1 = float(top1)
        self.top5 = float(top5)
        self.loss = float(loss)

    def log_wandb(self, data):
        #if check_data(data):
        data = data.decode('utf-8')
        metrics_dict = json.loads(data)

        metrics = {'Top1': self.top1, 'Top5': self.top5, 'Loss': self.loss, 'Latency': float(metrics_dict.get('Latency')), 'Throughput': float(metrics_dict.get('Throughput'))}
        print('Logging wandb metrics')
        wandb.log(metrics)

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