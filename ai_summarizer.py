#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
from openai import OpenAI

def generate_summary(client, text, prompt_template, output_dir, paper_title):
    """
    論文テキストから起承転結形式の要約を生成する
    
    Args:
        client (OpenAI): OpenAIクライアント
        text (str): 論文テキスト
        prompt_template (str): プロンプトテンプレート
        output_dir (str): 出力先ディレクトリ
        paper_title (str): 論文タイトル
    
    Returns:
        dict: 生成された要約（起承転結）と挨拶文
    """
    # ファイル名を作成
    filename = paper_title.replace(" ", "_").replace("/", "_")[:50]
    output_path = os.path.join(output_dir, f"{filename}.json")
    
    try:
        # プロンプトを作成
        prompt = prompt_template.replace("{論文テキスト}", text)
        
        # OpenAI APIを呼び出し - リトライロジックを追加
        max_retries = 3
        retry_count = 0
        backoff_time = 2  # 初期バックオフ時間（秒）
        
        while retry_count < max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "あなたは研究論文を中学生向けにわかりやすく解説する研究者です。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000
                )
                break  # 成功したらループを抜ける
            except Exception as api_error:
                retry_count += 1
                if retry_count >= max_retries:
                    raise  # 最大リトライ回数に達したら例外を再スロー
                
                # エラーの種類に応じてバックオフ時間を調整
                if hasattr(api_error, 'status_code') and api_error.status_code == 429:
                    logging.warning(f"API制限エラー（429）が発生しました。{backoff_time}秒後にリトライします。({retry_count}/{max_retries})")
                else:
                    logging.warning(f"APIエラーが発生しました: {str(api_error)}。{backoff_time}秒後にリトライします。({retry_count}/{max_retries})")
                
                time.sleep(backoff_time)
                backoff_time *= 2  # 指数バックオフ
        
        # 応答から起承転結を抽出
        summary_text = response.choices[0].message.content
        
        # 起承転結を分割（改行や「起:」「承:」などの記号で分割）
        parts = []
        current_part = ""
        current_section = None
        lines = summary_text.split('\n')
        
        # 起承転結のマーカーパターン
        markers = {
            "起": ["起:", "起：", "【起】", "起 ", "# 起", "## 起", "### 起"],
            "承": ["承:", "承：", "【承】", "承 ", "# 承", "## 承", "### 承"],
            "転": ["転:", "転：", "【転】", "転 ", "# 転", "## 転", "### 転"],
            "結": ["結:", "結：", "【結】", "結 ", "# 結", "## 結", "### 結"]
        }
        
        # 各行を処理
        for line in lines:
            line = line.strip()
            
            # 各セクションのマーカーを検出
            found_marker = False
            for section, section_markers in markers.items():
                if any(line.lower().find(marker.lower()) != -1 for marker in section_markers):
                    if current_section != section:  # 新しいセクションの開始
                        current_section = section
                        current_part = line
                        parts.append(current_part)
                        found_marker = True
                        break
            
            # マーカーが見つからなかった場合は既存のパートに追加
            if not found_marker and current_part and line:
                parts[-1] += " " + line
        
        # 起承転結の順序を確保
        ordered_parts = ["", "", "", ""]
        for part in parts:
            part_lower = part.lower()
            if any(marker.lower() in part_lower for marker in markers["起"]):
                ordered_parts[0] = part
            elif any(marker.lower() in part_lower for marker in markers["承"]):
                ordered_parts[1] = part
            elif any(marker.lower() in part_lower for marker in markers["転"]):
                ordered_parts[2] = part
            elif any(marker.lower() in part_lower for marker in markers["結"]):
                ordered_parts[3] = part
        
        # 空のパートを「情報が不足しています」で埋める
        parts = [part if part else "情報が不足しています。" for part in ordered_parts]
        
        # 各パートを140文字以内に制限（マークダウン見出しを除く）
        for i in range(len(parts)):
            # マークダウン見出しを抽出
            heading = ""
            content = parts[i]
            
            # マークダウン見出しのパターンを検出
            heading_match = None
            if content.startswith("##"):
                heading_match = content.split("\n")[0] if "\n" in content else content
                content = content[len(heading_match):].strip()
                heading = heading_match + "\n"
            
            # 本文を140文字以内に制限（見出しを除く）
            max_content_length = 140 - len(heading.strip())
            if len(content) > max_content_length:
                content = content[:max_content_length-3] + "..."
            
            # 見出しと本文を結合
            parts[i] = heading + content
        
        # 挨拶文を生成 - リトライロジックを追加
        greeting_prompt = f"論文「{paper_title}」について、中学生が興味を持つような短い一言を考えて。「だよ！」で終わる文にして。"
        
        retry_count = 0
        backoff_time = 2  # 初期バックオフ時間（秒）
        
        while retry_count < max_retries:
            try:
                greeting_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": greeting_prompt}
                    ],
                    max_tokens=100
                )
                break  # 成功したらループを抜ける
            except Exception as api_error:
                retry_count += 1
                if retry_count >= max_retries:
                    raise  # 最大リトライ回数に達したら例外を再スロー
                
                # エラーの種類に応じてバックオフ時間を調整
                if hasattr(api_error, 'status_code') and api_error.status_code == 429:
                    logging.warning(f"挨拶文生成時にAPI制限エラー（429）が発生しました。{backoff_time}秒後にリトライします。({retry_count}/{max_retries})")
                else:
                    logging.warning(f"挨拶文生成時にAPIエラーが発生しました: {str(api_error)}。{backoff_time}秒後にリトライします。({retry_count}/{max_retries})")
                
                time.sleep(backoff_time)
                backoff_time *= 2  # 指数バックオフ
        
        greeting_text = greeting_response.choices[0].message.content.strip()
        if greeting_text.endswith("。"):
            greeting_text = greeting_text[:-1]
        if not greeting_text.endswith("だよ！"):
            greeting_text += "だよ！"
        
        # 挨拶ツイート全体を作成（改行を入れる）
        greeting = f"C(＾▽＾ )つ みんなー！\n今日は論文「{paper_title}」について起承転結で解説します！\n\n{greeting_text}"
        
        # 140文字制限（タイトルが長い場合は短縮）
        if len(greeting) > 140:
            # タイトルの最大長を計算（全体の半分程度）
            max_title_length = 60
            if len(paper_title) > max_title_length:
                short_title = paper_title[:max_title_length-3] + "..."
                greeting = f"C(＾▽＾ )つ みんなー！\n今日は論文「{short_title}」について起承転結で解説します！\n\n{greeting_text}"
            
            # それでも長い場合は全体を切る
            if len(greeting) > 140:
                greeting = greeting[:137] + "..."
        
        # 結果を辞書にまとめる
        result = {
            "title": paper_title,
            "greeting": greeting,
            "ki": parts[0],
            "sho": parts[1],
            "ten": parts[2],
            "ketsu": parts[3]
        }
        
        # 結果をJSONファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logging.info(f"要約生成成功: {output_path}")
        return result
    
    except Exception as e:
        logging.error(f"要約生成エラー: {str(e)}")
        return None