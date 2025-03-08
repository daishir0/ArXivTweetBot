#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import PyPDF2
import logging

def extract_text_from_pdf(pdf_path, output_dir):
    """
    PDFからテキストを抽出し、テキストファイルに保存する
    
    Args:
        pdf_path (str): PDFファイルのパス
        output_dir (str): 出力先ディレクトリ
    
    Returns:
        str: 抽出したテキストを保存したファイルのパス
    """
    # ファイル名を取得（拡張子なし）
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    # 出力ファイルパス
    output_path = os.path.join(output_dir, f"{filename_without_ext}.txt")
    
    try:
        # PDFファイルを開く
        with open(pdf_path, 'rb') as file:
            # PDFReaderオブジェクトを作成
            reader = PyPDF2.PdfReader(file)
            
            # テキストを抽出
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            # テキストファイルに保存
            with open(output_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text)
            
            logging.info(f"テキスト抽出成功: {pdf_path} -> {output_path}")
            return output_path
    
    except Exception as e:
        logging.error(f"テキスト抽出エラー: {pdf_path} - {str(e)}")
        return None