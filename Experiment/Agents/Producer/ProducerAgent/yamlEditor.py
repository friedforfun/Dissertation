import os
import yaml

from AgentBase.Utils.Logging import logger
from AgentBase.Utils.MiscParsing import str_to_type
# Read YAML file
# Select params to modify
# write copy with modified params

# send message with location of modified yaml file

class YamlBase:
    def __init__(self, yaml_path):
        self.yaml_path = yaml_path
        self.yaml_object = self.read_yaml()

    def read_yaml(self):
        with open(self.yaml_path) as f:
            return yaml.load(f)

    def print(self):
        print(self.yaml_object)

    def write_yaml(self, file_name='schedule.yaml'):
        with open(file_name, 'w') as f:
            yaml.dump(self.yaml_object, f)
        return os.path.abspath(file_name)

class YamlEditor(YamlBase):
    def __init__(self, yaml_path):
        super().__init__(yaml_path)
        self.modification_dict = {}

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




class YamlEditorBuilder(YamlBase):
    def __init__(self, yaml_spec):
        """Used to build a YamlEditor using a yaml spec file, the spec file should contain keys that will represent the identifier for the yaml editor, and the values should be a list that represents a path through the schedule to the value.

        Examples:
            Given a schedule:
            >>> pruner:
            >>>     fc_pruner:
            >>>         final_sparsity: 0.5

            If we call the parameter in this schedule 'fc_pruner', and want to modify the float value of 'final_sparsity', add the following to the spec file:
            >>> fc_pruner:
            >>>     type: 'float' 
            >>>     path: ['pruner', 'fc_pruner', 'final_sparsity']

        """
        super().__init__(yaml_spec)
        self.editor = None

    def get_editor(self, yaml_schedule):
        """Creates a YamlEditor and using the already stored yaml spec builds up all the modification paths.

        Args:
            yaml_schedule (str): Path to the schedule to pass into YamlEditor constructor

        Raises:
            ValueError: No path found for a key

        Returns:
            YamlEditor: The YamlEditor object with all paths added
        """
        self.editor = YamlEditor(yaml_schedule)
        # ... add all modification paths
        for k,v in self.yaml_object.items():
            if k != 'version':
                assert type(k) == str

                path = v.get('path')
                if path is not None:
                    assert type(path) == list
                    assert type(path[0]) == str
                    self.editor.add_modification_path(k, path)
                else:
                    raise ValueError('YamlBuilder: missing path from yaml - Each Identifier should have a path')
        return self.editor

    def get_args(self, arg_parser):
        """Read the yaml spec file and build all the relevant arg parse args

        Args:
            arg_parser (ArgumentParser): An argparse.ArgumentParser

        Returns:
            ArgumentParser: The argument parser with all args added
        """
        args = arg_parser.add_argument_group('scheduler args')

        for k,v in self.yaml_object.items():
            if k != 'version':
                assert type(k) == str
                type_annotation = v.get('type')
                if type_annotation is not None:
                    args.add_argument('--{}'.format(k), type=str_to_type(type_annotation))
        return arg_parser

        

    
