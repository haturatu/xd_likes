#!/usr/bin/python3
import os
import requests
import time
from twikit import Client
from httpx import ReadTimeout
from loguru import logger

# ログイン設定をここで行う
USERNAME = 'login_userid'
EMAIL = 'login_user_mail'
PASSWORD = 'login_user_pass'

# リトライ設定
RETRY_LIMIT = 5
RETRY_DELAY = 300

# Twikitクライアントの初期化
client = Client('en-US')

# サービスにユーザー資格情報でログイン
# client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
# client.save_cookies('cookies.json')
client.load_cookies('cookies.json')

# ユーザーのスクリーンネームを指定
user_screen_name = "ComingClean_17"

# リトライ時に実行させる関数
def perform_request_with_retries(request_func, *args, **kwargs):
    for attempt in range(RETRY_LIMIT):
        try:
            response = request_func(*args, **kwargs)
            if response:
                return response
        except ReadTimeout:
            logger.warning(f"Attempt {attempt + 1} failed due to ReadTimeout.")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(RETRY_DELAY)
    raise Exception("Failed to fetch more tweets after retries.")

# ユーザーIDの取得
user = perform_request_with_retries(client.get_user_by_screen_name, user_screen_name)
if not user:
    raise Exception("Failed to fetch user information after retries.")
user_id = user.id

# ユーザーのいいねしたツイートを取得
liked_tweets = perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=40)
if not liked_tweets:
    raise Exception("Failed to fetch liked tweets after retries.")

total_tweets_fetched = 0

# 初期バッチのツイートをループ処理
for tweet in liked_tweets:
    total_tweets_fetched += 1
    target_tweet_id = tweet.id
    time.sleep(2)

    tweet_details = perform_request_with_retries(client.get_tweet_by_id, target_tweet_id)
    if tweet_details:
        author_username = tweet_details.user.screen_name
        logger.info(f"<Tweet id=\"{tweet_details.id}\", X id: \"{author_username}\", Text: \"{tweet_details.text}\">")
    else:
        logger.error("Failed to fetch tweet details after retries.")

    time.sleep(12)

# 上限値を決め、更に取得する必要がある場合試行する
# この場合は5000件を取得する
while total_tweets_fetched < 5000:
    more_tweets = perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=40)
    if not more_tweets:
        logger.error("Failed to fetch more tweets after retries.")
        continue

    for tweet in more_tweets:
        total_tweets_fetched += 1
        target_tweet_id = tweet.id
        time.sleep(2)

        tweet_details = perform_request_with_retries(client.get_tweet_by_id, target_tweet_id)
        if tweet_details:
            author_username = tweet_details.user.screen_name
            logger.info(f"<Tweet id=\"{tweet_details.id}\", X id: \"{author_username}\", Text: \"{tweet_details.text}\">")
        else:
            logger.error("Failed to fetch tweet details after retries.")

        time.sleep(12)

        if total_tweets_fetched >= 5000:
            break

