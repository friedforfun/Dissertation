import sys
import argparse
import time
import subprocess
import pandas as pd
import json
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv

from ConsumerAgent.openvino_interaction import BenchmarkQueue, OpenvinoParams, OpenvinoInteraction
from ConsumerAgent.redismanager import RedisConnectionManager
from AgentBase.Utils.Logging import logger
from AgentBase.Utils.Validation import get_check_path, get_check_IPv4, get_check_port, get_check_password

def main():
    run(parse_args())

RESULTS_DIR = './reports'
ONNX_FILE = 'model.onnx'

def run(args):
    try:
        logger.setLevel(5)
        data_path, openvino_path, redis_host, redis_port, redis_password = load_and_check_params(args)

        # Connect to redis
        redis_conn = RedisConnectionManager('Benchmarker', redis_host, port=redis_port, db=0, password=redis_password)

        # Create queue
        bench_queue = BenchmarkQueue()        

        # Tell listener what to do with message
        redis_conn.add_message_fn(bench_queue.queue_message)

        # create and start listener thread
        listener_thread = Thread(target=redis_conn.run, daemon=True)
        listener_thread.start()

        try:
            while True:
                if not bench_queue.is_empty():
                    logger.debug('Start ONNX copy')
                    model_data = bench_queue.pop()
                    copy_to_local_machine(model_data)
                    model_path = ONNX_FILE
                    ov_params = OpenvinoParams(model_path, data_path, perf_count=True, niter=100, report_folder=RESULTS_DIR)
                    benchmark = OpenvinoInteraction(ov_params)
                    logger.debug('Starting benchmark')
                    benchmark.run()
                    logger.debug('Benchmark finished')
                    results_df = read_results()
                    latency = results_df.loc['latency (ms)', :].values[0]
                    throughput = results_df.loc['throughput', :].values[0]
                    logger.debug('Latency: {}'.format(latency))
                    logger.debug('Throughput: {}'.format(throughput))
                    benchmark_results = json.dumps({'Model_UUID': model_data.get('Model-UUID'), 'Latency': latency, 'Throughput': throughput, 'Agent_ID': model_data.get('Agent_ID')})
                    redis_conn.publish_model_result(benchmark_results, model_data.get('Agent_ID'))

                time.sleep(2)

        except KeyboardInterrupt:
            logger.debug('Stopping...')            

    except Exception as e:
        print("Caught exception: {}".format(e))



def copy_to_local_machine(json_message):
    source = '{}@{}:{}'.format(json_message.get('User'), json_message.get('Sender_IP'), json_message.get('ONNX'))
    dest = ONNX_FILE
    subprocess.run(['scp', source, dest], capture_output=False, check=True)
    logger.debug('ONNX copied to local FS')
  

def read_results():
    report_path = '{}/benchmark_report.csv'.format(RESULTS_DIR)
    df = pd.read_csv(report_path, delimiter=';')
    #print(df)
    return df


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
    logger.debug('Path to data: {}'.format(data_path))
    logger.info('Data path OK')
    openvino_path = get_check_path('OPENVINO_ROOT', args.openvino)
    logger.debug('Path to openvino: {}'.format(openvino_path))
    logger.info('Openvino path OK')
    redis_host = get_check_IPv4('REDIS_HOST', args.redis)
    logger.debug('Redis host IP: {}'.format(redis_host))
    logger.info('Redis host IP ok')
    redis_port = get_check_port('REDIS_PORT', args.redis_port)
    logger.debug('Redis port: {}'.format(redis_port))
    logger.info('Redis port ok')
    redis_password = get_check_password('REDIS_PASSWORD', args.redis_password)
    if redis_password is not None:
        logger.debug('Redis password set: ********')
    else:
        logger.debug('No password for redis set.')

    return data_path, openvino_path, redis_host, redis_port, redis_password


if __name__ == "__main__":
    sys.exit(main() or 0)
