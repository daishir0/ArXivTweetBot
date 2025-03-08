#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import arxiv
import requests
import os
import sys
import time
import argparse
import yaml
import logging
import json
import tweepy
from pathlib import Path
from urllib.parse import urlparse
from openai import OpenAI

# 追加モジュールをインポート
from pdf_processor import extract_text_from_pdf
from ai_summarizer import generate_summary
from twitter_poster import post_thread

def load_config():
    """
    設定ファイルを読み込む
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_directories():
    """
    必要なディレクトリを作成
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = {
        'dl': os.path.join(base_dir, 'dl'),
        'text': os.path.join(base_dir, 'text'),
        'summary': os.path.join(base_dir, 'summary'),
        'processed': os.path.join(base_dir, 'processed'),
        'logs': os.path.join(base_dir, 'logs')
    }
    
    for dir_name, dir_path in dirs.items():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs

def setup_logging(log_dir):
    """
    ロギングを設定
    """
    log_file = os.path.join(log_dir, f"arxiv_downloader_{time.strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def is_processed(arxiv_id, processed_dir):
    """
    論文が既に処理済みかどうかを確認
    """
    processed_file = os.path.join(processed_dir, f"{arxiv_id}.json")
    return os.path.exists(processed_file)

def mark_as_processed(arxiv_id, paper_title, processed_dir):
    """
    論文を処理済みとしてマーク
    """
    processed_file = os.path.join(processed_dir, f"{arxiv_id}.json")
    data = {
        "arxiv_id": arxiv_id,
        "title": paper_title,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def search_arxiv(keywords, max_results=100, use_or=False):
    """
    arXivで指定されたキーワードを使用して論文を検索します。
    
    Args:
        keywords (list): 検索キーワードのリスト
        max_results (int): 取得する最大論文数
        use_or (bool): キーワードをORで結合するかどうか
    
    Returns:
        list: 検索結果の論文リスト
    """
    logging.info(f"キーワード '{' '.join(keywords)}' でarXivを検索中...")
    
    # 検索クエリを作成
    if use_or:
        query = ' OR '.join(keywords)
    else:
        query = ' AND '.join(keywords)
    
    # arXivクライアントを作成
    client = arxiv.Client()
    
    # 検索オブジェクトを作成
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    # 結果を取得
    results = list(client.results(search))
    
    logging.info(f"{len(results)}件の論文が見つかりました。")
    return results

def download_pdf(paper, download_dir, force_download=False):
    """
    論文のPDFをダウンロードします。
    
    Args:
        paper (arxiv.Result): 論文情報
        download_dir (str): ダウンロード先ディレクトリ
        force_download (bool): 既存のファイルを上書きするかどうか
    
    Returns:
        tuple: (成功したかどうか, ダウンロードパス, arXiv ID)
    """
    # PDFのURLを取得
    pdf_url = paper.pdf_url
    
    # ファイル名を作成（arXiv IDを使用）
    parsed_url = urlparse(pdf_url)
    path_parts = parsed_url.path.split('/')
    arxiv_id = path_parts[-1]
    if not arxiv_id.endswith('.pdf'):
        arxiv_id = f"{arxiv_id}.pdf"
    
    # arXiv IDから拡張子を除去（処理済みチェック用）
    arxiv_id_without_ext = os.path.splitext(arxiv_id)[0]
    
    # ダウンロード先のパスを作成
    download_path = os.path.join(download_dir, arxiv_id)
    
    # 既にファイルが存在する場合はスキップ（force_downloadがFalseの場合）
    if os.path.exists(download_path) and not force_download:
        logging.info(f"ファイル {arxiv_id} は既に存在します。スキップします。")
        return True, download_path, arxiv_id_without_ext
    
    try:
        # PDFをダウンロード
        logging.info(f"ダウンロード中: {paper.title} ({arxiv_id})")
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        # ファイルに保存
        with open(download_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"ダウンロード完了: {download_path}")
        return True, download_path, arxiv_id_without_ext
    
    except Exception as e:
        logging.error(f"ダウンロード失敗: {arxiv_id} - エラー: {str(e)}")
        return False, None, arxiv_id_without_ext

def process_paper(paper, dirs, openai_client, config, force_process=False, skip_twitter=False):
    """
    論文を処理する（ダウンロード、テキスト抽出、要約生成、Twitter投稿）
    
    Args:
        paper (arxiv.Result): 論文情報
        dirs (dict): ディレクトリパス
        openai_client (OpenAI): OpenAIクライアント
        config (dict): 設定情報
        force_process (bool): 処理済みの論文も強制的に処理するかどうか
        skip_twitter (bool): Twitter投稿をスキップするかどうか
    
    Returns:
        bool: 処理が成功したかどうか
    """
    # 1. PDFをダウンロード
    success, pdf_path, arxiv_id = download_pdf(paper, dirs['dl'])
    if not success:
        return False
    
    # 2. 処理済みかどうかを確認
    if is_processed(arxiv_id, dirs['processed']) and not force_process:
        logging.info(f"論文 {arxiv_id} は既に処理済みです。スキップします。")
        return True
    
    # 3. PDFからテキストを抽出
    text_path = extract_text_from_pdf(pdf_path, dirs['text'])
    if not text_path:
        return False
    
    # 4. テキストを読み込み
    with open(text_path, 'r', encoding='utf-8') as f:
        paper_text = f.read()
    
    # 5. 要約を生成
    summary = generate_summary(
        openai_client,
        paper_text,
        config['prompt']['template'],
        dirs['summary'],
        paper.title
    )
    if not summary:
        return False
    
    # arXiv IDを追加
    summary['arxiv_id'] = arxiv_id
    
    # 6. Twitterに投稿（スキップオプションがない場合のみ）
    if not skip_twitter:
        success = post_thread(config['twitter'], summary, dirs['logs'])
        if not success:
            logging.warning(f"Twitter投稿に失敗しましたが、処理は続行します: {paper.title}")
    else:
        logging.info(f"Twitter投稿をスキップしました: {paper.title}")
    
    # 7. 処理済みとしてマーク
    mark_as_processed(arxiv_id, paper.title, dirs['processed'])
    
    return True

def main():
    """
    メイン関数
    """
    # コマンドライン引数のパーサーを設定
    parser = argparse.ArgumentParser(
        description='arXivから指定したキーワードで論文を検索し、PDFをダウンロード、要約してTwitterに投稿します。'
    )
    parser.add_argument(
        'keywords',
        nargs='+',
        help='検索キーワード（複数指定可能）'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=200,
        help='取得する最大論文数（デフォルト: 200）'
    )
    parser.add_argument(
        '--use-or',
        action='store_true',
        help='キーワードをORで結合する（デフォルトはAND）'
    )
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='既にダウンロード済みのファイルも再ダウンロードする'
    )
    parser.add_argument(
        '--force-process',
        action='store_true',
        help='既に処理済みの論文も再処理する'
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='テストモード：未処理の論文を1つだけ処理する'
    )
    parser.add_argument(
        '--skip-twitter',
        action='store_true',
        help='Twitter投稿をスキップする'
    )
    parser.add_argument(
        '--max-process',
        type=int,
        default=4,
        help='1回の実行で処理する論文の最大数（デフォルト: 4）'
    )
    
    # 引数を解析
    args = parser.parse_args()
    
    # ディレクトリを設定
    dirs = setup_directories()
    
    # ロギングを設定
    setup_logging(dirs['logs'])
    
    # 設定を読み込み
    config = load_config()
    
    # OpenAIクライアントを初期化
    openai_client = OpenAI(api_key=config['openai']['api_key'])
    
    # arXivを検索
    papers = search_arxiv(args.keywords, args.max_results, args.use_or)
    
    if not papers:
        logging.info("論文が見つかりませんでした。")
        sys.exit(0)
    
    # 論文情報を表示
    logging.info("\n検索結果:")
    for i, paper in enumerate(papers, 1):
        logging.info(f"{i}. {paper.title} ({paper.published.year})")
    
    # 論文を処理
    logging.info("\n論文の処理を開始します...")
    processed_count = 0
    
    # 処理する論文の最大数
    max_process_count = 1 if args.test_mode else args.max_process
    
    for paper in papers:
        # 最大処理数に達した場合は終了
        if processed_count >= max_process_count:
            logging.info(f"最大処理数 {max_process_count} に達しました。処理を終了します。")
            break
        
        # 論文を処理
        if process_paper(paper, dirs, openai_client, config, args.force_process, args.skip_twitter):
            processed_count += 1
        
        # arXivのAPIレート制限を回避するために少し待機
        time.sleep(1)
    
    logging.info(f"\n処理完了: {processed_count}/{len(papers)}件の論文を処理しました。")

if __name__ == "__main__":
    main()
