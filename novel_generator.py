from __future__ import annotations

import argparse
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
        stream = self.chat(messages=messages, stream=True)
        print('='*80)
        print(f'{name}：')
        content = ''
        for chunk in stream:
            if chunk.message.content:
                content += chunk.message.content
                print(chunk.message.content, end='', flush=True)
        print()
        return content.strip()

    def generate_file(self, path_name: str, messages: list[Message], check_times: int = 1):
        '''生成文件'''
        path = self.book_output_dir / path_name
        if path.exists():
            print(f'{path_name} 已存在，跳过生成')
            return
        output_messages = [{
            'role': 'user',
            'content': f'请只用中文生成 {path_name} 的内容'
        }]
        path.parent.mkdir(parents=True, exist_ok=True)
        settings_content = self.read_text('设定集.md')
        fix_messages: list[Message] = []
        while True:
            stream = self.chat(
                messages=messages+fix_messages+output_messages)
            print('='*80)
            print(f'生成 {path_name}：')
            content = ''
            for chunk in stream:
                if chunk.message.content:
                    content += chunk.message.content
                    print(chunk.message.content, end='', flush=True)
            print('\n'+('='*80))
            if check_times <= 0:
                break
            check_times -= 1
            check = self.generate(f'检查 {path_name}', [
                {'role': 'system',
                    'content': '你是一个资深的热门网络小说读者，检查用户输入是否合理'},
                {'role': 'user',
                    'content': f'{settings_content or self.user_input}\n\n{path_name}：{content}'}
            ])
            fix_messages = [{
                'role': 'assistant',
                'content': content
            }, {
                'role': 'user',
                'content': f'{check}\n\n请重新生成'
            }]
        path.write_text(content, encoding='utf-8')
        print(f'{path_name} 生成完成')

    def generate_book_name(self):
        '''根据用户要求生成书名'''
        self.book_name = self.generate('生成书名', [
            {'role': 'system', 'content': '你是一位热门网络小说作者，根据用户输入，起个书名，仅回答一个书名'},
            {'role': 'user', 'content': f'{self.user_input}'}
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
            {'role': 'system', 'content': '你是一个专业的热门高质量网络小说作家，写设定集，要将模糊的灵感转化为可执行的商业蓝图，分析灵感核心，提炼出“爽点”和“期待感”，并构建世界观设定（力量体系、社会阶级、金手指机制）、人物小传（主角人设、主要配角、反派设计（需有智商和魅力））'},
            {'role': 'user', 'content': f'《{self.book_name}》\n\n要求：{self.user_input}'}
        ], 5)

    def generate_outline(self):
        '''生成总纲文件'''
        settings_content = self.read_text('设定集.md')

        self.generate_file('总纲.md', [
            {'role': 'system', 'content': '你是一个专业的小说作者，根据用户的输入，生成小说的总纲，要有一句话讲清楚故事卖点的核心梗，然后定义主线脉络，并划分大卷，每卷设定具体的字数目标和完结节点。在第一卷的开头专门设计黄金三章的起承转合（切入冲突、抛出悬念、确立期待）。'},
            {'role': 'user', 'content': f'《{self.book_name}》\n\n要求：{self.user_input}\n\n{settings_content}'}
        ], 4)

    def generate_total_part_num(self):
        '''根据总纲生成总卷数'''
        outline_content = self.read_text('总纲.md')
        return int(self.generate('生成最大卷数', [
            {'role': 'system', 'content': '你是一个小说卷数计数器，根据总纲，仅输出阿拉伯数字格式的最大卷数，不包含任何额外的内容和符号。'},
            {'role': 'user', 'content': outline_content}
        ]))

    def generate_part_name(self, part_num: int) -> str:
        '''根据卷号生成卷名'''
        if dir := next(self.book_output_dir.glob(f'第{part_num}卷-*'), None):
            return dir.name
        outline_content = self.read_text('总纲.md')
        part_name = self.generate(f'提取第{part_num}卷-卷名', [
            {'role': 'system', 'content': '你是一个专业的小说卷名提取器，根据总纲提取该卷的名称。仅输出卷名，不包含卷号'},
            {'role': 'user', 'content': f'{outline_content}\n\n输出第{part_num}卷的卷名，不包含卷号或第几卷：'}
        ])
        return f'第{part_num}卷-{part_name}'

    def generate_part_outline(self, part_name):
        '''生成卷大纲文件'''
        path_name = f'{part_name}/大纲.md'
        if self.exists(path_name):
            return
        settings_content = self.read_text('设定集.md')
        outline_content = self.read_text('总纲.md')
        self.generate_file(path_name, [
            {'role': 'system', 'content': '你是一个专业的热门高质量网络小说作家，写卷大纲，要有结构规划与节奏把控，结构规划要确保留存率，细化大纲，每章设计“钩子”（结尾悬念）。节奏把控要考虑“期待值管理”：“憋屈 - 爆发”的循环不要超过三章。最好是“小冲突（被骚扰） -> 心理博弈 -> 快速反杀 -> 嘲讽反派”。让读者在压抑后立刻得到释放。'},
            {'role': 'user', 'content': f'{settings_content}\n\n{outline_content}'}
        ], 3)

    def generate_total_chapter_num(self, part_name: str) -> int:
        '''根据卷大纲生成该卷的章数'''
        part_outline_content = self.read_text(f'{part_name}/大纲.md')
        return int(self.generate(f'生成{part_name}的最大章数', [
            {'role': 'system', 'content': '你是一个小说章数计数器，根据卷大纲，仅输出阿拉伯数字格式的最大章数，不包含任何额外的内容和符号。'},
            {'role': 'user', 'content': part_outline_content}
        ]))

    def generate_chapter_name(self, part_name: str, chapter_num: int) -> str:
        '''根据章节号生成章节名'''
        if dir := next(self.book_output_dir.glob(f'{part_name}/第{chapter_num}章-*'), None):
            return dir.name
        part_outline_content = self.read_text(f'{part_name}/大纲.md')
        chapter_name = self.generate(f'提取第{chapter_num}章-章节名', [
            {'role': 'system', 'content': '你是一个专业的小说章节名提取器，根据卷大纲提取该章节的名称。仅输出章节名，不包含章节号'},
            {'role': 'user', 'content': f'{part_outline_content}\n\n输出第{chapter_num}章的章节名，不包含章节号或第几章：'}
        ])
        return f'第{chapter_num}章-{chapter_name}'

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
                'content': '你是一个专业的热门高质量网络小说作家，写章节大纲，要屏蔽内心审查，关闭“逻辑纠错器”和“修辞美化器”。允许自己写出粗糙的草稿，只要它能连贯地讲述故事。展示而非告知：这是铁律。你不写“他很生气”，你只写“他摔碎了杯子，指关节泛白”。所有的情绪和背景信息，必须通过动作、环境、感官细节来呈现，绝不直接陈述。保持语势一致：根据场景切换调整叙事节奏。紧张时句子短促有力，抒情时句子绵长舒缓，但绝不为了炫技而破坏故事的沉浸感。'},
            {'role': 'user', 'content': f'{settings_content}\n\n{prev_content}\n\n{part_outline_content}'}
        ], 2)

    def generate_chapter_content(self, part_name: str, chapter_name: str):
        '''生成章节正文文件'''
        path_name = f'{part_name}/{chapter_name}/正文.md'
        if not self.exists(path_name):
            settings_content = self.read_text('设定集.md')
            chapter_outline_content = self.read_text(
                f'{part_name}/{chapter_name}/大纲.md')
            self.generate_file(path_name, [
                {'role': 'system', 'content': '你是一个专业的热门高质量网络小说作家，写章节正文，要给章节大纲注入血肉和灵魂。**对话重构**：删除那些信息重复的对话。让人物说话像真人，带有各自的语气、口头禅和潜台词。**感官扩容**：补充视觉、听觉、嗅觉、触觉、味觉的描述，让环境变得可感知。**节奏微调**：调整段落长短，制造呼吸感。在读者情绪最紧绷的地方暂停，在最需要放松的地方推进。'},
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
                stream = self.chat(messages=[
                    {'role': 'system',
                        'content': '你是一个小说正文洗稿器，正文开头不应该出现第几章第几卷，结尾不应该明说本章完，其余必须保持原样'},
                    {'role': 'user', 'content': content}
                ])
                cleaned_content = ''
                print(f'洗稿 {path_name}')
                for chunk in stream:
                    if chunk.message.content:
                        cleaned_content += chunk.message.content
                        print(chunk.message.content, end='', flush=True)
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
        total_part_num = self.generate_total_part_num()

        # 4. 开始生成各卷内容
        part_num = 1
        while part_num <= total_part_num:
            # 生成卷名
            part_name = self.generate_part_name(part_num)

            # 创建卷大纲
            self.generate_part_outline(part_name)
            total_chapter_num = self.generate_total_chapter_num(part_name)

            # 生成章节
            chapter_num = 1
            while chapter_num <= total_chapter_num:
                chapter_name = self.generate_chapter_name(
                    part_name, chapter_num)
                # 生成章节大纲
                self.generate_chapter_outline(part_name, chapter_name)

                # 生成章节正文
                self.generate_chapter_content(part_name, chapter_name)

                chapter_num += 1

            part_num += 1

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
