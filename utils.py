import os
from typing import TypeVar

os.environ['NO_PROXY'] = '127.0.0.1,localhost'  # noqa

import math
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

import markdown
import ollama
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
from modelscope import AutoTokenizer
from rich.console import Console as RichConsole
from rich.console import ConsoleOptions as RichConsoleOptions
from rich.console import RenderableType as RichRenderableType
from rich.console import RenderResult as RichRenderResult
from rich.live import Live as RichLive
from rich.markdown import Markdown as RichMarkdown
from rich.panel import Panel as RichPanel
from rich.segment import Segment as RichSegment
from rich.traceback import install as rich_traceback_install

console = RichConsole()

rich_traceback_install(console=console)

tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3.5-4B')


def get_num_ctx(text: str, delta_tokens: int = 0) -> int:
    token_count = len(tokenizer.encode(text))
    num_ctx = 2**max(15,
                     min(18, math.ceil(math.log2(token_count+delta_tokens))))
    return num_ctx


T = TypeVar("T")


def loop_last(values: Iterable[T]) -> Iterable[tuple[bool, T]]:
    """Iterate and generate a tuple with a flag for last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    for value in iter_values:
        yield False, previous_value
        previous_value = value
    yield True, previous_value


class RichTail:
    def __init__(
        self,
        renderable: RichRenderableType,
    ):
        self.renderable = renderable

    def __rich_console__(self, console: RichConsole, options: RichConsoleOptions) -> RichRenderResult:
        lines = console.render_lines(self.renderable, options, pad=False)
        lines = lines[-options.size.height//2:]
        new_line = RichSegment.line()
        for last, line in loop_last(lines):
            yield from line
            if not last:
                yield new_line


class Chat:
    def __init__(self, model: str, system_prompt: str | None = None):
        self.model = model
        self.client = ollama.Client()
        self.system_prompt = system_prompt

    def __call__(self, messages: list[dict[str, Any]], title: str | None = None, think: bool = False) -> str:
        if self.system_prompt:
            messages = [
                {'role': 'system', 'content': self.system_prompt},
            ] + messages
        num_ctx = get_num_ctx('\n'.join(m['content'] for m in messages), 5000)
        stream = self.client.chat(
            self.model, messages, stream=True, think=think, options={
                'num_ctx': num_ctx,
                'penalty_last_n': -1,
                'repeat_penalty': 1.5,
                'frequency_penalty': 0.5,
            })
        is_markdown = title and title.endswith('.md')
        content = ''
        think_text = ''
        with RichLive(console=console, vertical_overflow='visible') as live:
            live.update(RichPanel('', title=title))
            for chunk in stream:
                if chunk.message.thinking:
                    think_text += chunk.message.thinking
                    live.update(
                        RichPanel(RichTail(RichMarkdown(think_text)), title=title))
                elif chunk.message.content:
                    content += chunk.message.content
                    live.update(RichPanel(RichTail(RichMarkdown(content)
                                                   if is_markdown else content), title=title))
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
