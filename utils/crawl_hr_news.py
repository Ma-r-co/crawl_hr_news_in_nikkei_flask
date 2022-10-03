
import requests
from bs4 import BeautifulSoup
import lxml.html
import time
import datetime
import random

def is_target_date(target_date: str, content_date: str):
    idx_hi: int = content_date.find('日')
    return idx_hi >= 0 and target_date == content_date[0:idx_hi]

# def is_GRCS_related(article: str):
#     return any(grcs_word in article for grcs_word in GRCS_WORDS)

BASE_URL: str = 'https://www.nikkei.com'
MAX_REQUESTS = 1000

TITLE_SELECTOR = '#CONTENTS_MAIN > section > ul:nth-of-type({}) > li:nth-of-type({}) > div > div.col.headline > h3 > a'
    ##CONTENTS_MAIN > section > ul:nth-child(2) > li:nth-child(1) > div > div.col.headline > h3 > a
CONTENT_DATE_SELECTOR = '#CONTENTS_MAIN > section > ul:nth-of-type({}) > li:nth-of-type({}) > div > div.col.time > p'
    ##CONTENTS_MAIN > section > ul:nth-child(2) > li:nth-child(1) > div > div.col.time > p
HR_CONTENT_XPATH = '/html/body/div[5]/main/article/section[1]'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
}
session = requests.Session()

def crawl_hr_news(TARGET_DATE: str, FI_WORDS: list) -> list:
    stage = 1  # stage: 1-TARGET_DATEに達していない状態, 2-達した状態
    result = []
    cnt = 0  # cnt: ループの回数を記録する
    for bn in range(1, 1982, 30):  # ページのURLが /?bn=31, /?bn=61のように30刻みとなっていることに対応
        time.sleep(random.randint(1, 2))
        soup = BeautifulSoup(session.get(BASE_URL+'/news/jinji/hatsurei/?bn='+str(bn), headers=HEADERS).text, features="lxml")
        for ul_num in range(1, 4):
            for li_num in range(1, 11):
                cnt += 1
                if cnt >= MAX_REQUESTS:  # 安全考慮
                    result.append('Too many requests > {}'.format(MAX_REQUESTS))
                    return result
                header = soup.select(TITLE_SELECTOR.format(ul_num, li_num))
                link, title = header[0].attrs['href'], header[0].contents[0].contents[0]

                time_box = soup.select(CONTENT_DATE_SELECTOR.format(ul_num, li_num))
                content_date = time_box[0].contents[0]
                
                print('\r                                                                                 \r', end='')
                print('   [{}] Checking - ({}) {}'.format(cnt, content_date, title), end='', flush=True)

                if is_target_date(TARGET_DATE, content_date):
                    stage = 2
                    if any(fi_word in title for fi_word in FI_WORDS):
                        time.sleep(random.randint(1, 2))
                        html = lxml.html.fromstring(session.get(BASE_URL+link, headers=HEADERS).text)
                        hr_article = html.xpath(HR_CONTENT_XPATH)[0].text_content()
                        result.append('[{}]({}) ({}) > {}'.format(title, BASE_URL + link, content_date, hr_article))

                else:
                    if stage == 2:
                        print('')
                        return result
    print('')
    return result
