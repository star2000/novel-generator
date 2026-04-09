import os

os.environ['NO_PROXY'] = '127.0.0.1,localhost'  # noqa

import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import markdown
import ollama
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
from modelscope import AutoTokenizer
from rich.console import Console as RichConsole
from rich.live import Live as RichLive
from rich.markdown import Markdown as RichMarkdown
from rich.panel import Panel as RichPanel
from rich.traceback import install as rich_traceback_install

console = RichConsole()

rich_traceback_install(console=console, show_locals=True)

tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3.5-4B')


def get_num_ctx(text: str) -> int:
    token_count = len(tokenizer.encode(text))
    num_ctx = 2**max(15, min(18, math.ceil(math.log2(token_count))))
    return num_ctx


class Chat:
    def __init__(self, model: str):
        self.model = model
        self.client = ollama.Client()

    def __call__(self, messages: list[dict[str, Any]], title: str | None = None) -> str:
        num_ctx = get_num_ctx('\n'.join(m['content'] for m in messages))
        stream = self.client.chat(
            self.model, messages, stream=True, think=False, options={'num_ctx': num_ctx})
        content = ''
        with RichLive(console=console, vertical_overflow='visible') as live:
            for chunk in stream:
                if chunk.message.content:
                    content += chunk.message.content
                    live.update(RichPanel(RichMarkdown(content), title=title))
        return content.strip()


def get_chat(model: str):
    return Chat(model)


dmp = diff_match_patch()


def diff(old: str, new: str) -> str:
    return unquote(dmp.patch_toText(dmp.patch_make(old, new)))


def markdown_to_text(markdown_string: str) -> str:
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def text_to_html(text: str) -> str:
    ps: list[str] = []
    for l in text.splitlines():
        p = l.strip()
        if p:
            ps.append(f'<p>{p}</p>')
    return ''.join(ps)


def get_first_int(s: str) -> int:
    if match := re.search(r'\d+', s):
        return int(match.group())
    raise ValueError(f'{s} 中未找到整数')


def sorted_subdirs(path: Path) -> list[Path]:
    return sorted(path.glob('*/'), key=lambda x: get_first_int(x.name))
