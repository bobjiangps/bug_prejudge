import os
from utils.yaml_helper import YamlHelper


class Config:
    
    @classmethod
    def load(cls):
        env = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "env.yaml"))
        dbs = YamlHelper.load_yaml(os.path.join(os.getcwd(), "configuration", "database.yaml"))
        all_config = dict(env, **dbs)
        return all_config
