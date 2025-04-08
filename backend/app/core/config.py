# PATH: backend/app/core/config.py

import os
from functools import lru_cache

class Config:
    def __init__(self):
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypass")
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "mydatabase")

    def get_connection_string(self):
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

@lru_cache()
def get_config():
    return Config()
