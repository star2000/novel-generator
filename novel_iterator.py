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

        self.chat = u.Chat(model)

        self.outline = ''
        self.settings = ''
        self.chapters = []

        self.outline = self.chat(
            f"""\
生成一篇爽文小说的最小可行性大纲，包含以下要素：
1. 多个关键转折点
2. 人物核心欲望
3. 故事结局

要求：
- 大纲简洁，便于后续创作
- 转折点要有戏剧性
- 人物欲望要清晰
- 结局要有吸引力

{user_input}
""",
            '生成最小可行性大纲',
        )
        self.book_name = self.chat(
            f"""\
大纲：
{self.outline}

提取大纲中的书名，不包括书名号
""",
            '生成小说书名',
        )
        self.working_dir = Path(output_dir) / self.book_name
        self.working_dir.mkdir(parents=True, exist_ok=True)
        (self.working_dir / '大纲.md').write_text(self.outline, encoding='utf-8')

    def update_settings(self, content: str):
        """更新设定集"""
        prompt = f"""\
```txt
{content}
```

当前设定集：
{self.settings}

请根据以上内容，补充设定集

设定集应只关注底层设定，不包含任何多余内容，字数要非常少，文字简练
在当前设定集后追加内容：
"""

        update = self.chat(prompt, '更新设定集')
        self.settings += update
        (self.working_dir / '设定集.md').write_text(self.settings, encoding='utf-8')

    def compress_settings(self):
        """压缩设定集，去除冗余内容，保持核心信息不变"""
        prompt = f"""\
当前设定集：
{self.settings}
请压缩设定集，去除冗余内容，保持设定集核心信息不变
"""
        self.settings = self.chat(prompt, '压缩设定集')
        (self.working_dir / '设定集.md').write_text(self.settings, encoding='utf-8')

    def write_chapter(self) -> str:
        """写一章正文，结尾要有钩子"""
        chapter_num = len(self.chapters) + 1
        prompt = f"""\
{'\n\n'.join(f'第 {i} 章\n{c}' for i, c in enumerate(self.chapters, 1) if i > chapter_num - 5)}

大纲：
{self.outline}

设定集：
{self.settings}

请根据以上内容，写一章小说正文，结尾要自然地留下能引出悬念的钩子

第 {chapter_num} 章
"""

        content = self.chat(prompt, f'写第 {chapter_num} 章')
        self.chapters.append(content)
        (self.working_dir / f'第{chapter_num}章.md').write_text(
            content, encoding='utf-8'
        )
        self.update_settings(content)
        if chapter_num % 5 == 0:
            self.compress_settings()

    def run(self):
        """运行小说迭代器"""
        while True:
            self.write_chapter()


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
