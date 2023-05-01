from dataclasses import dataclass

from environs import Env

env = Env()
env.read_env(".env")


@dataclass
class Config:
    threshold: float


thr = env.float("THRESHOLD")
cfg = Config(threshold=thr)
