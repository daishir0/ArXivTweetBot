#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
import datetime
import argparse
import pandas as pd
from collections import defaultdict

def analyze_twitter_logs(log_dir):
    """
    Twitter投稿ログを分析する
    
    Args:
        log_dir (str): ログディレクトリのパス
        
    Returns:
        dict: 分析結果
    """
    # ログファイルを取得
    log_files = glob.glob(os.path.join(log_dir, "*_twitter_log.json"))
    
    if not log_files:
        print("ログファイルが見つかりません。")
        return None
    
    # 日付ごとの投稿数
    daily_posts = defaultdict(int)
    # 論文ごとの投稿情報
    paper_posts = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # タイムスタンプを解析
            timestamp = log_data.get('timestamp')
            if timestamp:
                date = timestamp.split()[0]  # YYYY-MM-DD部分を取得
                
                # エラーがない場合は投稿成功とみなす
                if 'error' not in log_data:
                    daily_posts[date] += 1
                    
                    # 論文情報を追加
                    paper_posts.append({
                        'date': date,
                        'title': log_data.get('title', 'Unknown'),
                        'status': 'Success',
                        'tweet_count': len(log_data.get('tweets', [])),
                        'timestamp': timestamp
                    })
                else:
                    # エラーがある場合
                    paper_posts.append({
                        'date': date,
                        'title': log_data.get('title', 'Unknown'),
                        'status': 'Failed',
                        'error': log_data.get('error', 'Unknown error'),
                        'tweet_count': len(log_data.get('tweets', [])),
                        'timestamp': timestamp
                    })
        except Exception as e:
            print(f"ログファイル {log_file} の解析中にエラーが発生しました: {str(e)}")
    
    # 結果を整形
    result = {
        'daily_posts': dict(daily_posts),
        'paper_posts': paper_posts,
        'total_posts': sum(daily_posts.values()),
        'total_days': len(daily_posts),
        'first_date': min(daily_posts.keys()) if daily_posts else None,
        'last_date': max(daily_posts.keys()) if daily_posts else None
    }
    
    return result

def generate_daily_summary(log_dir, output_file=None):
    """
    日次サマリーを生成する
    
    Args:
        log_dir (str): ログディレクトリのパス
        output_file (str, optional): 出力ファイルパス
        
    Returns:
        str: サマリーテキスト
    """
    result = analyze_twitter_logs(log_dir)
    
    if not result:
        return "データがありません。"
    
    # 日次サマリーを作成
    summary = "# Twitter投稿サマリー\n\n"
    summary += f"分析日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    summary += "## 投稿統計\n\n"
    summary += f"- 総投稿数: {result['total_posts']}件\n"
    summary += f"- 投稿日数: {result['total_days']}日\n"
    summary += f"- 初回投稿日: {result['first_date']}\n"
    summary += f"- 最終投稿日: {result['last_date']}\n\n"
    
    summary += "## 日別投稿数\n\n"
    summary += "日付 | 投稿数\n"
    summary += "---- | ------\n"
    
    # 日付でソート
    sorted_dates = sorted(result['daily_posts'].keys(), reverse=True)
    for date in sorted_dates:
        summary += f"{date} | {result['daily_posts'][date]}\n"
    
    summary += "\n## 最近の投稿\n\n"
    summary += "日時 | タイトル | 状態 | ツイート数\n"
    summary += "---- | ------- | ---- | ---------\n"
    
    # 最新の投稿10件を表示
    recent_posts = sorted(result['paper_posts'], key=lambda x: x['timestamp'], reverse=True)[:10]
    for post in recent_posts:
        status = "✅ 成功" if post['status'] == 'Success' else "❌ 失敗"
        summary += f"{post['timestamp']} | {post['title'][:50]}... | {status} | {post['tweet_count']}\n"
    
    # 出力ファイルに保存
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"サマリーを {output_file} に保存しました。")
    
    return summary

def export_to_csv(log_dir, output_file):
    """
    投稿ログをCSVファイルにエクスポートする
    
    Args:
        log_dir (str): ログディレクトリのパス
        output_file (str): 出力ファイルパス
    """
    result = analyze_twitter_logs(log_dir)
    
    if not result or not result['paper_posts']:
        print("エクスポートするデータがありません。")
        return
    
    # DataFrameに変換
    df = pd.DataFrame(result['paper_posts'])
    
    # CSVに保存
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"データを {output_file} にエクスポートしました。")

def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(
        description='Twitter投稿ログを分析し、サマリーを生成します。'
    )
    parser.add_argument(
        '--log-dir',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'),
        help='ログディレクトリのパス（デフォルト: logs/）'
    )
    parser.add_argument(
        '--output',
        help='サマリー出力ファイルのパス'
    )
    parser.add_argument(
        '--csv',
        help='CSVエクスポートファイルのパス'
    )
    
    args = parser.parse_args()
    
    # サマリーを生成
    summary = generate_daily_summary(args.log_dir, args.output)
    
    if not args.output:
        print(summary)
    
    # CSVにエクスポート
    if args.csv:
        export_to_csv(args.log_dir, args.csv)

if __name__ == "__main__":
    main()