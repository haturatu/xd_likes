#!/usr/bin/python3
import os
import httpx
import asyncio
from urllib.parse import urlparse
from twikit import Client

# ログイン設定をここで行う
USERNAME = 'login_userid'
EMAIL = 'login_user_mail'
PASSWORD = 'login_user_pass'

# Twikit クライアントの初期化
client = Client('en-US')

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
RETRY_DELAY = 900  # 秒

def create_save_folder(screen_name):
    path = os.path.join(SAVE_BASE_FOLDER, "media", screen_name)
    os.makedirs(path, exist_ok=True)
    return path

def get_clean_url(url):
    parsed_url = urlparse(url)
    base_url = parsed_url.path
    return base_url

async def download_image(url, save_path):
    if os.path.exists(save_path):
        print(f"Image already exists: {save_path}")
        return  # 既に画像が存在する場合はスキップ

    for attempt in range(RETRY_LIMIT):
        try:
            async with httpx.AsyncClient() as async_client:
                response = await async_client.get(url, timeout=10)
                response.raise_for_status()
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                print(f"Image saved: {save_path}")
                return  # 成功した場合、関数を終了
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Image not found (404): {url}")
                return  # 404エラーは無視して終了
            print(f"Attempt {attempt + 1} failed to download {url}: {e}")
            break  # 404以外のHTTPステータスエラーの場合、ループを抜ける
        except httpx.RequestError as e:
            print(f"Attempt {attempt + 1} failed to download {url}: {e}")
            break  # リクエストエラーの場合もループを抜ける

        if attempt < RETRY_LIMIT - 1:
            print(f"Retrying download for {url} after {RETRY_DELAY} seconds...")
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
                return None  # 最後のリトライでも失敗した場合は None を返す

async def process_user(screen_name):
    user = None
    try:
        user = await client.get_user_by_screen_name(screen_name)
    except Exception as e:
        print(f"Error retrieving user {screen_name}: {e}")
        return  # ユーザー情報の取得に失敗した場合は次のユーザーに進む
    
    save_folder = create_save_folder(screen_name)
    user_tweets = await fetch_user_tweets(user, 'Media')

    if user_tweets is None:
        print(f"Failed to fetch tweets for user {screen_name}. Skipping user.")
        return  # ツイート取得に失敗した場合は次のユーザーに進む

    module_items_error_count = 0

    while user_tweets:
        for tweet in user_tweets:
            if tweet.media is None:
                continue  # メディアがないツイートがある場合、次のツイートへ進む

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
            if "moduleItems" in str(e):
                module_items_error_count += 1
                if module_items_error_count >= 3:
                    print(f"Error fetching next set of tweets for user {screen_name}: 'moduleItems' error occurred 3 times. Skipping user.")
                    return
                continue
            break

async def process_batch(batch):
    await asyncio.gather(*(process_user(name) for name in batch))

async def main():
    # クッキーを使ってログイン
    try:
        # ユーザの認証情報でログイン、初回時のみ
        # await client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
        # client.save_cookies('cookies.json')
        # クッキーでロード
        client.load_cookies('cookies.json')
    except Exception as e:
        print(f"Failed to load cookies: {e}")
        return

    batch_size = 2
    for i in range(0, len(USER_SCREEN_NAMES), batch_size):
        batch = USER_SCREEN_NAMES[i:i + batch_size]
        await process_batch(batch)

if __name__ == "__main__":
    asyncio.run(main())


