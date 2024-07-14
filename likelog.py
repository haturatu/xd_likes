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

# ユーザの認証情報でログイン、初回時のみ
# client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
# client.save_cookies('cookies.json')

# クライアントの初期化
client = Client('en-US')

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

async def fetch_all_liked_tweets(user_id, max_tweets=5000):
    all_tweets = []
    cursor = None

    while len(all_tweets) < max_tweets:
        try:
            # お気に入りツイートを取得
            logger.info(f"Fetching liked tweets with cursor: {cursor}")
            result = await perform_request_with_retries(client.get_user_tweets, user_id=user_id, tweet_type='Likes', count=40, cursor=cursor)

            # 結果の内容をログに出力
            logger.info(f"Result object received: {result}")

            # ツイートリストとして直接使用
            liked_tweets = result

            if not liked_tweets:
                logger.warning("No liked tweets found or failed to fetch liked tweets.")
                break

            logger.info(f"Fetched {len(liked_tweets)} liked tweets.")
            all_tweets.extend(liked_tweets)

            # 収集したツイート数が最大件数に達しているかチェック
            if len(all_tweets) >= max_tweets:
                logger.info(f"Reached the maximum limit of {max_tweets} tweets.")
                break

            # 次のページがある場合は次のページを取得
            if hasattr(result, 'next'):
                logger.info("Fetching next page of liked tweets.")
                cursor = result.next_cursor if hasattr(result, 'next_cursor') else None

            else:
                logger.info("No more pages of liked tweets.")
                break

            await asyncio.sleep(2)  # APIリクエストの間隔を調整

        except Exception as e:
            logger.error(f"Failed to fetch more liked tweets: {e}")
            break

    return all_tweets[:max_tweets]

async def main():
    # クッキーを使ってログイン
    try:
        client.load_cookies('cookies.json') 
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return

    # 取得先のID
    user_screen_name = "get_likes_user_id"

    # ユーザIDの取得
    try:
        user = await perform_request_with_retries(client.get_user_by_screen_name, user_screen_name)
        if not user:
            raise Exception("Failed to fetch user information after retries.")
        user_id = user.id
    except Exception as e:
        logger.error(f"Failed to get user ID: {e}")
        return

    # ユーザのお気に入りツイートを取得
    all_tweets = await fetch_all_liked_tweets(user_id, max_tweets=5000)  # 最大5000件取得する設定

    total_tweets_fetched = len(all_tweets)

    # ツイートの詳細情報を取得しログに書き出し
    for tweet in all_tweets:
        await asyncio.sleep(2)

        try:
            tweet_details = await perform_request_with_retries(client.get_tweet_by_id, tweet.id)
            if tweet_details:
                author_username = tweet_details.user.screen_name
                logger.info(f"<Tweet id=\"{tweet_details.id}\", X id: \"{author_username}\", Text: \"{tweet_details.text}\">")
            else:
                logger.error("Failed to fetch tweet details after retries.")
        except Exception as e:
            logger.error(f"Failed to fetch tweet details: {e}")
            continue

        await asyncio.sleep(12)

    logger.info(f"Total tweets fetched: {total_tweets_fetched}")

# メイン関数を非同期で実行
asyncio.run(main())

