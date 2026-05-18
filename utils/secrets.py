import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(env_key: str, block_name: str) -> str:
    value = os.getenv(env_key)
    if value:
        return value
    from prefect.blocks.system import Secret
    return Secret.load(block_name).get()