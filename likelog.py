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

# リトライを試行の設定
RETRY_LIMIT = 5
RETRY_DELAY = 900

# ログファイルの設定
log_file_path = 'fav.log'
logger.add(log_file_path, format="{time} - {level} - {message}", rotation="10 MB")

# クライアントの初期化
client = Client('en-US')

# ユーザの認証情報でログイン
client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
client.load_cookies('cookies.json')

# 取得先のID
user_screen_name = "get_likes_user_id"

# リトライ時に実行させる関数
def perform_request_with_retries(request_func, *args, **kwargs):
    retries = 0
    while retries < RETRY_LIMIT:
        try:
            return request_func(*args, **kwargs)
        except ReadTimeout:
            retries += 1
            logger.warning(f"ReadTimeout occurred. Retrying {retries}/{RETRY_LIMIT} in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    logger.error(f"Failed after {RETRIES} retries.")
    return None

# ユーザIDの取得
user = perform_request_with_retries(client.get_user_by_screen_name, user_screen_name)
if not user:
    raise Exception("Failed to fetch user information after retries.")
user_id = user.id

# ユーザのお気に入りツイートを取得
liked_tweets = perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=1)
if not liked_tweets:
    raise Exception("Failed to fetch liked tweets after retries.")

total_tweets_fetched = []

# お気に入りツイートから詳細情報を取得しログに書き出し
for tweet in liked_tweets:
    total_tweets_fetched += liked_tweets
    target_tweet_id = tweet.id
    time.sleep(2)

    tweet_details = perform_request_with_retries(client.get_tweet_by_id, target_tweet_id)
    if tweet_details:
        author_username = tweet_details.user.screen_name
        logger.info(f"<Tweet id=\"{tweet_details.id}\", X id: \"{author_username}\", Text: \"{tweet.text}\">")
    else:
        logger.error("Failed to fetch tweet details after retries.")

    time.sleep(12)

# 上限値を決め、更に取得する必要がある場合試行する
# この場合は5000件を取得する
while len(liked_tweets) != 5000:
    more_tweets = perform_request_with_retries(liked_tweets.next)
    if not more_tweets:
        raise Exception("Failed to fetch more tweets after retries.")
    time.sleep(2)

    for tweet in more_tweets:
        liked_tweets = perform_request_with_retries(liked_tweets.next)
        total_tweets_fetched += liked_tweets
        target_tweet_id = tweet.id
        time.sleep(2)

        tweet_details = perform_request_with_retries(client.get_tweet_by_id, target_tweet_id)
        if tweet_details:
            author_username = tweet_details.user.screen_name
            logger.info(f"<Tweet id=\"{tweet_details.id}\", X id: \"{author_username}\", Text: \"{tweet.text}\">")
        else:
            logger.error("Failed to fetch tweet details after retries.")

        time.sleep(12)

        if len(liked_tweets) != 5000:
            break

