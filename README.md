# 医療・介護向けバイタル管理システム (Cloud Deployed Version)

## 📌 概要
医療・介護現場での「誤入力防止」と「情報の適切な分離」を目的としたWebアプリケーションです。
ローカル開発だけでなく、AWS EC2（Ubuntu）上にDockerを用いて本番環境を構築し、インターネット公開まで完了しています。

## 🌐 公開URL
- **URL:** `http://98.94.68.223/`
- ※現在はテスト運用中のため、上記アドレスから直接アクセス可能です。

## 🛠 使用技術
- **Infrastructure:** AWS (EC2 / Ubuntu), Docker, Docker Compose
- **Web Server:** Nginx (Reverse Proxy)
- **Backend:** Python 3.9, Flask
- **Database:** MySQL 8.0
- **Frontend:** HTML5, CSS3, Jinja2

## 🚀 構築・デプロイ手順

### 1. AWS環境のセットアップ
- EC2インスタンス（Ubuntu）の起動
- セキュリティグループの設定（SSH: 22番, HTTP: 80番の開放）

### 2. サーバー内での環境構築
```bash
# ツールのインストール
sudo apt update && sudo apt install -y git docker.io docker-compose

# リポジトリのクローン
git clone https://github.com/kaneko668/docker_kadai
cd docker_kadai

# 環境変数の設定
nano .env  # データベース接続情報を記述
---
MYSQL_ROOT_PASSWORD=root_pass
MYSQL_DATABASE=medical_db
MYSQL_USER=medical_user
MYSQL_PASSWORD=medical_pass
---

### cd proxy
### nano Dockerfile
---
##### FROM nginx:latest
##### COPY default.conf /etc/nginx/conf.d/default.conf
---

cd ../
sudo docker-compose up -d --build

使い方
１：介護士アカウント、医者アカウントを作る

２：介護士アカウントでは患者の状態を項目ごとに入力し送信する。

３：医者アカウントは介護士アカウントから送信された、データが一覧表示で閲覧可能。

工夫した点
将来医療系の仕事をするので合わせた


苦労点
エラー処理