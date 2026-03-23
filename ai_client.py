import functools
import os

os.environ['NO_PROXY'] = '127.0.0.1,localhost'



def get_client(model:str):
    import ollama
    return functools.partial(ollama.chat, model=model, stream=True, think=False)
