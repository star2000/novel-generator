
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import requests

import utils as u

if TYPE_CHECKING:
    from typing import *  # type: ignore

    class BookIntro(TypedDict):
        status: str
        tag: str
        message: str

    class BookSignLevelStatus(TypedDict):
        sign_level: int
        expect_word_number: int

    class BookThumbUrlItem(TypedDict):
        size: str
        main_url: str
        backup_url: str

    class BookItem(TypedDict):
        book_name: str
        book_id: str
        status: int
        verify_status: int
        thumb_uri: str
        category: str
        create_time: str
        author: str
        abstract: str
        genre: int
        price: int
        word_count: int
        sale_type: int
        read_count: int
        authorize_type: int
        sign_progress: int
        creation_status: int
        can_recommend: int
        origin_level: str
        origin_app_level: int
        book_flight_alias_name: str
        free_status: int
        last_chapter_time: str
        last_chapter_title: str
        last_chapter_id: str
        chapter_number: int
        total_impression_count: int
        add_bookshelf_count: int
        attend_day_count: int
        attend_word_count: int
        attend_need_word_count: int
        is_cp: int
        source: str
        set_top: int
        has_hide: int
        has_activity: int
        activity_id: int
        activity_name: str
        can_join_activity: bool
        can_join_activity_id: str
        can_join_activity_name: str
        can_join_activity_url: str
        sign_level_status: BookSignLevelStatus
        security_auditor_status: int
        security_status: int
        thumb_url_list: List[BookThumbUrlItem]
        book_intro: BookIntro
        referral_traffic_permission: int
        referral_traffic_running_state: int
        in_attend_activity: int
        default_thumb_url: bool
        write_extra_permission: int
        content_word_number: int
        extra_word_number: int
        attend_brave_wind_task: int
        weak_ending: int

    class VolumeItem(TypedDict):
        index: int
        book_id: str
        volume_id: str
        volume_name: str
        item_count: int
        can_delete: bool

    class ChapterItem(TypedDict):
        item_id: str
        volume_id: str
        index: int
        title: str
        recommend_title: str
        recommend_editable: int
        display_status: int
        is_title_recommend: int
        recommend_count_limit: int
        recommend_count: int
        article_status: int
        recommend_status: int
        create_time: int
        need_pay: int
        price: int
        word_number: int
        timer_time: str
        can_delete: int
        mp_highlight_stage: int
        sell_product_chapter: int
        cant_modify_reason: str
        correction_feedback_num: int
        author_speak_audit_block: bool
        timer_chapter_preview: Any | None

    class NewArticleColumnDataAuditChapter(TypedDict):
        audit_failed_chapter_title: str
        audit_time_chapter_title: str

    class NewArticleColumnData(TypedDict):
        article_status: int
        book_id: str
        book_name: str
        can_charge: int
        previous_chapter_title: str
        need_pay: int
        platform: int
        sale_type: int
        status: int
        verify_status: int
        audit_chapter: NewArticleColumnDataAuditChapter
        origin_chapter_ad_status: int
        chapter_ad_permission: bool
        chapter_passed_num: int
        has_new_volume: bool
        attribution_type: int
        book_extra_word_number: int
        has_new_volume_tip: str

    class NewArticleVolumeDataItem(TypedDict):
        volume_id: str
        volume_name: str

    class NewArticleLatestPublishItemInfo(TypedDict):
        item_id: str
        title: str
        volume_id: str
        volume_name: str

    class NewArticlePreAuditInfo(TypedDict):
        pre_audit_switch_close: int
        pre_audit_left_count: int
        pre_audit_current_status: Any | None
        latest_pre_audit_result: Any | None

    class NewArticle(TypedDict):
        column_data: NewArticleColumnData
        volume_data: List[NewArticleVolumeDataItem]
        media_id: int
        latest_publish_item_info: NewArticleLatestPublishItemInfo
        item_id: str
        latest_version: int
        permission_switch: int
        is_initial_default_book: bool
        volume_id: str
        creation_status: int
        is_reuse: int
        pre_audit_info: NewArticlePreAuditInfo


class FanQieNovelAuthorClient:
    BASE_URL = 'https://fanqienovel.com/api/author/'

    @staticmethod
    def check_sessionid(sessionid: str):
        assert re.match(r'[a-z0-9]{32}', sessionid), f'{sessionid} 会话id格式错误'

    def __init__(self, sessionid: str):
        self.check_sessionid(sessionid)
        self.cookies = {
            'sessionid': sessionid,
        }
        self._secsdk_csrf_token = ''
        self._secsdk_csrf_token_expired_at = None

    def _request(self, method, url, **kwargs):
        resp = requests.request(
            method,
            urljoin(self.BASE_URL, url),
            cookies=self.cookies,
            **kwargs
        )
        assert resp.status_code == 200, f'{resp.status_code=} {resp.text=}'
        assert resp.text, 'secsdk_csrf 校验未通过'
        resp_json = resp.json()
        assert resp_json['code'] == 0, f"{resp_json['code']} {resp_json['message']}"
        return resp_json['data']

    def _get(self, url, params={}, **kwargs):
        return self._request('get', url, params=params, **kwargs)

    def secsdk_csrf_token(self):
        now = datetime.now()
        if self._secsdk_csrf_token_expired_at and self._secsdk_csrf_token_expired_at < now:
            return self._secsdk_csrf_token
        resp = requests.head('https://fanqienovel.com/ttwid/check/', headers={
            'x-secsdk-csrf-request': '1',
            'x-secsdk-csrf-version': '1.2.22'
        })
        token_info = resp.headers['x-ware-csrf-token'].split(',')
        max_age = 24 * 60 * 60 * 1000
        try:
            max_age = int(token_info[2])
        except ValueError:
            pass
        expired_at = now + timedelta(milliseconds=max_age)
        self._secsdk_csrf_token = token_info[1]
        self._secsdk_csrf_token_expired_at = expired_at
        return self._secsdk_csrf_token

    def _post(self, url, data, **kwargs):
        return self._request('post', url, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'x-secsdk-csrf-token': self.secsdk_csrf_token(),
        }, **kwargs)

    def get_book_list(self, page_count=10):
        '''获取书列表'''
        book_list: list[BookItem] = []
        while True:
            data = self._get('book/book_list/v1', {
                'page_count': page_count,
                'page_index': len(book_list) // page_count,
            })
            book_list.extend(data['book_list'])
            if len(book_list) >= data['total_count']:
                break
        return book_list

    def get_volume_list(self, book_id: str) -> list[VolumeItem]:
        '''获取卷列表'''
        data = self._get('volume/volume_list/v1', {
            'book_id': book_id,
        })
        return data['volume_list']

    @staticmethod
    def check_volume_name(volume_name: str):
        assert re.match(r'第[零一二三四五六七八九十百千万亿]+[卷]：.+',
                        volume_name), f'{volume_name} 卷名格式错误'

    @staticmethod
    def check_article_title(article_title: str):
        assert re.match(r'第\d+章 .+', article_title), f'{article_title} 章节名格式错误'

    def add_volume(self, book_id: str, volume_name: str):
        '''新增卷'''
        self.check_volume_name(volume_name)

        return self._post('volume/add_volume/v0', {
            'book_id': book_id,
            'volume_name': volume_name,
        })

    def get_chapter_list(self, book_id: str, volume_id: str, page_count=15):
        '''获取章节列表'''
        chapter_list: list[ChapterItem] = []
        while True:
            data = self._get('chapter/chapter_list/v1', {
                'book_id': book_id,
                'volume_id': volume_id,
                'page_count': page_count,
                'page_index': len(chapter_list) // page_count,
            })
            chapter_list.extend(data['item_list'])
            if len(chapter_list) >= data['total_count']:
                break
        return chapter_list

    def new_article(self, book_id: str) -> NewArticle:
        '''新建文章'''
        return self._post('article/new_article/v0', {'book_id': book_id, 'need_reuse': 1})

    def publish_article(self, book_id: str, volume_id: str, volume_name: str, title: str, content: str, item_id: str | None = None):
        '''发布文章'''
        self.check_volume_name(volume_name)
        self.check_article_title(title)

        if item_id is None:
            item_id = self.new_article(book_id)['item_id']
        if '<p>' not in content:
            content = u.text_to_html(content)
        return self._post('publish_article/v0', {
            'book_id': book_id,
            'volume_id': volume_id,
            'volume_name': volume_name,
            'item_id': item_id,
            'title': title,
            'content': content,
            'use_ai': 1,
        })


if __name__ == '__main__':
    import argparse
    import os
    from pathlib import Path

    from dotenv import load_dotenv
    from pycnnum import num2cn

    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', type=str, default='qw', help='模型名称')
    parser.add_argument('--output-dir', '-o', type=str,
                        default='./dist/', help='输出目录路径')
    args = parser.parse_args()

    chat = u.Chat(args.model, '你是一位专业的热门高质量网络小说作家')
    output_dir = Path(args.output_dir)

    client = FanQieNovelAuthorClient(os.environ['FANQIE_SESSIONID'])

    for book in client.get_book_list():
        novel_dir = output_dir / book['book_name']
        if not novel_dir.exists():
            continue
        book_id = book['book_id']
        volume_name_id_map = {
            volume['volume_name']: volume['volume_id']
            for volume in client.get_volume_list(book_id)
        }
        used_article_title: set[str] = set()
        for part_dir in u.sorted_subdirs(novel_dir):
            part_num = u.get_first_int(part_dir.name)
            part_cnnum = num2cn(part_num)
            volume_name = part_dir.name.replace(
                str(part_num), part_cnnum, 1).replace('-', '：', 1)
            if volume_name not in volume_name_id_map:
                client.add_volume(book_id, volume_name)
                volume_name_id_map = {
                    volume['volume_name']: volume['volume_id']
                    for volume in client.get_volume_list(book_id)
                }
                assert volume_name in volume_name_id_map, f'{volume_name} 添加失败'
            volume_id = volume_name_id_map[volume_name]
            chapter_list = client.get_chapter_list(book_id, volume_id)
            chapter_title_list = [chapter['title'] for chapter in chapter_list]
            for chapter_dir in u.sorted_subdirs(part_dir):
                prune_article_order, prune_article_title = chapter_dir.name.split(
                    '-', 1)
                article_content = (
                    chapter_dir / '正文.txt').read_text(encoding='utf-8')
                is_rename = False
                while prune_article_title in used_article_title:
                    new_article_title = chat([
                        {'role': 'user', 'content': f'正文：{article_content}\n\n原名：{prune_article_title}\n\n仅输出简短、优雅，不包含符号的新章节标题：'}
                    ], f'{volume_name} {chapter_dir.name} 章节名重复，重新取名')
                    prune_article_title = new_article_title.strip()
                    is_rename = True
                if is_rename:
                    chapter_dir.rename(
                        part_dir / f'{prune_article_order}-{prune_article_title}')
                used_article_title.add(prune_article_title)
                article_title = f'{prune_article_order} {prune_article_title}'
                if article_title in chapter_title_list:
                    continue
                print(f'上传章节：{volume_name}——{article_title}')
                client.publish_article(
                    book_id, volume_id, volume_name, article_title, article_content)
