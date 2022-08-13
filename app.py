# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from utils.crawl_hr_news import crawl_hr_news
from datetime import datetime, timedelta
import os

DEFAULT_TARGET_DATE: str = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
DEFAULT_FI_WORDS = ['銀行', 'バンク', '金庫', '信金', '信用', '組合', 'ファイナンシャル', 'フィナンシャル', 'ファイナンス', '証券', '證券', '保険', '損保', '生命', '生保', '金融庁']


app = Flask(__name__)


@app.route('/', methods = ["GET" , "POST"]) #2 GETとPOSTをリクエストできるようにする
def index():
    if request.method == 'POST': #3POSTの処理
      target_date = request.form['target_date']
      fi_words = request.form['fi_words']
      result = crawl_hr_news(str(int(target_date.split('-')[-1])), fi_words.split(','))
      return render_template('index.html', target_date=target_date, fi_words=fi_words, result='\n'.join(result), result_count=len(result) )
    return render_template('index.html', target_date=DEFAULT_TARGET_DATE, fi_words=','.join(DEFAULT_FI_WORDS)) #6 GETの処理

if __name__ == '__main__':
    if os.getenv('FLASK_APP_ENV') == 'PRODUCTION':
        app.run()
    else:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True

