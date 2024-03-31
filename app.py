# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from utils.crawl_hr_news import CrawlHrNewsInNikkei, CrawlHrNewsInNikkeiError
from datetime import datetime, timedelta
import os
import traceback

DEFAULT_TARGET_DATE: str = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
DEFAULT_FI_WORDS = ['銀行', 'バンク', '金庫', '信金', '信用', '組合', 'ファイナンシャル', 'フィナンシャル', 'ファイナンス', '証券', '證券', '保険', '損保', '生命', '生保', '金融庁']


app = Flask(__name__)


@app.route('/', methods = ["GET" , "POST"]) #2 GETとPOSTをリクエストできるようにする
def index():
    if request.method == 'POST': #3 POSTの処理
        base_url = 'https://www.nikkei.com'
        target_date = request.form['target_date']
        fi_words = request.form['fi_words']
        crawler = CrawlHrNewsInNikkei(base_url, fi_words.split(','), target_date)
        try:
            result_count, result = crawler.start_crawling()
        except CrawlHrNewsInNikkeiError as e:
            result_count, result = 0, "!"*50 + "\nエラーが発生しました\n" + "!"*50 + "\n\n" + traceback.format_exc()
        return render_template('index.html', target_date=target_date, fi_words=fi_words, result=result, result_count=result_count)
    return render_template('index.html', target_date=DEFAULT_TARGET_DATE, fi_words=','.join(DEFAULT_FI_WORDS)) #6 GETの処理

if __name__ == '__main__':
    if os.getenv('FLASK_APP_ENV') == 'PRODUCTION':
        app.run()
    else:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
        app.config['DEBUG'] = True
        app.run()

