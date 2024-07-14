#!/usr/bin/python3
import os
import httpx
import asyncio
from urllib.parse import urlparse
from twikit import Client

# Twikit クライアントの初期化
client = Client('en-US')
client.load_cookies('cookies.json')

# ファイルからユーザー名を読み込む
def load_usernames(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

# USER_SCREEN_NAMESにファイルから読み込んだユーザー名を代入
USER_SCREEN_NAMES = load_usernames('xids')

# 保存先フォルダを指定
SAVE_BASE_FOLDER = "/your/dir"

# リトライ設定
RETRY_LIMIT = 5
RETRY_DELAY = 900

def create_save_folder(screen_name):
    path = os.path.join(SAVE_BASE_FOLDER, "media", screen_name)
    os.makedirs(path, exist_ok=True)
    return path

def get_clean_url(url):
    parsed_url = urlparse(url)
    base_url = parsed_url.path
    return base_url

async def download_image(url, save_path):
    for attempt in range(RETRY_LIMIT):
        try:
            async with httpx.AsyncClient() as async_client:
                response = await async_client.get(url, timeout=10)
                response.raise_for_status()
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                print(f"Image saved: {save_path}")
                return 
        except httpx.RequestError as e:
            print(f"Attempt {attempt + 1} failed to download {url}: {e}")
            if attempt < RETRY_LIMIT - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"Failed to download {url} after {RETRY_LIMIT} attempts")

async def fetch_user_tweets(user, tweet_type):
    for attempt in range(RETRY_LIMIT):
        try:
            return await user.get_tweets(tweet_type)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed to fetch tweets: {e}")
            if attempt < RETRY_LIMIT - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"Failed to fetch tweets after {RETRY_LIMIT} attempts")
                return None 

async def process_user(screen_name):
    user = None
    try:
        user = await client.get_user_by_screen_name(screen_name)
    except Exception as e:
        print(f"Error retrieving user {screen_name}: {e}")
        return 
    
    save_folder = create_save_folder(screen_name)
    user_tweets = await fetch_user_tweets(user, 'Media')

    if user_tweets is None:
        print(f"Failed to fetch tweets for user {screen_name}. Skipping user.")
        return  

    while user_tweets:
        for tweet in user_tweets:
            if tweet.media is None:
                continue 

            for media in tweet.media:
                url = media.get('media_url_https')
                if url:
                    if url.endswith('.jpg'):
                        url = url.replace('.jpg', '?format=jpg&name=orig')
                    clean_url = get_clean_url(url)
                    save_path = os.path.join(save_folder, f"{screen_name}_{clean_url.split('/')[-1]}.jpeg")
                    await download_image(url, save_path)

        try:
            user_tweets = await user_tweets.next()
        except Exception as e:
            print(f"Error fetching next set of tweets for user {screen_name}: {e}")
            continue

async def process_batch(batch):
    await asyncio.gather(*(process_user(name) for name in batch))

async def main():
    batch_size = 10
    for i in range(0, len(USER_SCREEN_NAMES), batch_size):
        batch = USER_SCREEN_NAMES[i:i + batch_size]
        await process_batch(batch)

if __name__ == "__main__":
    asyncio.run(main())

