FROM python:3.9-slim

WORKDIR /app
RUN pip install flask mysql-connector-python

# srcフォルダの中身（Pythonのコードやtemplates）を丸ごとコンテナにコピー
COPY src/ ./src/

# Flaskを起動するコマンド（例）
CMD ["python", "src/app.py"]