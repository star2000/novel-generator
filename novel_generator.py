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

### 一、设定集 (Setting & World Building)
**核心定义**：小说的“地基”与“说明书”。它决定了世界观的规则、背景历史、角色关系网、力量体系及特殊道具。
**常见误区**：写成枯燥的辞典，或设定过于宏大却与故事无关（背景板）。

#### 📝 应该写什么？
1.  **世界观架构**：地理环境、社会结构、文化习俗、特殊历史事件。
2.  **力量/能力体系**：等级划分（如练气九层）、获取方式、克制关系、副作用（平衡性的关键）。
3.  **势力与人设草图**：主要派别、正反派阵营、主角团及重要配角的基本档案。
4.  **核心冲突源**：贯穿全书的矛盾点（如：资源匮乏、信仰崩塌、种族隔阂）。
5.  **道具/物品库**：关键物品的来源、功能及限制条件。

#### 🚫 专属守则
*   **内部一致性原则**：一旦写下“火球术需要消耗寿命”，就不能在正文里让主角无中生有地放个火球，除非有合理的剧情解释（伏笔或剧情杀）。
*   **服务于剧情原则**：所有设定必须推动情节发展。如果某个设定在正文中用不上，建议砍掉或修改，避免“设定堆砌”。
*   **逻辑自洽原则**：严禁出现为了爽而强行打破逻辑的情况（例如：明明设定了高阶怪物，却为了救场让主角随便打个胜仗）。


### 二、总纲 (Master Plan / Synopsis)
**核心定义**：小说的“导航图”。用几百字到几千字，概括整本书的脉络、核心梗（Goldfinger）、主线任务及结局走向。
**常见误区**：写成“爽文”堆砌流水账，缺乏逻辑闭环，导致中期崩盘。

#### 📝 应该写什么？
1.  **核心梗（Hook）**：一句话讲清楚主角的特殊性、目标及面临的绝境（例如：主角拥有读心术，但只能听到敌人坏话，目标是成为最强）。
2.  **主线剧情流**：从开局到最终 BOSS 的宏观路线图（起承转合）。
3.  **人物弧光**：主角的性格变化轨迹及最终结局（BE/HE/开放式）。
4.  **关键矛盾推进机制**：冲突是如何升级的？反派为何如此强大？
5.  **爽点节奏规划**：预计在哪里安排大高潮、哪里安排低谷以蓄势待发。

#### 🚫 专属守则
*   **闭环原则**：开篇必须抛出悬念或核心需求，结尾必须回应开头的问题（或提供合理的新的问题），形成完整闭环。
*   **拒绝烂尾原则**：在总纲中明确标注“最终决战”的节点，确保所有伏笔（种子）都有对应的回收点（果实）。
*   **节奏可视化**：总纲中应能清晰看到“压抑 - 释放”、“平静 - 危机”的波浪式节奏，而非直线上升。


### 三、卷大纲 (Volume Outline)
**核心定义**：将总纲拆解的“阶段性战役”。通常每卷对应一个大高潮或一个世界观的完整展开。
**常见误区**：只写章节列表，没写剧情走向；或者剧情过于细碎，像流水账。

#### 📝 应该写什么？
1.  **卷名与核心任务**：本卷要解决什么问题？达成什么阶段性胜利？
2.  **情节节点**：列出 5-8 个关键剧情点（如：初战告捷、遭遇背叛、获得关键宝物、发现惊天秘密）。
3.  **人物关系变动**：本卷中谁获得了成长？谁成为了新敌人？谁退隐了？
4.  **势力消长**：正反派力量对比的变化过程。
5.  **情感/剧情钩子**：本卷结尾要留下什么悬念，让读者迫切想看下一卷？

#### 🚫 专属守则
*   **颗粒度适中**：不能太粗（否则正文写不完），不能太细（否则正文时不知道怎么写）。每个节点应包含“起因 - 发展 - 高潮 - 结果”。
*   **冲突递增原则**：随着卷序推进，外部冲突和内部冲突必须层层加码，读者期待感不能下降。
*   **草蛇灰线**：在卷大纲中要埋下连接下一卷的线索（伏笔），但在本卷内部也要有足够的高光时刻。


### 四、章节大纲 (Chapter Outline)
**核心定义**：正文的“骨架”。详细规划每一章甚至每一节的内容，确保正文写作时有章可循。
**常见误区**：只写“今天主角打怪了”，缺乏情绪张力和具体情节设计。

#### 📝 应该写什么？
1.  **章节标题**：吸引眼球，体现本章节核心事件。
2.  **核心事件**：本章发生了什么？（建议每章至少发生一件具体事）。
3.  **情绪曲线**：本章的情绪是高昂（打脸）、压抑（等待）、紧张（对峙）还是温馨（日常）？
4.  **钩子（Hook）**：结尾留下了什么悬念？（金手指觉醒？意外发现？反派现身？）
5.  **互动/反应**：本章结尾后，读者会有什么期待？主角会有何反应？

#### 🚫 专属守则
*   **黄金三章法则**：前三章必须完成：金手指展示/获取、主角困境、初步反击/悬念，快速抓住读者。
*   **钩子前置**：结尾悬念必须设置在最后 10%-20% 处，强行留住读者的点击欲望。
*   **避免注水**：严禁为了凑字数而写无关的背景介绍或对话，每一段文字都必须推动剧情或塑造人物。


### 五、正文 (Main Body)
**核心定义**：小说的“血肉”与“灵魂”。读者直接阅读的内容，是审美、节奏、代入感的最直接体现。
**常见误区**：文笔华丽但逻辑不通，或文笔平白但节奏拖沓，缺乏画面感。

#### 📝 应该写什么？
1.  **画面感（Show, Don't Tell）**：通过动作、神态、环境描写来呈现，而非直接告诉读者情绪。
2.  **快节奏叙事**：剔除冗长心理描写，直接切入冲突和行动，保持阅读流。
3.  **人物对话**：符合人设，推动剧情，展现潜台词。
4.  **感官体验**：调动读者的视、听、触、嗅，增强沉浸感。
5.  **情感共鸣**：让读者不仅在看故事，更是在为角色经历。

#### 🚫 专属守则
*   **阅读友好原则**：段落不宜过长，节奏紧凑，避免大段枯燥的说教或数据堆砌（可用旁白概括）。
*   **逻辑严密原则**：人物行为必须符合其性格设定，对话必须符合逻辑，杜绝降智打击。
*   **反馈及时原则**：主角的付出必须有回报（哪怕是微小的），读者的情绪投入需要得到即时满足。

                           
### ⭐ 通用守则 (Universal Golden Rules)
无论处于哪个阶段，以下三条铁律贯穿始终：

#### 1. 读者第一原则 (The Reader First)
*   **内容**：所有的设定、大纲和正文，最终目的只有一个——**取悦读者/留住读者**。
*   **执行**：不要过度追求所谓的“文学性”而牺牲了故事的流畅度。网文是商业创作，读者的情绪价值（爽、虐、燃、感动）是最高优先级。如果设定很有趣但写不出，       
就改大纲；如果大纲很完美但正文写不动，就重写设定。

#### 2. 动态调整原则 (Iterative Process)
*   **内容**：没有一稿定情的作品。大纲是基于初稿的推演，初稿是基于大纲的填充，但**市场反馈会反向修正你的理解**。
*   **执行**：如果你写了几十万字，感觉前面的设定现在来看太烂，或者有读者反馈不喜欢某个套路，你要敢于在后期调整人物关系、修改力量体系，甚至重写部分章节。     
**大纲不是枷锁，而是导航，导航可以随时微调航线。**

#### 3. 核心不变原则 (Core Consistency)
*   **内容**：在允许微调的情况下，故事的**核心梗（Core Concept）** 和 **主角动机（Core Motivation）** 必须保持稳定。
*   **执行**：可以改变主角身边的配角、可以改变反派的脸谱，但不能改变主角“为什么要变强”这个核心驱动力，否则故事就失去了灵魂，变成了单纯的流水账。
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
            {'role': 'user', 'content': f'开题灵感：{self.user_input}\n\n提取或起个书名，仅回答一个，不携带书名号'}
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

开题灵感：{self.user_input}

写设定集，需要定义剧情大纲之外的所有方面，要有一定深度的各种人、事、物的名字和背景设定，立住人设，深化情感内核，用于生成大纲
'''}
        ])

    def generate_outline(self):
        '''生成总纲文件'''
        settings_content = self.read_text('设定集.md')

        self.generate_file('总纲.md', [
            {'role': 'user', 'content': f'''\
《{self.book_name}》

开题灵感：{self.user_input}

{settings_content}
'''}
        ])

    def generate_part_names(self):
        '''生成卷名列表'''
        outline_content = self.read_text('总纲.md')
        parts_str = self.generate_file('卷名.txt', [
            u.Message(role='system', content='你是一个小说卷名生成器'),
            u.Message(
                role='user', content=f'{outline_content}\n\n提取或生成所有的卷名，不重复，每行一个，仅输出卷名，不包含第几卷'),
        ], think=True)
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
            u.Message(role='system', content='你是一个小说章节名生成器'),
            u.Message(
                role='user', content=f'{part_outline_content}\n\n提取或生成所有的章节名，不重复，每行一个，仅输出章节名，不包含第几章'),
        ], think=True)
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
                        'content': '你是一个小说正文洗稿器，开头不应该出现第几章第几卷，结尾不应该明说本章完，内容不应该出现无意义的重复，总之这类影响读者阅读体验的与正文无关的内容，要删或改，其余必须保持原样'},
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
            self.user_input = self.chat([
                {'role': 'user', 'content': '仅生成一个小说的开题灵感，包含一个书名和一个介绍，不包含无关内容'}
            ], title='生成开题灵感')

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
