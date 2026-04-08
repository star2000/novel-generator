from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

import utils as u

if TYPE_CHECKING:
    from typing import *  # type:ignore

    Message = dict[str, Any]


class NovelGenerator:
    def __init__(self, model: str, output_dir: str, user_input: str | None = None, book_name: str | None = None):
        self.chat = u.get_chat(model)
        self.output_dir = Path(output_dir)
        self.user_input = user_input
        self.book_name = book_name

    def exists(self, path_name: str) -> bool:
        '''检查文件是否存在'''
        return (self.book_output_dir / path_name).exists()

    def read_text(self, path_name: str) -> str:
        '''读取文件内容'''
        if not self.exists(path_name):
            return ''
        return f'<{path_name}>\n'+(self.book_output_dir / path_name).read_text(encoding='utf-8') + f'\n</{path_name}>'

    def generate(self, name: str, messages: list[Message]):
        '''生成内容'''
        stream = self.chat(messages)
        print('='*80)
        print(f'{name}：')
        content = ''
        for chunk in stream:
            content += chunk
            print(chunk, end='', flush=True)
        print()
        return content.strip()

    def generate_file(self, path_name: str, messages: list[Message]):
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
        stream = self.chat(messages+output_messages)
        print('='*80)
        print(f'生成 {path_name}：')
        content = ''
        for chunk in stream:
            content += chunk
            print(chunk, end='', flush=True)
        print('\n'+('='*80))
        path.write_text(content, encoding='utf-8')
        print(f'{path_name} 生成完成')
        return content

    def generate_book_name(self):
        '''根据用户要求生成书名'''
        self.book_name = self.generate('生成书名', [
            {'role': 'system', 'content': '你是一位专业的热门高质量网络小说作家'},
            {'role': 'user', 'content': f'要求：{self.user_input}\n\n起个热门网络小说名，仅回答一个，不使用符号'}
        ])

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
            {'role': 'system', 'content': '你是一位专业的热门高质量网络小说作家'},
            {'role': 'user', 'content': f'''\
《{self.book_name}》

要求：{self.user_input}

写设定集，需要定义起承转合之外的所有方面，以及有一定深度的各种人、事、物的名字和背景设定
'''}
        ])

    def generate_outline(self):
        '''生成总纲文件'''
        settings_content = self.read_text('设定集.md')

        self.generate_file('总纲.md', [
            {'role': 'system', 'content': '你是一位专业的热门高质量网络小说作家'},
            {'role': 'user', 'content': f'''\
《{self.book_name}》

要求：{self.user_input}

{settings_content}

写总纲，要细分成多个大卷，每个大卷按起承转合的结构来写'''}
        ])

    def generate_part_names(self):
        '''生成卷名列表'''
        outline_content = self.read_text('总纲.md')
        parts_str = self.generate_file('卷名.txt', [
            {'role': 'system',
                'content': '你是一个大卷卷名生成器，输出格式为每行一个，名字要精简优雅不重复，不使用符号'},
            {'role': 'user', 'content': outline_content}
        ])
        part_names = [
            f"第{i}卷-{part_name}"
            for i, part_name in enumerate((
                n.strip('《》') for n in parts_str.splitlines()
                if n and '卷名' not in n), 1)
        ]
        return part_names

    def generate_part_outline(self, part_name):
        '''生成卷大纲文件'''
        path_name = f'{part_name}/大纲.md'
        settings_content = self.read_text('设定集.md')
        outline_content = self.read_text('总纲.md')
        self.generate_file(path_name, [
            {'role': 'system', 'content': '你是一位专业的热门高质量网络小说作家'},
            {'role': 'user', 'content': f'''\
{settings_content}

{outline_content}

写卷大纲，要细分成多个剧情单元，每个剧情单元按起承转合的结构来写，剧情单元的每个阶段要有描述和章节数量规划'''}
        ])

    def generate_chapter_names(self, part_name: str):
        '''生成章节名列表'''
        part_outline_content = self.read_text(f'{part_name}/大纲.md')
        chapters_str = self.generate_file(f'{part_name}/章名.txt', [
            {'role': 'system',
                'content': '你是一个章节章名生成器，输出格式为每行一个，名字要精简优雅不重复，不使用符号'},
            {'role': 'user', 'content': part_outline_content}
        ])
        chapter_names = [
            f"第{i}章-{chapter_name}"
            for i, chapter_name in enumerate((
                n.strip('《》') for n in chapters_str.splitlines()
                if n and '章名' not in n), 1)
        ]
        return chapter_names

    def get_prev_chapter_dir(self, part_name: str, chapter_name: str) -> Path | None:
        '''获取前一章的目录'''
        part_num = u.get_first_int(part_name)
        chapter_num = u.get_first_int(chapter_name)
        if chapter_num == 1:
            if part_num == 1:
                return None
            # 找上一卷的最后一章
            prev_part_dir = next(
                self.book_output_dir.glob(f'第{part_num - 1}卷-*/'))
            prev_chapters = list(
                (self.book_output_dir / prev_part_dir.name).glob('*/'))
            return max(prev_chapters, key=lambda x: u.get_first_int(x.name))
        return next((self.book_output_dir / part_name).glob(f'第{chapter_num-1}章-*/'))

    def generate_chapter_outline(self, part_name: str, chapter_name: str):
        '''生成章节大纲文件'''
        path_name = f'{part_name}/{chapter_name}/大纲.md'
        if self.exists(path_name):
            return
        settings_content = self.read_text('设定集.md')
        part_outline_content = self.read_text(f'{part_name}/大纲.md')
        prev_content = ''
        if prev_chapter_dir := self.get_prev_chapter_dir(part_name, chapter_name):
            if prev_chapter_outline_content := self.read_text(str(prev_chapter_dir / '大纲.md')):
                prev_content += f'\n\n{prev_chapter_outline_content}'
        self.generate_file(path_name, [
            {'role': 'system',
                'content': '你是一位专业的热门高质量网络小说作家'},
            {'role': 'user', 'content': f'''
{settings_content}

{prev_content}

{part_outline_content}

写章节大纲，要细分成多个小节，每个小节按起承转合的结构来写'''}
        ])

    def generate_chapter_content(self, part_name: str, chapter_name: str):
        '''生成章节正文文件'''
        path_name = f'{part_name}/{chapter_name}/正文.md'
        if not self.exists(path_name):
            settings_content = self.read_text('设定集.md')
            chapter_outline_content = self.read_text(
                f'{part_name}/{chapter_name}/大纲.md')
            self.generate_file(path_name, [
                {'role': 'system', 'content': '你是一位专业的热门高质量网络小说作家'},
                {'role': 'user', 'content': f'{settings_content}\n\n{chapter_outline_content}'}
            ])
        content = (self.book_output_dir /
                   path_name).read_text(encoding='utf-8')
        cleaned_path = self.book_output_dir / path_name.replace('.md', '.txt')
        only_chapter_name = chapter_name.split('-', 1)[1]
        only_part_name = part_name.split('-', 1)[1]
        while True:
            if cleaned_path.exists():
                cleaned_content = cleaned_path.read_text(encoding='utf-8')
            else:
                stream = self.chat([
                    {'role': 'system',
                        'content': '你是一个小说正文洗稿器，正文开头不应该出现第几章第几卷，结尾不应该明说本章完，其余必须保持原样'},
                    {'role': 'user', 'content': content}
                ])
                cleaned_content = ''
                print(f'洗稿 {path_name}')
                for chunk in stream:
                    cleaned_content += chunk
                    print(chunk, end='', flush=True)
                print()
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
    parser.add_argument('--model', '-m', type=str, default='qw', help='模型名称')
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
