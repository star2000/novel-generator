from __future__ import annotations
import argparse
from pathlib import Path
import re
from typing import TYPE_CHECKING

from ai_client import get_client

if TYPE_CHECKING:
    import ollama


class NovelGenerator:
    def __init__(self, model:str, output_dir:str, user_input:str|None=None, book_name:str|None=None):
        self.client = get_client(model)
        self.output_dir = Path(output_dir)
        self.user_input = user_input
        self.book_name = book_name

    def exists(self, path_name: str) -> bool:
        """检查文件是否存在"""
        return (self.book_output_dir / path_name).exists()

    def read_text(self, path_name: str) -> str:
        """读取文件内容"""
        if not self.exists(path_name):
            return ''
        return f'{path_name}：'+(self.book_output_dir / path_name).read_text(encoding="utf-8")

    def generate(self, name: str, messages: list[ollama.Message]):
        '''生成内容'''
        stream = self.client(messages=messages)
        print('='*80)
        print(f"{name}：")
        content = ''
        for chunk in stream:
            print(chunk.message.content, end="", flush=True)
            content += chunk.message.content
        print()
        return content.strip()

    def generate_file(self, path_name: str, messages: list[ollama.Message]):
        '''生成文件'''
        path = self.book_output_dir / path_name
        if path.exists():
            print(f"{path_name} 已存在，跳过生成")
            return
        output_messages = [{
            'role':'user',
            'content':f"请只用中文生成 {path_name} 的内容"
        }]
        path.parent.mkdir(parents=True, exist_ok=True)
        settings_content = self.read_text("设定集.txt")
        fix_messages:list[ollama.Message] = []
        while True:
            stream = self.client(messages=messages+fix_messages+output_messages)
            print('='*80)
            print(f"生成 {path_name}：")
            content = ''
            for chunk in stream:
                content += chunk.message.content
                print(chunk.message.content, end="", flush=True)
            print()
            # 对正文，用ai洗稿，删除首尾可能存在的第几部第几章和本章完之类的与小说正文无关的内容
            if '正文.' in path_name:
                content = self.generate(f'洗稿 {path_name}', [
                    {"role": "system", "content": "你是一个小说正文洗稿器，根据用户输入的小说正文，删除首尾可能存在的第几部第几章和本章完之类的与小说正文无关的内容，然后输出洗稿后的文本。"},
                    {"role": "user", "content": content}
                ])
            check = self.generate(f'检查 {path_name}', [
                {"role": "system", "content": "你是一个资深的小说审稿人，根据设定集，对用户的输入文本的各方面做出评价和评分（1-10分），并提出优化建议，如无建议输出'无需优化'"},
                {"role": "user", "content": f"{settings_content}\n\n{path_name}：{content}"}
            ])
            if '无需优化' not in check:
                print(f"{path_name} 检查发现还不完美，重新生成")
                fix_messages=[{
                    'role':'assistant',
                    'content':content
                },{
                    'role':'user',
                    'content':f"{check}\n\n请重新生成"
                }]
                continue
            break
        path.write_text(content, encoding="utf-8")
        print(f"{path_name} 生成完成")


    def get_user_input(self):
        """获取用户输入的小说要求"""
        self.user_input = input("请输入小说生成要求：")

    def generate_book_name(self):
        """根据用户要求生成书名"""
        self.book_name = self.generate('生成书名', [
            {"role": "system", "content": "你是一个专业的小说书名生成器，根据用户的输入，仅生成一个最合适的书名，书名要优雅、简介、符合用户要求，不能包含任何额外的内容和符号。"},
            {"role": "user", "content": f"{self.user_input}"}
        ])
    
    def setup_book_output_dir(self):
        """设置小说根目录"""
        self.book_output_dir = self.output_dir / self.book_name
        self.book_output_dir.mkdir(parents=True, exist_ok=True)

    def generate_outline(self):
        """生成总纲文件"""
        self.generate_file("总纲.txt", [
            {"role": "system", "content": "你是一个专业的小说总纲生成器，根据用户的要求生成小说的总纲，包括有多少部以及每一部的大致内容。仅输出总纲内容，不包含任何额外的内容和符号。"},
            {"role": "user", "content": f"《{self.book_name}》\n\n要求：{self.user_input}"}
        ])

    def generate_total_part_num(self):
        """根据总纲生成总部数"""
        outline_content = self.read_text("总纲.txt")
        return int(self.generate('生成最大部数', [
            {"role": "system", "content": "你是一个小说部数计数器，根据总纲，仅输出阿拉伯数字格式的最大部数，不包含任何额外的内容和符号。"},
            {"role": "user", "content": outline_content}
        ]))
    
    def generate_settings(self):
        """生成设定集文件"""
        outline_content = self.read_text("总纲.txt")
        self.generate_file("设定集.txt", [
            {"role": "system", "content": "你是一个专业的小说设定集生成器，根据小说总纲写各种设定，比如世界背景、主角（至少13个）、配角（至少26个）、地点、事件、势力，这些都要有完善的背景和细节，以及每个事件都要标注发生时间，主角和配角都要有足够的人物深度"},
            {"role": "user", "content": f"《{self.book_name}》\n\n要求：{self.user_input}\n\n{outline_content}"}
        ])

    def generate_part_name(self, part_num: int) -> str:
        """根据部号生成部名"""
        if dir := next(self.book_output_dir.glob(f"第{part_num}部-*"), None):
            return dir.name
        outline_content = self.read_text("总纲.txt")
        part_name = self.generate(f'生成第{part_num}部-部名', [
            {"role": "system", "content": "你是一个专业的小说部名生成器，根据总纲生成该部的名称。仅输出部名，不包含任何额外的内容和符号。"},
            {"role": "user", "content": f"{outline_content}\n\n为第{part_num}部生成名称，仅输出部名，不包含部号，不包含第几部："}
        ])
        return f"第{part_num}部-{part_name}"
 
    def generate_part_outline(self, part_name):
        """生成部大纲文件"""
        path_name = f"{part_name}/大纲.txt"
        if self.exists(path_name):
            return
        settings_content = self.read_text("设定集.txt")
        outline_content = self.read_text("总纲.txt")
        self.generate_file(path_name, [
            {"role": "system", "content": "你是一个专业的小说部大纲生成器，根据设定集和总纲生成该部的大纲，包括有多少章以及每一章的大致内容，包括主要事件、剧情伏笔、角色发展、环境变化等。"},
            {"role": "user", "content": f"{settings_content}\n\n{outline_content}"}
        ])

    def generate_total_chapter_num(self, part_name: str) -> int:
        """根据部大纲生成该部的章数"""
        part_outline_content = self.read_text(f"{part_name}/大纲.txt")
        return int(self.generate(f'生成{part_name}的最大章数', [
            {"role": "system", "content": "你是一个小说章数计数器，根据部大纲，仅输出阿拉伯数字格式的最大章数，不包含任何额外的内容和符号。"},
            {"role": "user", "content": part_outline_content}
        ]))

    def generate_chapter_name(self, part_name: str, chapter_num: int) -> str:
        """根据章节号生成章节名"""
        if dir := next(self.book_output_dir.glob(f"{part_name}/第{chapter_num}章-*"), None):
            return dir.name
        part_outline_content = self.read_text(f"{part_name}/大纲.txt")
        chapter_name = self.generate(f'生成第{chapter_num}章-章节名', [
            {"role": "system", "content": "你是一个专业的小说章节名生成器，根据部大纲生成该章节的名称。仅输出章节名，不包含章节号和部号，不包含第几章，不包含任何额外的内容和符号。"},
            {"role": "user", "content": f"{part_outline_content}\n\n为{part_name}的第{chapter_num}章生成名称，仅输出章节名，不包含章节号和部号，不包含第几章："}
        ])
        return f"第{chapter_num}章-{chapter_name}"
    
    def get_prev_chapter_dir(self, part_name:str,chapter_name:str) -> Path | None:
        """获取前一章的目录"""
        part_num = int(re.search(r'\d+', part_name)[0])
        chapter_num = int(re.search(r'\d+', chapter_name)[0])
        if chapter_num == 1:
            if part_num == 1:
                return None
            # 找上一部的最后一章
            prev_part_dir = next(self.book_output_dir.glob(f'第{part_num - 1}部-*/'))
            prev_chapters = list((self.book_output_dir / prev_part_dir.name).glob('*/'))
            return max(prev_chapters, key=lambda x: int(re.search(r'\d+', x.name)[0]))
        return next((self.book_output_dir / part_name).glob(f"第{chapter_num-1}章-*/"))

    def generate_chapter_outline(self, part_name: str, chapter_name: str):
        """生成章节大纲文件"""
        path_name = f"{part_name}/{chapter_name}/大纲.txt"
        if self.exists(path_name):
            return
        settings_content = self.read_text("设定集.txt")
        part_outline_content = self.read_text(f"{part_name}/大纲.txt")
        prev_content = ''
        if prev_chapter_dir := self.get_prev_chapter_dir(part_name, chapter_name):
            if prev_chapter_outline_content := self.read_text(prev_chapter_dir / '大纲.txt'):
                prev_content += f"\n\n{prev_chapter_outline_content}"
        self.generate_file(path_name, [
            {"role": "system", "content": "你是一个专业的小说章节大纲生成器，主要事件、剧情伏笔、角色发展、环境变化等，以及配角要有一定的人物深度"},
            {"role": "user", "content": f"{settings_content}\n\n{prev_content}\n\n{part_outline_content}"}
        ])

    def generate_chapter_content(self, part_name: str, chapter_name: str):
        """生成章节正文文件"""
        path_name = f"{part_name}/{chapter_name}/正文.txt"
        if self.exists(path_name):
            return
        settings_content = self.read_text("设定集.txt")
        chapter_outline_content = self.read_text(f"{part_name}/{chapter_name}/大纲.txt")
        prev_content = ''
        if prev_chapter_dir := self.get_prev_chapter_dir(part_name, chapter_name):
            if prev_chapter_content := self.read_text(prev_chapter_dir / '正文.txt'):
                prev_content += f"\n\n{prev_chapter_content}"
        self.generate_file(path_name, [
            {"role": "system", "content": "你是一个专业的小说正文生成器，根据设定集和章节大纲生成高质量的章节正文。叙事要顺畅，角色要有深度，情节要有张力"},
            {"role": "user", "content": f"{settings_content}\n\n{prev_content}\n\n{chapter_outline_content}"}
        ])

    def run(self):
        """运行小说生成流程"""
        # 1. 获取用户输入
        if self.user_input is None and self.book_name is None:
            self.get_user_input()

        # 2. 生成书名并设置根目录
        if self.book_name is None:
            self.generate_book_name()

        self.setup_book_output_dir()

        if self.user_input is not None:
            (self.book_output_dir / "要求.txt").write_text(self.user_input, encoding="utf-8")
        else:
            self.user_input = self.read_text("要求.txt")

        # 3. 生成总纲和设定集
        self.generate_outline()
        total_part_num = self.generate_total_part_num()
        self.generate_settings()

        # 4. 开始生成各部内容
        part_num = 1
        while part_num <= total_part_num:
            # 生成部名
            part_name = self.generate_part_name(part_num)
            
            # 创建部大纲
            self.generate_part_outline(part_name)
            total_chapter_num = self.generate_total_chapter_num(part_name)
            
            # 生成章节
            chapter_num = 1
            while chapter_num <= total_chapter_num:
                chapter_name = self.generate_chapter_name(part_name, chapter_num)
                # 生成章节大纲
                self.generate_chapter_outline(part_name, chapter_name)

                # 生成章节正文
                self.generate_chapter_content(part_name, chapter_name)

                chapter_num += 1

            part_num += 1
        
        print(f"小说《{self.book_name}》生成完成")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="小说生成器")
    parser.add_argument("--model", '-m', type=str, default="qw", help="模型名称")
    parser.add_argument("--book-name", '-n', type=str, help="小说书名")
    parser.add_argument("--user-input", '-i', type=str, help="小说生成要求")
    parser.add_argument("--output-dir", '-o', type=str, default="./dist/", help="输出目录路径")
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
