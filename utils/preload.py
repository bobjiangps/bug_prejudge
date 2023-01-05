from pathlib import Path
from utils.singleton import Singleton
from sights.lib.visual.experiment import load
import torch


class PreLoad(Singleton):

    def __init__(self):
        self._path = Path.cwd().joinpath("static", "data_models")
        self.models = {}
        self._exclude = ["demo", "ocr"]

    def activate(self):
        for p in Path(self._path).iterdir():
            if p.is_dir():
                folder = p.parts[-1]
                if folder not in self._exclude:
                    for f in p.glob("*.pt"):
                        self.models[folder] = {f.parts[-1].split(".")[0]: load(str(f), map_location=torch.device("cpu"))}
        return self.models
