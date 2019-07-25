from utils.yaml_helper import YamlHelper
import os
import argparse


class Config:
    
    @classmethod
    def load_all(cls):
        env = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "env.yaml"))
        dbs = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "database.yaml"))
        all_config = dict(env, **dbs)
        return all_config

    @classmethod
    def load_db(cls, name=None):
        if name:
            return YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "database.yaml"))[name]
        else:
            return YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "database.yaml"))

    @classmethod
    def load_env(cls, name=None):
        if name:
            return YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "env.yaml"))[name]
        else:
            return YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "env.yaml"))


class CommandParser:

    @classmethod
    def args(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument("-tr", "--round_id", type=int)
        parser.add_argument("-ts", "--script_id", type=int)
        parser.add_argument("-tc", "--case_id", type=int)
        args = parser.parse_args()
        return args
