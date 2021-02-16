import os
import yaml

from AgentBase.Utils.Logging import logger
# Read YAML file
# Select params to modify
# write copy with modified params

# send message with location of modified yaml file

class YamlEditor:
    def __init__(self, yaml_path):
        self.yaml_path = yaml_path
        self.yaml_object = self.read_yaml()
        self.modification_dict = {}

    def read_yaml(self):
        with open(self.yaml_path) as f:
            return yaml.load(f)
    
    def print(self):
        print(self.yaml_object)

    def add_modification_path(self, id, yaml_dict_path):
        """Add an identifier for a path through the parsed yaml document. For e

        Args:
            id (str): [description]
            yaml_dict_path (list[str]): [description]

        Examples:
            Given a yaml file of the format:
            >>> pruner:
            >>>     fc_pruner:
            >>>         final_sparsity: 0.5

            To create a path to modify the value of 'final_sparsity' we use the function like so:
            >>> yamlEditor.add_modification_path('example', ['pruner', 'fc_pruner', 'final_sparsity'])

        """
        self.modification_dict[id] = yaml_dict_path

    def set_value_by_id(self, id, value):
        path = self.modification_dict.get(id)
        if path is not None:
            yaml_seek = self.yaml_object[path[0]]
            for p in path[1:-1]:
                yaml_seek = yaml_seek[p]

            yaml_seek[path[-1]] = value
        else:
            raise ValueError('Path ID is not valid')

    def write_yaml(self, file_name='schedule.yaml'):
        with open(file_name, 'w') as f:
            yaml.dump(self.yaml_object, f)
        return os.path.abspath(file_name)