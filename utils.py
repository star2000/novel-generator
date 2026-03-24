import functools
import os
import re
from urllib.parse import unquote

from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
import markdown

os.environ['NO_PROXY'] = '127.0.0.1,localhost'



def get_client(model:str, stream=True, think=False):
    import ollama
    return functools.partial(ollama.chat, model=model, stream=stream, think=think)


dmp = diff_match_patch()

def diff(old: str, new: str) -> str:
    return unquote(dmp.patch_toText(dmp.patch_make(old, new)))


def markdown_to_text(markdown_string: str) -> str:
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()
