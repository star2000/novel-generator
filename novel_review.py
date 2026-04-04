import argparse
import math
from pathlib import Path

import utils as u


def review_novel(novel_dir: Path):
    part_num = 0
    chapter_num = 0
    word_num = 0
    word_list = [f'《{novel_dir.name}》']
    for part in u.sorted_subdirs(novel_dir):
        part_num += 1
        word_list.append(part.name)
        for chapter in u.sorted_subdirs(part):
            word_file = (chapter / '正文.txt')
            if word_file.exists():
                chapter_num += 1
                word_list.append(chapter.name)
                word = word_file.read_text(encoding='utf-8')
                word_num += len(word)
                word_list.append(word)
    words = '\n'.join(word_list)
    num_ctx = 2**max(15, min(18, math.ceil(math.log2(len(words)))))
    stream = chat(messages=[
        {'role': 'system', 'content': '你是一个资深的热门网络小说读者，根据用户输入的小说内容，对各方面做出评价和评分'},
        {'role': 'user', 'content': words + '\n\n请对小说的各方面做出评价和评分'},
    ], options={'num_ctx': num_ctx})
    print('='*80)
    print(f'《{novel_dir.name}》 共{part_num}卷{chapter_num}章{word_num}字 评价：')
    for chunk in stream:
        if chunk.message.content:
            print(chunk.message.content, end='', flush=True)
    print()


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='小说评价器')
    parser.add_argument('--model', '-m', type=str, default='qw', help='模型名称')
    parser.add_argument('--output-dir', '-o', type=str,
                        default='./dist/', help='输出目录路径')
    parser.add_argument('--book-name', '-n', type=str, help='小说书名')
    args = parser.parse_args()

    chat = u.get_chat(args.model)

    output_dir = Path(args.output_dir)

    if args.book_name:
        review_novel(output_dir / args.book_name)
    else:
        for novel_dir in output_dir.glob('*/'):
            review_novel(novel_dir)
