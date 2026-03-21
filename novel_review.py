import argparse
from pathlib import Path

from ai_client import get_client

def review_novel(novel_dir: Path):
    part_num = 0
    chapter_num = 0
    word_list = [f'《{novel_dir.name}》']
    for part in novel_dir.glob('*/'):
        part_num += 1
        word_list.append(part.name)
        for chapter in part.glob('*/'):
            text = (chapter / '正文.txt')
            if text.exists():
                chapter_num += 1
                word_list.append(chapter.name)
                word_list.append(text.read_text(encoding='utf-8'))
    words = '\n'.join(word_list)
    stream = chat(messages=[
        {'role': 'system', 'content': '你是一个资深的小说读者，根据用户输入的小说内容，对各方面做出评价和评分'},
        {'role': 'user', 'content': words+'\n\n请对小说的各方面做出评价和评分'},
    ])
    print('='*80)
    print(f"《{novel_dir.name}》 共{part_num}部{chapter_num}章{len(words)}字 评价：")
    for chunk in stream:
        print(chunk.message.content, end='', flush=True)
    print()

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="小说评价器")
    parser.add_argument("--model", '-m', type=str, default="qw", help="模型名称")
    parser.add_argument("--output-dir", '-o', type=str, default="./dist/", help="输出目录路径")
    parser.add_argument("--book-name", '-n', type=str, help="小说书名")
    args = parser.parse_args()

    chat = get_client(args.model)

    output_dir = Path(args.output_dir)

    if args.book_name:
        review_novel(output_dir / args.book_name)
    else:
        for novel_dir in output_dir.glob('*/'):
            review_novel(novel_dir)
