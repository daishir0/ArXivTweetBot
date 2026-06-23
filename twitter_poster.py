#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import requests
import tweepy

DEFAULT_XQUIK_API_BASE_URL = "https://xquik.com/api/v1"


def get_twitter_backend(config):
    """
    Twitter投稿バックエンドを検証して返す
    """
    backend = config.get('backend', 'x-api')
    if backend not in ('x-api', 'xquik'):
        raise ValueError(f"Unsupported twitter backend: {backend}")
    return backend


def get_required_xquik_config(config):
    """
    Xquik投稿に必要な設定を検証して返す
    """
    xquik_config = config.get('xquik', {})
    missing_fields = [
        field for field in ('account', 'api_key')
        if not xquik_config.get(field)
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"Missing required twitter.xquik config field(s): {missing}")
    return xquik_config


def create_twitter_client(config):
    """
    Tweepyクライアントを初期化する
    """
    return tweepy.Client(
        consumer_key=config['api_key'],
        consumer_secret=config['api_key_secret'],
        access_token=config['access_token'],
        access_token_secret=config['access_token_secret']
    )


def post_xquik_tweet(config, text, in_reply_to_tweet_id=None):
    """
    Xquik APIでツイートを投稿する
    """
    xquik_config = get_required_xquik_config(config)
    payload = {
        "account": xquik_config['account'],
        "text": text
    }
    if in_reply_to_tweet_id:
        payload["reply_to_tweet_id"] = str(in_reply_to_tweet_id)

    response = requests.post(
        f"{xquik_config.get('api_base_url', DEFAULT_XQUIK_API_BASE_URL).rstrip('/')}/x/tweets",
        headers={
            "Content-Type": "application/json",
            "x-api-key": xquik_config['api_key']
        },
        json=payload,
        timeout=30
    )
    if response.status_code not in (200, 202):
        raise RuntimeError(f"Xquik post failed with status {response.status_code}: {response.text[:300]}")

    data = response.json()
    tweet_id = data.get("tweetId")
    if tweet_id:
        return str(tweet_id)

    write_action_id = data.get("writeActionId")
    if write_action_id:
        raise RuntimeError(
            "Xquik accepted the tweet, but confirmation is pending. "
            f"Thread replies require a confirmed tweet ID. writeActionId={write_action_id}"
        )

    raise RuntimeError("Xquik response did not include tweetId or writeActionId")


def post_tweet(config, client, text, in_reply_to_tweet_id=None):
    """
    設定されたバックエンドでツイートを投稿し、ツイートIDを返す
    """
    backend = get_twitter_backend(config)
    if backend == 'xquik':
        return post_xquik_tweet(config, text, in_reply_to_tweet_id)

    response = client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to_tweet_id)
    return response.data['id']

def post_thread(config, summary, log_dir):
    """
    要約をTwitterスレッドとして投稿する
    
    Args:
        config (dict): Twitter API設定（APIキー、トークンなど）
        summary (dict): 投稿する要約
        log_dir (str): ログ出力先ディレクトリ
    
    Returns:
        bool: 投稿が成功したかどうか
    """
    # ログファイルパス
    log_path = os.path.join(log_dir, f"{summary['title'].replace(' ', '_')[:30]}_twitter_log.json")
    
    try:
        backend = get_twitter_backend(config)
        if backend == 'xquik':
            get_required_xquik_config(config)
            client = None
        else:
            client = create_twitter_client(config)
        
        tweets = []
        
        # arXiv IDを取得（ファイル名から）
        arxiv_id = None
        if 'arxiv_id' in summary:
            arxiv_id = summary['arxiv_id']
        
        # 1. 挨拶ツイート（改行とarXivのURLを追加）
        # 挨拶文を直接フォーマット
        paper_title = summary['title']
        greeting_part = summary['greeting'].split("だよ！")[0] + "だよ！" if "だよ！" in summary['greeting'] else summary['greeting']
        
        # 改行を入れた挨拶文を作成
        greeting_text = f"C(＾▽＾ )つ みんなー！\n今日は論文「{paper_title}」について起承転結で解説します！\n\n{greeting_part}"
        
        # タイトルが長い場合は短縮
        if len(greeting_text) > 120:  # URLの長さを考慮
            max_title_length = 50
            if len(paper_title) > max_title_length:
                short_title = paper_title[:max_title_length-3] + "..."
                greeting_text = f"C(＾▽＾ )つ みんなー！\n今日は論文「{short_title}」について起承転結で解説します！\n\n{greeting_part}"
        
        # arXivのURLを追加
        if arxiv_id:
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
            greeting_text += f"\n\n{arxiv_url}"
        
        logging.info(f"挨拶ツイートを投稿中: {greeting_text}")
        greeting_tweet_id = post_tweet(config, client, greeting_text)
        tweets.append({
            "type": "greeting",
            "id": greeting_tweet_id,
            "text": summary['greeting']
        })
        time.sleep(2)  # API制限回避のための待機
        
        # 2. 起のツイート
        logging.info(f"起のツイートを投稿中")
        ki_tweet_id = post_tweet(config, client, summary['ki'], greeting_tweet_id)
        tweets.append({
            "type": "ki",
            "id": ki_tweet_id,
            "text": summary['ki']
        })
        time.sleep(2)
        
        # 3. 承のツイート
        logging.info(f"承のツイートを投稿中")
        sho_tweet_id = post_tweet(config, client, summary['sho'], ki_tweet_id)
        tweets.append({
            "type": "sho",
            "id": sho_tweet_id,
            "text": summary['sho']
        })
        time.sleep(2)
        
        # 4. 転のツイート
        logging.info(f"転のツイートを投稿中")
        ten_tweet_id = post_tweet(config, client, summary['ten'], sho_tweet_id)
        tweets.append({
            "type": "ten",
            "id": ten_tweet_id,
            "text": summary['ten']
        })
        time.sleep(2)
        
        # 5. 結のツイート
        logging.info(f"結のツイートを投稿中")
        ketsu_tweet_id = post_tweet(config, client, summary['ketsu'], ten_tweet_id)
        tweets.append({
            "type": "ketsu",
            "id": ketsu_tweet_id,
            "text": summary['ketsu']
        })
        
        # ログを保存
        log_data = {
            "title": summary['title'],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tweets": tweets
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Twitter投稿成功: {summary['title']}")
        return True
    
    except Exception as e:
        logging.error(f"Twitter投稿エラー: {str(e)}")
        
        # エラーの詳細情報を取得
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Twitter APIレスポンス: {e.response.text}")
        
        # エラーログを保存
        error_log = {
            "title": summary['title'],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e),
            "tweets": tweets if 'tweets' in locals() else []
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, ensure_ascii=False, indent=2)
        
        return False
