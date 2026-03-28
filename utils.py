import functools
import os
import re
from pathlib import Path
from urllib.parse import unquote

import markdown
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch

os.environ['NO_PROXY'] = '127.0.0.1,localhost'


def get_chat(model: str):
    import ollama
    return functools.partial(ollama.chat, model=model, stream=True, think=False)


dmp = diff_match_patch()


def diff(old: str, new: str) -> str:
    return unquote(dmp.patch_toText(dmp.patch_make(old, new)))


def markdown_to_text(markdown_string: str) -> str:
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def text_to_html(text: str) -> str:
    ps: list[str] = []
    for l in text.splitlines():
        p = l.strip()
        if p:
            ps.append(f"<p>{p}</p>")
    return "".join(ps)


def get_first_int(s: str) -> int:
    if match := re.search(r'\d+', s):
        return int(match.group())
    raise ValueError(f"{s} 中未找到整数")


def sorted_subdirs(path: Path) -> list[Path]:
    return sorted(path.glob('*/'), key=lambda x: get_first_int(x.name))
