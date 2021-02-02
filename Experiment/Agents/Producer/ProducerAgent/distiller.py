from compress_classifier import main as compress_classifier

"""
    Sets compression params and starts compression
"""

class Distiller:

    def __init__(self, model_name, data_path, yaml_path):
        
        self.model_name = model_name
        self.data_path = data_path
        self.yaml_path = yaml_path
        

    def run(self):
        """Begin pruning with the given parameters
        """

        pass

class CompressionParams:

    def __init__(self):
        pass
