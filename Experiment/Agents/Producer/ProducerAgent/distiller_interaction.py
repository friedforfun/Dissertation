import sys
import uuid
from AgentBase.Utils.Logging import logger

"""
    Sets compression params and starts compression
"""

class Distiller:

    def __init__(self, CLI_params):
        
        self.onnx_id = uuid.uuid1()
        self.CLI_params = CLI_params
        #self.watcher = watcher

         
    def run(self):
        """Begin pruning with the given parameters
        """
        
        try:
            import compress_classifier
            self.CLI_params.clear_and_set_params()
            compress_classifier.main()


        except KeyboardInterrupt:
            print("\n-- KeyboardInterrupt --")
        except Exception as e:
            logger.exception('Exception from distiller compress_classifier: {}'.format(e))
            raise e

        


class CompressionParams:
    """CLI params compress classifier uses

    Args:
        arch (string): The model architecture
        data_path (string): Path for the data
        yaml_path (string): Path to the .yaml file that defines the compression settings
        epochs (int, optional): Number of epochs. Defaults to 180.
        lr (string, optional): Initial learning rate. Defaults to None.
        j (int, optional): number of workers. Defaults to None.
        p (string, optional): print frequency. Defaults to None.
        deterministic (Any, optional): Ensure deterministic execution. Defaults to None.
        resume_from (string, optional): Checkpoint path to resume from. Defaults to None.
        onnx (string, optional): Export to ONNX format with this name. Defaults to None.
        thinnify (Any, optional): Remove zero filters and create a smaller model. Defaults to None.
        reset_optimizer (Any, optional): Flag to override optimizer if resumed from checkpoint. This will reset epochs count.
    """

    def __init__(self, arch, data_path, yaml_path, epochs=180, lr=None, j=None, p=50, deterministic=None, resume_from=None, onnx=None, thinnify=None, reset_optimizer=None):

        self.param_list = []

        self.param_list.append('--arch={}'.format(arch))
        self.arch = arch

        self.param_list.append('{}'.format(data_path))
        self.data_path = data_path

        self.param_list.append('--compress={}'.format(yaml_path))
        self.yaml = yaml_path

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

        if reset_optimizer is not None:
            self.param_list.append('--reset-optimizer')
            self.reset_optimizer = reset_optimizer

    
    def clear_and_set_params(self):
        """Clear argv parameters and set the new parameters defined by DistillerParams
        """

        sys.argv = [sys.argv[0]]

        for param in self.param_list:
            sys.argv.append(param)
