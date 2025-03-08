#!/bin/bash

# テスト実行スクリプト
# テストモードで1件だけ処理する

# Anaconda環境の設定
# Anacondaのパスを設定（必要に応じて変更）
CONDA_PATH="/home/ec2-user/anaconda3"
CONDA_PROFILE="$CONDA_PATH/etc/profile.d/conda.sh"

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 日付を取得
DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M:%S")

# スクリプトの絶対パスを取得
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ログディレクトリ（絶対パス）
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 実行ログファイル
EXEC_LOG="$LOG_DIR/test_execution_$DATE.log"

# 開始メッセージ
echo "===== ArXivTweetBot テスト実行 =====" >> "$EXEC_LOG"
echo "日時: $DATE $TIME" >> "$EXEC_LOG"
echo "" >> "$EXEC_LOG"

# Anaconda環境を有効化
echo "Anaconda環境を有効化中..." >> "$EXEC_LOG"
if [ -f "$CONDA_PROFILE" ]; then
    # conda.shが存在する場合はそれを使用
    source "$CONDA_PROFILE"
    conda activate base >> "$EXEC_LOG" 2>&1
    PYTHON_CMD="python"
    echo "Anaconda環境を有効化しました。" >> "$EXEC_LOG"
else
    # conda.shが見つからない場合は直接パスを指定
    PYTHON_CMD="$CONDA_PATH/bin/python"
    echo "conda.shが見つかりません。直接Pythonパスを使用します: $PYTHON_CMD" >> "$EXEC_LOG"
fi

# Pythonバージョンを確認
echo "Pythonバージョン:" >> "$EXEC_LOG"
$PYTHON_CMD --version >> "$EXEC_LOG" 2>&1
echo "" >> "$EXEC_LOG"

# LLMとRAGのキーワードで検索して処理（テストモードで1件のみ）
echo "LLMとRAGのキーワードで検索を実行中（テストモード）..." >> "$EXEC_LOG"
$PYTHON_CMD "$SCRIPT_DIR/arxiv_downloader.py" "LLM" "RAG" --test-mode >> "$EXEC_LOG" 2>&1

# 実行結果のサマリーを生成
echo "" >> "$EXEC_LOG"
echo "Twitter投稿ログの分析中..." >> "$EXEC_LOG"
$PYTHON_CMD "$SCRIPT_DIR/twitter_log_analyzer.py" --output "$LOG_DIR/twitter_summary_test_$DATE.md" --csv "$LOG_DIR/twitter_posts_test_$DATE.csv" >> "$EXEC_LOG" 2>&1

# 完了メッセージ
echo "" >> "$EXEC_LOG"
echo "テスト処理が完了しました。" >> "$EXEC_LOG"
echo "サマリー: $LOG_DIR/twitter_summary_test_$DATE.md" >> "$EXEC_LOG"
echo "CSVデータ: $LOG_DIR/twitter_posts_test_$DATE.csv" >> "$EXEC_LOG"
echo "===== 終了 =====" >> "$EXEC_LOG"

echo "テスト実行が完了しました。ログは $EXEC_LOG を確認してください。"