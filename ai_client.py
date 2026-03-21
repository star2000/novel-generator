import os
import functools
os.environ['NO_PROXY'] = '127.0.0.1,localhost'

import ollama


def get_client(model:str):
    return functools.partial(ollama.chat, model=model, stream=True, think=False)
