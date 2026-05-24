import argparse
from pathlib import Path

import utils as u


class NovelIterator:
    def __init__(
        self,
        model: str,
        output_dir: str,
        user_input: str | None,
    ):
        if not user_input:
            user_input = input('要求：')

        self.chat = u.Chat(model, '你是一位幽默风趣的网文作者')

        self.outline = ''
        self.settings = ''
        self.chapters = []
        self.chapter_outlines = []

        self.outline = self.chat(
            f"""\
生成一篇有趣的小说大纲，包含以下要素：
1. 多个关键转折点
2. 人物核心欲望
3. 故事结局

{user_input}
""",
            '生成大纲',
        )
        self.book_name = self.chat(
            f"""\
<大纲>
{self.outline}
</大纲>

提取大纲中的书名，不包括书名号：
""",
            '提取大纲中的书名',
        )
        self.working_dir = Path(output_dir) / self.book_name
        self.working_dir.mkdir(parents=True, exist_ok=True)
        (self.working_dir / '大纲.md').write_text(self.outline, encoding='utf-8')

    def update_settings(self, chapter_num: int, content: str):
        """补充设定集"""
        prompt = f"""\
<最新章节>
{content}
</最新章节>

<当前设定集>
{self.settings}
</当前设定集>

请根据最新章节的内容补充当前设定集，并输出完整的设定集：
"""

        self.settings = self.chat(prompt, '补充设定集')
        (self.working_dir / f'第{chapter_num}章' / '设定集.md').write_text(
            self.settings, encoding='utf-8'
        )

    def is_end(self, content: str) -> bool:
        result = self.chat(f"""\
<最新章节>
{content}
</最新章节>

本章是否是全书的最后一章（比如出现了“全书完”之类的词句）？[是/否]：
""")
        return '是' in result

    def write_chapter(self, chapter_num: int) -> str:
        """创作正文"""
        prompt = f"""\
<大纲>
{self.outline}
</大纲>

<设定集>
{self.settings}
</设定集>

{'\n\n'.join(f'<第{i}章总结>\n{c}\n</第{i}章总结>' for i, c in enumerate(self.chapter_outlines, 1))}

请创作第 {chapter_num} 章的正文：
"""

        content = self.chat(prompt, f'第 {chapter_num} 章')
        self.chapters.append(content)
        (self.working_dir / f'第{chapter_num}章' / '正文.md').write_text(
            content, encoding='utf-8'
        )
        return content

    def write_chapter_outline(self, chapter_num: int, content: str):
        """总结正文"""
        prompt = f"""\
<设定集>
{self.settings}
</设定集>

<第{chapter_num}章>
{content}
</第{chapter_num}章>

请对第{chapter_num}章中的内容进行总结并输出：
"""

        chapter_outline = self.chat(prompt, f'总结第{chapter_num}章正文')
        self.chapter_outlines.append(chapter_outline)
        (self.working_dir / f'第{chapter_num}章' / '总结.md').write_text(
            chapter_outline, encoding='utf-8'
        )

    def run(self):
        """运行小说迭代器"""
        chapter_num = 1
        while True:
            content = self.write_chapter(chapter_num)
            if self.is_end(content):
                break
            self.update_settings(chapter_num, content)
            self.write_chapter_outline(content)
            chapter_num += 1


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='小说生成器')
    parser.add_argument(
        '--model', '-m', type=str, default='qwen3.5:4b', help='模型名称'
    )
    parser.add_argument('--book-name', '-n', type=str, help='小说书名')
    parser.add_argument('--user-input', '-i', type=str, help='小说生成要求')
    parser.add_argument(
        '--output-dir', '-o', type=str, default='./dist/', help='输出目录路径'
    )
    args = parser.parse_args()

    # 初始化生成器
    generator = NovelIterator(
        model=args.model,
        output_dir=args.output_dir,
        user_input=args.user_input,
    )

    # 运行生成流程
    generator.run()
