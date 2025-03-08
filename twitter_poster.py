#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import tweepy

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
        # Twitter APIの認証情報
        ck = config['api_key']
        cs = config['api_key_secret']
        at = config['access_token']
        ats = config['access_token_secret']
        
        # tweepy Clientを初期化
        client = tweepy.Client(
            consumer_key=ck,
            consumer_secret=cs,
            access_token=at,
            access_token_secret=ats
        )
        
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
        greeting_response = client.create_tweet(text=greeting_text)
        greeting_tweet_id = greeting_response.data['id']
        tweets.append({
            "type": "greeting",
            "id": greeting_tweet_id,
            "text": summary['greeting']
        })
        time.sleep(2)  # API制限回避のための待機
        
        # 2. 起のツイート
        logging.info(f"起のツイートを投稿中")
        ki_response = client.create_tweet(
            text=summary['ki'],
            in_reply_to_tweet_id=greeting_tweet_id
        )
        ki_tweet_id = ki_response.data['id']
        tweets.append({
            "type": "ki",
            "id": ki_tweet_id,
            "text": summary['ki']
        })
        time.sleep(2)
        
        # 3. 承のツイート
        logging.info(f"承のツイートを投稿中")
        sho_response = client.create_tweet(
            text=summary['sho'],
            in_reply_to_tweet_id=ki_tweet_id
        )
        sho_tweet_id = sho_response.data['id']
        tweets.append({
            "type": "sho",
            "id": sho_tweet_id,
            "text": summary['sho']
        })
        time.sleep(2)
        
        # 4. 転のツイート
        logging.info(f"転のツイートを投稿中")
        ten_response = client.create_tweet(
            text=summary['ten'],
            in_reply_to_tweet_id=sho_tweet_id
        )
        ten_tweet_id = ten_response.data['id']
        tweets.append({
            "type": "ten",
            "id": ten_tweet_id,
            "text": summary['ten']
        })
        time.sleep(2)
        
        # 5. 結のツイート
        logging.info(f"結のツイートを投稿中")
        ketsu_response = client.create_tweet(
            text=summary['ketsu'],
            in_reply_to_tweet_id=ten_tweet_id
        )
        ketsu_tweet_id = ketsu_response.data['id']
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