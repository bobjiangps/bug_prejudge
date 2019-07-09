import os
from utils.yaml_helper import YamlHelper


class Config:
    
    @classmethod
    def load_all(cls):
        env = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "env.yaml"))
        dbs = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "database.yaml"))
        all_config = dict(env, **dbs)
        return all_config

    @classmethod
    def load_db(cls):
        dbs = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "database.yaml"))
        return dbs

    @classmethod
    def load_env(cls):
        env = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "env.yaml"))
        return env
