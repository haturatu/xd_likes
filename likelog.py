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
            response = await request_func(*args, **kwargs)  # 非同期リクエストを待機
            if response:
                return response
        except ReadTimeout:
            logger.warning(f"Attempt {attempt + 1} failed due to ReadTimeout.")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
        await asyncio.sleep(RETRY_DELAY)
    raise Exception("Failed to fetch more tweets after retries.")

async def fetch_and_process_liked_tweets(user_id):
    all_tweets = []
    next_page = True

    while next_page:
        try:
            # お気に入りツイートを取得
            logger.info("Fetching page of liked tweets.")
            liked_tweets = await perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=40)
            if not liked_tweets:
                logger.warning("No liked tweets found or failed to fetch liked tweets.")
                break

            for tweet in liked_tweets:
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

            next_page = liked_tweets.next if hasattr(liked_tweets, 'next') else None

            if next_page:
                logger.info("Fetching next page of liked tweets.")
                await asyncio.sleep(2)  # APIリクエストの間隔

        except Exception as e:
            logger.error(f"Failed to fetch more liked tweets: {e}")
            break

async def main():
    # クッキーを使ってログイン
    try:
        client.load_cookies('cookies.json')  # 非同期ではない場合
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

    # ユーザのお気に入りツイートを取得し処理
    await fetch_and_process_liked_tweets(user_id)

# メイン関数を非同期で実行
asyncio.run(main())
