import argparse
from pathlib import Path
import re
from urllib.parse import unquote

from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
import markdown

from ai_client import get_client


dmp = diff_match_patch()

def diff(old: str, new: str) -> str:
    return unquote(dmp.patch_toText(dmp.patch_make(old, new)))

def markdown_to_text(markdown_string: str) -> str:
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def clean_novel(model: str, novel_dir: Path):
    chat = get_client(model, stream=False)

    parts = list(novel_dir.glob('*/'))
    parts.sort(key=lambda x: int(re.search(r'\d+', x.name)[0]))
    for part in parts:
        chapters = list(part.glob('*/'))
        chapters.sort(key=lambda x: int(re.search(r'\d+', x.name)[0]))
        for chapter in chapters:
            text = (chapter / '正文.md')
            if text.exists():
                print(f"处理 「{part.name}」 「{chapter.name}」 ...")
                content = text.read_text(encoding='utf-8')
                response = chat(messages=[
                    {"role": "system", "content": "你是一个小说整理器，将用户输入的小说正文，删除第几部第几章和本章完之类的与小说正文无关的部分，尽量少地改动，然后输出整理后的文本。"},
                    {"role": "user", "content": content}
                ])
                new_content = markdown_to_text(response.message.content or content)
                diff_text = diff(content, new_content)
                (chapter/ '正文.txt').write_text(new_content, encoding='utf-8')
                (chapter/ '差异.txt').write_text(diff_text, encoding='utf-8')
                print(diff_text)


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="小说正文整理器")
    parser.add_argument("--model", '-m', type=str, default="qw", help="模型名称")
    parser.add_argument("--output-dir", '-o', type=str, default="./dist/", help="输出目录路径")
    parser.add_argument("--book-name", '-n', type=str, help="小说书名")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if args.book_name:
        clean_novel(args.model, output_dir / args.book_name)
    else:
        for novel_dir in output_dir.glob('*/'):
            clean_novel(args.model, novel_dir)
