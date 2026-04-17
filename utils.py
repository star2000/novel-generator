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

rich_traceback_install(console=console)

tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3.5-4B')


def get_num_ctx(text: str, delta_tokens: int = 0) -> int:
    token_count = len(tokenizer.encode(text))
    num_ctx = 2**max(15,
                     min(18, math.ceil(math.log2(token_count+delta_tokens))))
    return num_ctx


class Chat:
    def __init__(self, model: str, system_prompt: str | None = None):
        self.model = model
        self.client = ollama.Client()
        self.system_prompt = system_prompt

    def __call__(self, messages: list[dict[str, Any]], title: str | None = None) -> str:
        if self.system_prompt:
            messages = [
                {'role': 'system', 'content': self.system_prompt},
            ] + messages
        num_ctx = get_num_ctx('\n'.join(m['content'] for m in messages), 5000)
        stream = self.client.chat(
            self.model, messages, stream=True, think='low', options={'num_ctx': num_ctx})
        is_markdown = title and title.endswith('.md')
        content = ''
        think_text = ''
        with RichLive(console=console, vertical_overflow='visible') as live:
            for chunk in stream:
                if chunk.message.thinking:
                    think_text += chunk.message.thinking
                    live.update(
                        RichPanel(RichMarkdown(think_text), title=title))
                elif chunk.message.content:
                    content += chunk.message.content
                    live.update(RichPanel(RichMarkdown(content)
                                          if is_markdown else content, title=title))
        return content.strip()


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
