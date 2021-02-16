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

    def add_modification_path(self, id, list_path_to_rule):
        self.modification_dict[id] = list_path_to_rule

    def set_value_by_id(self, id, value):
        path = self.modification_dict.get(id)
        if path is not None:
            yaml_seek = self.yaml_object[path[0]]
            for p in path[1:-1]:
                yaml_seek = yaml_seek[p]

            yaml_seek[path[-1]] = value
        else:
            raise ValueError('Rule ID is not valid')