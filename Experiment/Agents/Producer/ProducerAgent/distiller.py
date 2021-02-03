import sys
import uuid
from compress_classifier import main as compress_classifier
from ProducerAgent.Utils.Logging import logger

"""
    Sets compression params and starts compression
"""

class Distiller:

    def __init__(self, model_name, data_path, yaml_path, CLI_params):
        
        self.model_name = model_name
        self.data_path = data_path
        self.yaml_path = yaml_path
        self.onnx_name = uuid.uuid1()
        self.CLI_params = CLI_params

         

    def run(self):
        """Begin pruning with the given parameters
        """
        try:
            # Args to add to sys.argv for compress classifier:
            # --arch self.model_name
            # data_path
            # --compress=yaml file
            # --epochs=180
            # --lr=0.3
            # -j=1
            # --deterministic
            # --export-onnx=self.onnx_name
            # --out-dir
            # --thinnify



            compress_classifier()
        except KeyboardInterrupt:
            print("\n-- KeyboardInterrupt --")
        except Exception as e:
            logger.exception('Exception from distiller compress_classifier: {}'.format(e))
            raise e


class CompressionParams:

    def __init__(self, arch, epochs=180, lr=None, j=None, p=None, deterministic=None, resume_from=None, onnx=None, thinnify=None):
        self.param_list = []

        self.param_list.append('--arch={}'.format(arch))
        self.arch = arch

        self.param_list.append('--epochs={}'.format(epochs))
        self.epochs = epochs
        
        if lr is not None:
            self.param_list.append('--lr={}'.format(lr))
            self.lr = lr

        if j is not None:
            self.param_list.append('-j={}'.format(j))
            self.j = j

        if p is not None:
            self.param_list.append('-p={}'.format(p))
            self.p = p
        
        if deterministic is not None:
            self.param_list.append('--deterministic')
            self.deterministic = deterministic

        if resume_from is not None:
            self.param_list.append('--resume-from={}'.format(resume_from))
            self.resume_from = resume_from

        if onnx is not None:
            self.param_list.append('--export-onnx={}'.format(onnx))
            self.onnx = onnx

        if thinnify is not None:
            self.param_list.append('--thinnify')
            self.thinnify = thinnify

    
        

