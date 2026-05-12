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
        self.working_dir = Path(output_dir) / u.now().strftime('%Y%m%d_%H%M%S')
        self.working_dir.mkdir(parents=True, exist_ok=True)
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

    def update_settings(self, content: str):
        """更新设定集"""
        prompt = f"""\
当前设定集：
{self.settings}

请根据以下内容，补充设定集：

```txt
{content}
```

设定集应只关注底层设定，不包含剧情内容。
输出追加设定集，不包含已经存在的设定：
"""

        update = self.chat(prompt, '更新设定集')
        self.settings += update
        (self.working_dir / '设定集.md').write_text(self.settings, encoding='utf-8')

    def write_chapter(self) -> str:
        """写一章正文，结尾要有钩子"""
        chapter_num = len(self.chapters) + 1
        prompt = f"""\
{'\n\n'.join(f'第 {i} 章\n{c}' for i, c in enumerate(self.chapters, 1))}

大纲：
{self.outline}

设定集：
{self.settings}

请根据以上内容，写一章小说正文
要求：
1. 章节结尾必须有钩子，引出下一章
2. 保持人物性格一致
3. 情节要有张力
4. 字数控制在 2000-3000 字

第 {chapter_num} 章
"""

        content = self.chat(prompt, f'写第 {chapter_num} 章')
        self.chapters.append(content)
        (self.working_dir / f'第{chapter_num}章.md').write_text(
            content, encoding='utf-8'
        )
        self.update_settings(content)

    def run(self):
        """运行小说迭代器"""
        print('=' * 50)
        print('开始小说创作循环')
        print('=' * 50)

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
