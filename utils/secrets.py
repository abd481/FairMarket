import os
from inspect import isawaitable
from dotenv import load_dotenv

load_dotenv()


def _resolve(value):
    if not isawaitable(value):
        return value

    from prefect.utilities.asyncutils import run_coro_as_sync

    return run_coro_as_sync(value)


def get_secret(env_key: str, block_name: str) -> str:
    value = os.getenv(env_key)
    if value:
        return value
    from prefect.blocks.system import Secret

    secret = _resolve(Secret.load(block_name))
    return _resolve(secret.get())
