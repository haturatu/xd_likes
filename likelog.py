#!/usr/bin/python3
import os
import requests
import time
import asyncio
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
# client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
# client.save_cookies('cookies.json')
client.load_cookies('cookies.json')

# 取得先のID
user_screen_name = "get_username"


# リトライ時に実行させる関数
async def perform_request_with_retries(request_func, *args, **kwargs):
    for attempt in range(RETRY_LIMIT):
        try:
            response = await request_func(*args, **kwargs)
            if response:
                return response
        except ReadTimeout:
            logger.warning(f"Attempt {attempt + 1} failed due to ReadTimeout.")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
        await asyncio.sleep(RETRY_DELAY)
    raise Exception("Failed to fetch more tweets after retries.")

async def main():
    # クッキーを使ってログイン
    try:
        client.load_cookies('cookies.json') 
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return

    # ユーザIDの取得
    try:
        user = await perform_request_with_retries(client.get_user_by_screen_name, user_screen_name)
        if not user:
            raise Exception("Failed to fetch user information after retries.")
        user_id = user.id
    except Exception as e:
        logger.error(f"Failed to get user ID: {e}")
        return

    # お気に入りツイートを取得
    try:
        liked_tweets = await perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=40)
        if not liked_tweets:
            raise Exception("Failed to fetch liked tweets after retries.")
    except Exception as e:
        logger.error(f"Failed to get liked tweets: {e}")
        return

    total_tweets_fetched = 0
    all_tweets = []

    # ループ処理
    while liked_tweets:
        for tweet in liked_tweets:
            all_tweets.append(tweet)
            total_tweets_fetched += 1
            target_tweet_id = tweet.id
            await asyncio.sleep(2)

            try:
                tweet_details = await perform_request_with_retries(client.get_tweet_by_id, target_tweet_id)
                if tweet_details:
                    author_username = tweet_details.user.screen_name
                    logger.info(f"<Tweet id=\"{tweet_details.id}\", X id: \"{author_username}\", Text: \"{tweet_details.text}\">")
                else:
                    logger.error("Failed to fetch tweet details after retries.")
            except Exception as e:
                logger.error(f"Failed to fetch tweet details: {e}")

            await asyncio.sleep(12)

        # さらにツイートを取得する
        if len(all_tweets) < 5000 and liked_tweets.next:
            try:
                liked_tweets = await perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=40)
                if not liked_tweets:
                    raise Exception("Failed to fetch more tweets after retries.")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Failed to fetch more tweets: {e}")
                break
        else:
            break

    logger.info(f"Total tweets fetched: {total_tweets_fetched}")

# メイン関数をasyncioで非同期で実行
asyncio.run(main())

