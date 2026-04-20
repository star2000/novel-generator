import os

os.environ['NO_PROXY'] = '127.0.0.1,localhost'  # noqa

import math
import re
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence, TypeVar
from urllib.parse import unquote

import markdown
import ollama
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
from pydantic import model_validator
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

tokenizer = None


def get_num_ctx(text: str, num_predict: int = 0) -> int:
    global tokenizer
    if tokenizer is None:
        from modelscope import AutoTokenizer
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                'Qwen/Qwen3.5-4B', local_files_only=True)
        except:
            tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3.5-4B')
    token_count = len(tokenizer.encode(text))
    num_ctx = 2**max(15, min(18, math.ceil(math.log2(token_count+num_predict))))
    return num_ctx


T = TypeVar("T")


def loop_last(values: Iterable[T]) -> Iterable[tuple[bool, T]]:
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


def is_repeated(text: str):
    return re.search(r'([\s\S]{2,1000})\1\1', text)


class Message(ollama.Message):
    @model_validator(mode='after')
    def validate_role(self):
        if self.role not in ['assistant', 'system', 'user']:
            self.content = f"{self.role}: {self.content or ''}"
            self.role = 'user'
        return self


ThinkType = bool | Literal['low', 'medium', 'high'] | None


class Chat:
    def __init__(self, model: str, system_prompt: str | None = None, think: ThinkType = False):
        self.model = model
        self.client = ollama.Client()
        self.system_prompt = system_prompt
        self.think: ThinkType = think

    def __call__(
            self,
            messages: Sequence[dict[str, Any] | Message],
            title: str | None = None,
            think: ThinkType = None,
            format: dict[str, Any] | Literal['', 'json'] | None = None,
            num_predict: int = 5000,
    ) -> str:
        if self.system_prompt:
            if not any(m['role'] == 'system' for m in messages):
                messages = [
                    Message(role='system', content=self.system_prompt),
                ] + list(messages)
        if think is None:
            think = self.think
        if think:
            num_predict += 10000
        is_markdown = title and title.endswith('.md')
        with RichLive(console=console, vertical_overflow='visible') as live:
            live.update(RichPanel('', title=title))
            num_ctx = get_num_ctx(
                '\n'.join(m['content'] for m in messages), num_predict)
            while True:
                content = ''
                think_text = ''
                stream = self.client.chat(
                    self.model, messages, stream=True, think=think, format=format, options={
                        'num_ctx': num_ctx,
                        'num_predict': num_predict,
                    })
                for chunk in stream:
                    if chunk.message.thinking:
                        think_text += chunk.message.thinking
                        live.update(
                            RichPanel(RichTail(RichMarkdown(think_text)), title=title))
                    elif chunk.message.content:
                        content += chunk.message.content
                        live.update(RichPanel(RichTail(RichMarkdown(content)
                                                       if is_markdown else content), title=title))
                        if is_repeated(content):
                            break
                else:
                    break
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
