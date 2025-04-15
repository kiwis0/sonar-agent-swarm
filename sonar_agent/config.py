import os

def get_config(key, fallback=None):
    return os.getenv(key.upper(), fallback)