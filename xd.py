#!/usr/bin/python3
import os
import requests
import httpx
import asyncio
from urllib.parse import urlparse, parse_qs
from twikit import Client

# Twikit クライアントの初期化
client = Client('en-US')
client.load_cookies('cookies.json')

USER_SCREEN_NAMES = [
    'user_id', 'add_more'
]
SAVE_BASE_FOLDER = "./media"

def create_save_folder(screen_name):
    path = os.path.join(SAVE_BASE_FOLDER, "media", screen_name)
    os.makedirs(path, exist_ok=True)
    return path

def get_clean_url(url):
    parsed_url = urlparse(url)
    base_url = parsed_url.path
    return base_url

async def download_image(url, save_path):
    async with httpx.AsyncClient() as async_client:
        try:
            response = await async_client.get(url, timeout=10)
            response.raise_for_status()
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Image saved: {save_path}")
        except httpx.RequestError as e:
            print(f"Failed to download {url}: {e}")

async def process_user(screen_name):
    try:
        user = await client.get_user_by_screen_name(screen_name)
        save_folder = create_save_folder(screen_name)
        user_tweets = await user.get_tweets('Media')

        while user_tweets:
            for tweet in user_tweets:
                for media in tweet.media:
                    url = media['media_url_https']
                    if url.endswith('.jpg'):
                        url = url.replace('.jpg', '?format=jpg&name=orig')
                    clean_url = get_clean_url(url)
                    save_path = os.path.join(save_folder, f"{screen_name}_{clean_url.split('/')[-1]}.jpeg")
                    await download_image(url, save_path)

            user_tweets = await user_tweets.next()

    except Exception as e:
        print(f"Error processing {screen_name}: {e}")

async def main():
    await asyncio.gather(*(process_user(name) for name in USER_SCREEN_NAMES))

if __name__ == "__main__":
    asyncio.run(main())
