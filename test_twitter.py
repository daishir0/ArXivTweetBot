#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import yaml

def main():
    # config.yamlから設定を読み込む
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Twitter APIの設定
    ck = config['twitter']['api_key']
    cs = config['twitter']['api_key_secret']
    at = config['twitter']['access_token']
    ats = config['twitter']['access_token_secret']
    
    # Clientを初期化
    client = tweepy.Client(
        consumer_key=ck,
        consumer_secret=cs,
        access_token=at,
        access_token_secret=ats
    )
    
    # テスト投稿
    response = client.create_tweet(text="テスト投稿です。このツイートはすぐに削除されます。")
    print(f"投稿成功: {response}")
    
    # 投稿したツイートのIDを取得
    tweet_id = response.data['id']
    
    # 投稿したツイートを削除
    client.delete_tweet(tweet_id)
    print(f"ツイート削除成功: {tweet_id}")

if __name__ == "__main__":
    main()