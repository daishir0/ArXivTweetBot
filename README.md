# ArXivTweetBot

## Overview
ArXivTweetBot is an automated tool that searches for academic papers on arXiv based on specified keywords, downloads them, generates concise summaries using OpenAI's API, and posts these summaries on Twitter in a structured "Ki-Sho-Ten-Ketsu" (introduction, development, turn, conclusion) format. It's designed to make academic research more accessible to a wider audience.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/daishir0/ArXivTweetBot.git
cd ArXivTweetBot
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a configuration file:
```bash
cp config.sample.yaml config.yaml
```

4. Edit the configuration file with your API keys:
```bash
# OpenAI API key for generating summaries
# Get it from: https://platform.openai.com/
nano config.yaml  # Add your OpenAI API key

# Twitter API credentials for posting tweets
# Get them from: https://developer.twitter.com/
# Edit the same config.yaml file to add your Twitter credentials
```

5. Make the shell scripts executable:
```bash
chmod +x run_daily.sh run_test.sh
```

## Usage

### Basic Usage
Search for papers with specific keywords and process them (default: up to 4 papers):
```bash
python arxiv_downloader.py "LLM" "RAG"
```

### Test Mode
Process just one paper to test the system:
```bash
python arxiv_downloader.py "LLM" "RAG" --test-mode
# Or use the test script:
./run_test.sh
```

### Daily Automated Run
Set up a daily automated run using the provided script:
```bash
./run_daily.sh
```

### Cron Job Setup
To run the script automatically at scheduled times:
```bash
crontab -e
```

Add a line like this to run it daily at 9 AM:
```
0 9 * * * /path/to/ArXivTweetBot/run_daily.sh
```

#### Using with Anaconda
The scripts have been updated to work with Anaconda environments. They will automatically:
1. Detect the Anaconda installation
2. Activate the base environment
3. Use the Python from that environment

If you're using a different Anaconda installation path, edit the following line in both `run_daily.sh` and `run_test.sh`:
```bash
CONDA_PATH="/home/ec2-user/anaconda3"
```

For more detailed instructions on setting up cron with Anaconda, see the `cron_setup.md` file.

### Command Line Options
```bash
# Skip Twitter posting (only download and summarize)
python arxiv_downloader.py "LLM" "RAG" --skip-twitter

# Force reprocessing of already processed papers
python arxiv_downloader.py "LLM" "RAG" --force-process

# Change the maximum number of papers to process (default: 4)
python arxiv_downloader.py "LLM" "RAG" --max-process 10

# Change the maximum number of search results (default: 200)
python arxiv_downloader.py "LLM" "RAG" --max-results 50

# Use OR instead of AND for keywords
python arxiv_downloader.py "LLM" "RAG" --use-or
```

### Analyzing Twitter Logs
View statistics about your Twitter posts:
```bash
# Display summary in terminal
python twitter_log_analyzer.py

# Save summary to a file
python twitter_log_analyzer.py --output twitter_summary.md

# Export data to CSV
python twitter_log_analyzer.py --csv twitter_posts.csv
```

## Notes

1. **API Rate Limits**: Twitter has rate limits that restrict how many tweets you can post in a short period. The default setting processes a maximum of 4 papers per day to avoid hitting these limits.

2. **OpenAI API Costs**: Using the OpenAI API for generating summaries incurs costs. Monitor your usage to avoid unexpected charges.

3. **Paper Processing Time**: Processing large PDF files may take time, especially for papers with complex formulas or figures.

4. **Twitter API Access**: You need a Twitter Developer account with appropriate access levels to use the Twitter posting functionality.

5. **File Structure**:
   - `dl/`: Downloaded PDF files
   - `text/`: Extracted text from PDFs
   - `summary/`: Generated summaries in JSON format
   - `processed/`: Records of processed papers
   - `logs/`: Execution and Twitter posting logs

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# ArXivTweetBot

## 概要
ArXivTweetBotは、arXivから指定したキーワードで学術論文を検索し、ダウンロードして、OpenAI APIを使用して簡潔な要約を生成し、その要約を「起承転結」形式でTwitterに投稿する自動化ツールです。学術研究をより広い層にアクセスしやすくすることを目的としています。

## インストール方法

1. リポジトリをクローンします：
```bash
git clone https://github.com/daishir0/ArXivTweetBot.git
cd ArXivTweetBot
```

2. 必要な依存関係をインストールします：
```bash
pip install -r requirements.txt
```

3. 設定ファイルを作成します：
```bash
cp config.sample.yaml config.yaml
```

4. APIキーで設定ファイルを編集します：
```bash
# 要約生成用のOpenAI APIキー
# 取得先: https://platform.openai.com/
nano config.yaml  # OpenAI APIキーを追加

# ツイート投稿用のTwitter API認証情報
# 取得先: https://developer.twitter.com/
# 同じconfig.yamlファイルにTwitter認証情報を追加
```

5. シェルスクリプトに実行権限を付与します：
```bash
chmod +x run_daily.sh run_test.sh
```

## 使い方

### 基本的な使い方
特定のキーワードで論文を検索して処理します（デフォルト：最大4件）：
```bash
python arxiv_downloader.py "LLM" "RAG"
```

### テストモード
システムをテストするために1つの論文だけを処理します：
```bash
python arxiv_downloader.py "LLM" "RAG" --test-mode
# またはテストスクリプトを使用：
./run_test.sh
```

### 日次自動実行
提供されたスクリプトを使用して日次自動実行を設定します：
```bash
./run_daily.sh
```

### cronジョブの設定
スケジュールされた時間に自動的にスクリプトを実行するには：
```bash
crontab -e
```

毎日午前9時に実行するには、次のような行を追加します：
```
0 9 * * * /path/to/ArXivTweetBot/run_daily.sh
```

#### Anacondaとの併用
スクリプトはAnaconda環境で動作するように更新されました。自動的に以下の処理を行います：
1. Anacondaのインストールを検出
2. base環境を有効化
3. その環境のPythonを使用

異なるAnacondaインストールパスを使用している場合は、`run_daily.sh`と`run_test.sh`の両方で以下の行を編集してください：
```bash
CONDA_PATH="/home/ec2-user/anaconda3"
```

Anacondaを使用したcronの設定に関する詳細な手順は、`cron_setup.md`ファイルを参照してください。

### コマンドラインオプション
```bash
# Twitter投稿をスキップ（ダウンロードと要約のみ）
python arxiv_downloader.py "LLM" "RAG" --skip-twitter

# 既に処理済みの論文も再処理
python arxiv_downloader.py "LLM" "RAG" --force-process

# 処理する論文の最大数を変更（デフォルト：4）
python arxiv_downloader.py "LLM" "RAG" --max-process 10

# 検索結果の最大数を変更（デフォルト：200）
python arxiv_downloader.py "LLM" "RAG" --max-results 50

# キーワードをANDではなくORで結合
python arxiv_downloader.py "LLM" "RAG" --use-or
```

### Twitterログの分析
Twitter投稿に関する統計情報を表示します：
```bash
# ターミナルにサマリーを表示
python twitter_log_analyzer.py

# サマリーをファイルに保存
python twitter_log_analyzer.py --output twitter_summary.md

# データをCSVにエクスポート
python twitter_log_analyzer.py --csv twitter_posts.csv
```

## 注意点

1. **APIレート制限**：Twitterには短時間に投稿できるツイート数を制限するレート制限があります。これらの制限に達しないように、デフォルト設定では1日に最大4件の論文を処理します。

2. **OpenAI APIのコスト**：要約生成にOpenAI APIを使用するとコストが発生します。予期しない料金を避けるために使用状況を監視してください。

3. **論文処理時間**：大きなPDFファイルの処理には時間がかかる場合があります。特に複雑な数式や図表を含む論文の場合はさらに時間がかかります。

4. **Twitter APIアクセス**：Twitter投稿機能を使用するには、適切なアクセスレベルを持つTwitter開発者アカウントが必要です。

5. **ファイル構造**：
   - `dl/`：ダウンロードしたPDFファイル
   - `text/`：PDFから抽出したテキスト
   - `summary/`：JSON形式で生成された要約
   - `processed/`：処理済み論文の記録
   - `logs/`：実行とTwitter投稿のログ

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。
