import requests
from bs4 import BeautifulSoup, Tag
import datetime
import time
import random
import re
from zoneinfo import ZoneInfo
from typing import Literal, Union

class CrawlHrNewsInNikkeiError(Exception):
    pass

class CrawlHrNewsInNikkei():
    def __init__(self, base_url: str, fi_words: list[str], target_date: str, max_requests: int = 1000, max_pages: int = 100, max_duration: Union[int,float] = 300):
        '''
        max_requests: Webサイトに負荷をかけすぎないように最大のリクエスト数を定める。デフォルトは1000。
        max_pages: page番号の最大値を定める。デフォルトは100(Webサイトの仕様制約)。
        max_duration: 処理の最大時間秒数。この時間を過ぎると処理結果を途中で返す。デフォルトは5分(300秒)。
        '''
        self.HTTP_HEADERS: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip" 
        }
        self.BASE_URL: str = base_url
        self.FI_WORDS: list[str] = fi_words
        self.TARGET_DATE: datetime.date = datetime.datetime.strptime(target_date + '+0900', r'%Y-%m-%d%z').date()
        self.MAX_REQUESTS: int = max_requests
        self.MAX_PAGES: int = max_pages
        self.MAX_DURATION: float = float(max_duration) 
        self.ZONE_INFO: ZoneInfo = ZoneInfo("Asia/Tokyo")
        self.result: list[str] = []
        self.starting_page_no: int = 1
        self.request_cnt: int = 0
        self.crawling_status: int = 0  # 0: 実行中以外, 1: 実行を継続, 2: 実行を終わる
        
    def _compare_to_target_date(self, hatsurei_date: datetime.datetime) -> Literal['earlier', 'later', 'same']:
        if hatsurei_date.date() < self.TARGET_DATE:
            return "earlier"
        elif hatsurei_date.date() > self.TARGET_DATE:
            return 'later'
        else:
            return 'same'

    def _is_financial_institution(self, title: str):
        return any(fi_word in title for fi_word in self.FI_WORDS)

    def _scrape_jinji_cards(self, session: requests.Session, page: int) -> list[Tag]:
        '''
        "https://www.nikkei.com/news/jinji/hatsurei/?page={page}"のHTMLを取得し、jinjiCard部分を抜き出す

        '''
        self.request_cnt += 1
        try:
            soup = BeautifulSoup(session.get(self.BASE_URL+'/news/jinji/hatsurei/?page='+str(page), headers=self.HTTP_HEADERS).text, 'html.parser')
        except Exception as ex:
            raise CrawlHrNewsInNikkeiError(f"{self.BASE_URL+'/news/jinji/hatsurei/?page='+str(page)}へのリクエストまたはパースに失敗しました。")
        
        return soup.find_all('article', attrs={'class': re.compile(r'^jinjiCard[\w]+$')})

    def _scrape_jinji_article(self, session: requests.Session, href: str) -> list[Tag]:
        '''
        "https://www.nikkei.com/article/XXXXXXXXXX/"のHTMLを取得し、paragraph部分を抜き出す

        '''
        self.request_cnt += 1
        try:
            soup = BeautifulSoup(session.get(self.BASE_URL + href, headers=self.HTTP_HEADERS).text, 'html.parser')
        except Exception as ex:
            raise CrawlHrNewsInNikkeiError(f"{self.BASE_URL + href}へのリクエストまたはパースに失敗しました。")
        return soup.find_all('p', {'class': re.compile(r'^paragraph_[\w]+$')})

    def _get_starting_page_no(self, session: requests.Session) -> int:
        '''
        Crawlingをスタートするページを見つける
        - 1ページ目がスタート対象であるかをチェック。対象であれば1を返す
        - 指定した日付が１ページ目にのっている最新の日付よりも新しい場合は1を返す
        - 違う場合は2分探索により見つける
        '''
        print(f"Checking page-{1}")
        jinji_cards = self._scrape_jinji_cards(session, 1)
        for jinji_card in jinji_cards:
            el_time = jinji_card.find('time')
            el_time_datetime = datetime.datetime.fromisoformat(el_time.get('datetime').replace('Z', '+00:00')).astimezone(self.ZONE_INFO)
            if el_time_datetime.date() <= self.TARGET_DATE:
                return 1

        def solve(n):
            print(f"Checking page-{n}")
            time.sleep(random.random())
            jinji_cards = self._scrape_jinji_cards(session, n)
            if jinji_cards:
                jinji_card = jinji_cards[-1]
                el_time = jinji_card.find('time')
                el_time_datetime = datetime.datetime.fromisoformat(el_time.get('datetime').replace('Z', '+00:00')).astimezone(self.ZONE_INFO)
                return el_time_datetime.date() <= self.TARGET_DATE
            else:
                return True

        # [ok, ng) - Maximum
        # (ng, ok] - Minimum
        # ok が 最終的な答え
        ok = self.MAX_PAGES
        ng = 0
        while abs(ok - ng) > 1:
            mid = (ok + ng) // 2
            if solve(mid):
                ok = mid
            else:
                ng = mid
        return ok

    def start_crawling(self) -> tuple[int, str]:
        start_datetime = datetime.datetime.now(self.ZONE_INFO)
        self.crawling_status = 1
        self.result.clear()
        with requests.session() as session:
            self.starting_page_no = self._get_starting_page_no(session)
            for page in range(self.starting_page_no, self.MAX_PAGES + 1):
                print(f'Starting page-{page}', flush=True)
                time.sleep(2 * random.random())
                jinji_cards = self._scrape_jinji_cards(session, page)
                for jinji_card in jinji_cards:
                    el_time = jinji_card.find('time')
                    el_time_datetime = datetime.datetime.fromisoformat(el_time.get('datetime').replace('Z', '+00:00')).astimezone(self.ZONE_INFO)
                    el_a = jinji_card.find('a', attrs={'class': re.compile(r'^fauxBlockLink_[\w]+$')})
                    el_a_text = el_a.text
                    el_a_href = el_a.get('href')
                    date_comparison_result = self._compare_to_target_date(el_time_datetime)
                    if date_comparison_result == 'same':  # targe_dateと同じ日付であればリンク先をスクレイピングする
                        if self._is_financial_institution(el_a_text):
                            self.result.append(f'**[{el_a_text}]({self.BASE_URL + el_a_href}) ({el_time_datetime.strftime(r"%m/%d %H:%M")})**')
                            time.sleep(2 * random.random())
                            paragraphs = self._scrape_jinji_article(session, el_a_href)
                            for paragraph in paragraphs:
                                self.result.extend(paragraph.text.split('▽'))
                    elif date_comparison_result == 'later':  # target_dateよりも後の日付の場合、何も処理は行わず次の要素に進む
                        continue
                    elif date_comparison_result == 'earlier':  # target_dateよりも前の日付の場合、crawlingを終了する
                        self.crawling_status = 2
                        break
                    
                    # MAX_REQUESTSを超過した場合
                    if self.request_cnt > self.MAX_REQUESTS:
                        self.crawling_status = 2
                        self.result = ["!" * 50, f"リクエスト数の最大値 {self.MAX_REQUESTS} を超過したため処理を途中で中断しました", "!" * 50] + self.result
                        break

                    # MAX_DURATIONを超過した場合
                    if (datetime.datetime.now(self.ZONE_INFO) - start_datetime).total_seconds() > self.MAX_DURATION:
                        self.crawling_status = 2
                        self.result = ["!" * 50, f"処理時間の最大秒数 {self.MAX_DURATION} を超過したため処理を途中で中断しました", "!" * 50] + self.result
                        break

                if self.crawling_status == 2:
                    break

        self.crawling_status = 0
        if self.result:
            return len(self.result), '\n'.join(self.result)
        else:
            return 0, "結果は0件でした"
