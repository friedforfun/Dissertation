import sys
import json
from collections import deque

from AgentBase.Utils.Logging import logger

class OpenvinoInteraction:
    def __init__(self, params):
        self.params = params

    def run(self):
        try:
            from openvino.tools.benchmark.main import main
            self.params.clear_and_set_params()
            main()

        except Exception as e:
            logger.debug('Openvino exception encountered: {}'.format(e))

class OpenvinoParams:
    def __init__(self, model_path, images_path, architecture='MYRIAD', perf_count=None, niter=None, report_type='detailed_counters', report_folder='./reports'):
        self.param_list = []

        self.model_path = model_path
        self.param_list.append('-m={}'.format(model_path))

        self.images_path = images_path
        self.param_list.append('-i={}'.format(images_path))

        self.architecture = architecture
        self.param_list.append('-d={}'.format(architecture))

        if niter is not None:
            self.niter = niter
            self.param_list.append('-niter={}'.format(niter))
    
        if perf_count is not None:
            self.perf_count = perf_count
            self.param_list.append('-pc={}'.format(perf_count))

        self.report_type = report_type
        self.param_list.append('-report_type={}'.format(report_type))

        self.report_folder = report_folder
        self.param_list.append('-report_folder={}'.format(report_folder))

    def clear_and_set_params(self):
        # Clear parameters for argparse
        sys.argv = [sys.argv[0]]   

        for param in self.param_list:
            sys.argv.append(param)

class BenchmarkQueue:
    def __init__(self):
        self.q = deque()

    def append(self, item):
        self.q.append(item)

    def pop(self):
        return self.q.popleft()

    def queue_message(self, message):
        #logger.debug('Message recieved: {}'.format(message))
        d_message = message.decode('utf-8')
        json_message = json.loads(d_message)
        logger.debug('------------------------- ONNX COPY LOCATION -------------------------')
        for k, v in json_message.items():
            logger.debug('{}: {}'.format(k, v))
        self.append(json_message)

    def is_empty(self):
        if self.q:
            return False
        else:
            return True
