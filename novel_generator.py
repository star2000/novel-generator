from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

import utils as u

if TYPE_CHECKING:
    from typing import *  # type:ignore

    Message = dict[str, Any] | u.Message


class NovelGenerator:
    def __init__(self, model: str, output_dir: str, user_input: str | None = None, book_name: str | None = None):
        self.chat = u.Chat(model, '''\
你是一位专业的热门高质量网络小说作家。
小说结构：设定集、总纲、卷大纲、章节大纲、正文。
核心守则：
1. **节奏即生命线**：开局三章定生死，每章必留钩子，精准卡位爽点/悬念，零注水。
2. **人设驱动剧情**：主角有明确目标与成长弧光，配角有独立动机与功能，情感真实不脸谱化。
3. **死守类型公约数**：严格匹配赛道核心期待，在框架内做细节/视角/规则微创新。
4. **设定自洽且服务叙事**：世界观逻辑严密不崩盘，规则清晰可执行，关键细节留白供读者脑补。
5. **行文克制高效**：白描为主，段落短平快；对话推进剧情，拒用无效描写与辞藻堆砌。
''')
        self.output_dir = Path(output_dir)
        self.user_input = user_input
        self.book_name = book_name

    def exists(self, path_name: str) -> bool:
        '''检查文件是否存在'''
        return (self.book_output_dir / path_name).exists()

    def get_true_text(self, path_name: str) -> str:
        '''获取真实文件内容'''
        if not self.exists(path_name):
            return ''
        return (self.book_output_dir / path_name).read_text(encoding='utf-8')

    def read_text(self, path_name: str) -> str:
        '''读取文件内容'''
        if text := self.get_true_text(path_name):
            return f'<{path_name}>\n' + text + f'\n</{path_name}>'
        return ''

    def generate_file(self, path_name: str, messages: list[Message], think: bool = False):
        '''生成文件'''
        path = self.book_output_dir / path_name
        if path.exists():
            print(f'{path_name} 已存在，跳过生成')
            return path.read_text(encoding='utf-8')
        output_messages = [{
            'role': 'user',
            'content': f'请只用中文生成 {path_name} 的内容'
        }]
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.chat(messages+output_messages, path_name, think=think)
        path.write_text(content, encoding='utf-8')
        return content

    def generate_book_name(self):
        '''根据用户要求生成书名'''
        self.book_name = self.chat([
            {'role': 'user', 'content': f'要求：{self.user_input}\n\n起个书名，仅回答一个，不使用符号'}
        ], '生成书名')

    def setup_book_output_dir(self):
        '''设置小说根目录'''
        assert self.book_name
        self.book_output_dir = self.output_dir / self.book_name
        self.book_output_dir.mkdir(parents=True, exist_ok=True)

    def save_user_input(self, user_input: str | None = None):
        '''保存用户输入'''
        user_input = user_input or self.user_input
        f = self.book_output_dir / '要求.md'
        if user_input is None:
            self.user_input = f.read_text(encoding='utf-8')
        else:
            f.write_text(user_input, encoding='utf-8')
            self.user_input = user_input

    def generate_settings(self):
        '''生成设定集文件'''
        self.generate_file('设定集.md', [
            {'role': 'user', 'content': f'''\
《{self.book_name}》

要求：{self.user_input}

写设定集，需要定义剧情大纲之外的所有方面，要有一定深度的各种人、事、物的名字和背景设定，立住人设，深化情感内核，用于生成大纲
'''}
        ])

    def generate_outline(self):
        '''生成总纲文件'''
        settings_content = self.read_text('设定集.md')

        self.generate_file('总纲.md', [
            {'role': 'user', 'content': f'''\
《{self.book_name}》

要求：{self.user_input}

{settings_content}
'''}
        ])

    def generate_part_names(self):
        '''生成卷名列表'''
        outline_content = self.read_text('总纲.md')
        parts_str = self.generate_file('卷名.txt', [
            u.Message(role='system',
                      content='根据用户输入生成不重复的卷名，每行一个，仅输出卷名，不包含编号，不包含符号'),
            u.Message(role='user', content=outline_content),
        ])
        part_names = [
            f"第{i}卷-{part_name}"
            for i, part_name in enumerate((n for n in parts_str.splitlines() if n), 1)
        ]
        return part_names

    def get_novel_part_outline(self, max_tokens: int = 20000) -> str:
        contents: list[str] = []
        tokens = 0
        parts = u.sorted_subdirs(self.book_output_dir)
        parts.reverse()
        for part in parts:
            f = part / '大纲.md'
            if f.exists():
                name = f'{part.name} / 大纲'
                text = f.read_text(encoding='utf-8')
                content = f'<{name}>\n' + text + f'\n</{name}>\n'
                t = u.get_num_ctx(content)
                if t + tokens > max_tokens:
                    break
                contents.insert(0, content)
                tokens += t
        return ''.join(contents)

    def generate_part_outline(self, part_name):
        '''生成卷大纲文件'''
        path_name = f'{part_name}/大纲.md'
        novel_part_outline = self.get_novel_part_outline()
        part_names = self.read_text('卷名.txt')
        settings_content = self.read_text('设定集.md')
        outline_content = self.read_text('总纲.md')
        self.generate_file(path_name, [
            {'role': 'user', 'content': f'''\
{novel_part_outline}

{settings_content}

{outline_content}

{part_names}
'''}
        ])

    def generate_chapter_names(self, part_name: str):
        '''生成章节名列表'''
        part_outline_content = self.read_text(f'{part_name}/大纲.md')
        chapters_str = self.generate_file(f'{part_name}/章名.txt', [
            u.Message(role='system',
                      content='根据用户输入生成不重复的章名，每行一个，仅输出章名，不包含编号，不包含符号'),
            u.Message(role='user', content=part_outline_content),
        ])
        chapter_names = [
            f"第{i}章-{chapter_name}"
            for i, chapter_name in enumerate((n for n in chapters_str.splitlines() if n), 1)
        ]
        return chapter_names

    def get_novel_chapter_outline(self, max_tokens: int = 20000) -> str:
        contents: list[str] = []
        tokens = 0
        parts = u.sorted_subdirs(self.book_output_dir)
        parts.reverse()
        for part in parts:
            chapters = u.sorted_subdirs(part)
            chapters.reverse()
            for chapter in chapters:
                f = chapter / '大纲.md'
                if f.exists():
                    name = f'{part.name} / {chapter.name} / 大纲'
                    text = f.read_text(encoding='utf-8')
                    content = f'<{name}>\n' + text + f'\n</{name}>\n'
                    t = u.get_num_ctx(content)
                    if t + tokens > max_tokens:
                        break
                    contents.insert(0, content)
                    tokens += t
        return ''.join(contents)

    def generate_chapter_outline(self, part_name: str, chapter_name: str):
        '''生成章节大纲文件'''
        path_name = f'{part_name}/{chapter_name}/大纲.md'
        if self.exists(path_name):
            return
        novel_chapter_outline = self.get_novel_chapter_outline()
        settings_content = self.read_text('设定集.md')
        part_outline_content = self.read_text(f'{part_name}/大纲.md')
        chapter_names = self.read_text(f'{part_name}/章名.txt')
        self.generate_file(path_name, [
            {'role': 'user', 'content': f'''
{novel_chapter_outline}

{settings_content}

{part_outline_content}

{chapter_names}
'''}
        ])

    def get_novel_text(self, max_tokens: int = 20000) -> str:
        contents: list[str] = []
        tokens = 0
        parts = u.sorted_subdirs(self.book_output_dir)
        parts.reverse()
        for part in parts:
            chapters = u.sorted_subdirs(part)
            chapters.reverse()
            for chapter in chapters:
                f = chapter / '正文.txt'
                if f.exists():
                    name = f'{part.name} / {chapter.name}'
                    text = f.read_text(encoding='utf-8')
                    content = f'<{name}>\n' + text + f'\n</{name}>\n'
                    t = u.get_num_ctx(content)
                    if t + tokens > max_tokens:
                        break
                    contents.insert(0, content)
                    tokens += t
        return ''.join(contents)

    def generate_chapter_content(self, part_name: str, chapter_name: str):
        '''生成章节正文文件'''
        path_name = f'{part_name}/{chapter_name}/正文.md'
        if not self.exists(path_name):
            novel_text = self.get_novel_text()
            settings_content = self.read_text('设定集.md')
            chapter_outline_content = self.read_text(
                f'{part_name}/{chapter_name}/大纲.md')
            self.generate_file(path_name, [
                {'role': 'user', 'content': f'''\
{novel_text}

{settings_content}

{chapter_outline_content}'''}
            ])
        content = self.get_true_text(path_name)
        cleaned_path = self.book_output_dir / path_name.replace('.md', '.txt')
        only_chapter_name = chapter_name.split('-', 1)[1]
        only_part_name = part_name.split('-', 1)[1]
        while True:
            if cleaned_path.exists():
                cleaned_content = cleaned_path.read_text(encoding='utf-8')
            else:
                cleaned_content = self.chat([
                    {'role': 'system',
                        'content': '你是一个小说正文洗稿器，正文开头不应该出现第几章第几卷，结尾不应该明说本章完，其余必须保持原样'},
                    {'role': 'user', 'content': content}
                ], f'洗稿 {path_name}')
                cleaned_content = u.markdown_to_text(cleaned_content)
                cleaned_path.write_text(cleaned_content, encoding='utf-8')
            if only_chapter_name in cleaned_content and only_part_name in cleaned_content:
                cleaned_path.unlink()
                continue
            break
        diff_path = self.book_output_dir / path_name.replace('.md', '.diff')
        if not diff_path.exists():
            raw_content = u.markdown_to_text(content)
            cleaned_content = cleaned_path.read_text(encoding='utf-8')
            diff_text = u.diff(raw_content, cleaned_content)
            diff_path.write_text(diff_text, encoding='utf-8')

    def run(self):
        '''运行小说生成流程'''
        # 1. 获取用户输入
        if self.user_input is None and self.book_name is None:
            self.user_input = input('请输入小说生成要求：')

        # 2. 生成书名并设置根目录
        if self.book_name is None:
            self.generate_book_name()

        self.setup_book_output_dir()

        self.save_user_input()

        # 3. 生成设定集和总纲
        self.generate_settings()
        self.generate_outline()

        # 4. 开始生成各卷内容
        for part_name in self.generate_part_names():
            # 创建卷大纲
            self.generate_part_outline(part_name)

            # 生成章节
            for chapter_name in self.generate_chapter_names(part_name):
                # 生成章节大纲
                self.generate_chapter_outline(part_name, chapter_name)

                # 生成章节正文
                self.generate_chapter_content(part_name, chapter_name)

        print(f'小说《{self.book_name}》生成完成')


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='小说生成器')
    parser.add_argument('--model', '-m', type=str,
                        default='qwen3.5:4b', help='模型名称')
    parser.add_argument('--book-name', '-n', type=str, help='小说书名')
    parser.add_argument('--user-input', '-i', type=str, help='小说生成要求')
    parser.add_argument('--output-dir', '-o', type=str,
                        default='./dist/', help='输出目录路径')
    args = parser.parse_args()

    # 初始化生成器
    generator = NovelGenerator(
        model=args.model,
        output_dir=args.output_dir,
        user_input=args.user_input,
        book_name=args.book_name,
    )

    # 运行生成流程
    generator.run()
