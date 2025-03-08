# cronでAnaconda環境を使用するための設定方法

## 1. スクリプトの修正（完了済み）

`run_daily.sh`と`run_test.sh`スクリプトを修正して、Anaconda環境を有効化するようにしました。主な変更点：

- Anacondaのパスを設定
- conda.shを使用して環境を有効化
- Pythonコマンドを変数化して、Anaconda環境のPythonを使用

## 2. Anacondaのパスを確認

スクリプト内のAnacondaパスが正しいことを確認してください。現在は以下のように設定されています：

```bash
CONDA_PATH="/home/ec2-user/anaconda3"
```

実際のAnacondaのインストールパスが異なる場合は、このパスを修正してください。

```bash
# Anacondaのパスを確認するコマンド
which conda
```

## 3. スクリプトに実行権限を付与

```bash
chmod +x /home/ec2-user/arxiv-downloader/run_daily.sh
chmod +x /home/ec2-user/arxiv-downloader/run_test.sh
```

## 4. cronの設定

cronを編集して、毎日13:55に実行するように設定します：

```bash
crontab -e
```

以下の行を追加します：

```
55 13 * * * /home/ec2-user/arxiv-downloader/run_daily.sh
```

## 5. 絶対パスの使用

cronでは相対パスが機能しないことがあるため、スクリプト内で使用するパスは絶対パスに変更することをお勧めします。

例えば、以下のように変更します：

```bash
# 相対パス
LOG_DIR="./logs"

# 絶対パス
LOG_DIR="/home/ec2-user/arxiv-downloader/logs"
```

## 6. テスト実行

設定が正しいか確認するために、手動でスクリプトを実行してテストします：

```bash
/home/ec2-user/arxiv-downloader/run_test.sh
```

ログファイルを確認して、Anaconda環境が正しく有効化されているか、Pythonのバージョンが正しいかを確認します：

```bash
cat /home/ec2-user/arxiv-downloader/logs/test_execution_*.log
```

## 7. cronのログを確認

cronジョブが実行された後、ログファイルを確認して正常に実行されたかどうかを確認します：

```bash
cat /home/ec2-user/arxiv-downloader/logs/execution_*.log
```

## 8. トラブルシューティング

### 8.1. cronの環境変数

cronは通常のシェル環境と異なる環境で実行されるため、必要な環境変数がない場合があります。スクリプト内で必要な環境変数を設定することをお勧めします。

### 8.2. パスの問題

cronはPATH環境変数が限られているため、コマンドは絶対パスで指定することをお勧めします。

### 8.3. ログの確認

cronジョブのエラーを確認するには、システムログを確認します：

```bash
sudo grep CRON /var/log/syslog
```

または

```bash
sudo journalctl | grep CRON
```

## 9. 注意点

- cronは非対話的環境で実行されるため、対話的なコマンドは機能しません。
- cronジョブは、ユーザーのホームディレクトリではなく、/などから実行されることがあります。
- cronジョブは、ユーザーのシェル設定ファイル（.bashrc、.bash_profileなど）を読み込みません。