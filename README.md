# ChatApp

WSL (Debian) 上に構築したリアルタイムチャットアプリの雛形。

## 構成

- バックエンド: Python + FastAPI + WebSocket (`backend/`)
- フロントエンド: React + TypeScript + Vite (`frontend/`)
- DB: PostgreSQL 17 (WSL内にインストール)

## 前提 (セットアップ済み)

- WSL Debianディストリビューション
- Python 3.13 (`python3-venv`)
- Node.js LTS (nvm経由, v24)
- PostgreSQL 17 (ロール `chatapp_user` / DB `chatapp_db` 作成済み)

## 起動方法

WSLターミナル (`wsl -d Debian`) で以下を実行。

### 1. PostgreSQLを起動

```bash
sudo service postgresql start
```

### 2. バックエンド

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

http://localhost:8000 で起動。`/messages` で過去メッセージ一覧、`/ws/{username}` でWebSocket接続。

### 3. フロントエンド

別のWSLターミナルで:

```bash
cd frontend
npm run dev
```

http://localhost:5173 で起動。

## ディレクトリ構成

```
ChatApp/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPIエントリーポイント / WebSocketエンドポイント
│   │   ├── config.py          # 環境変数設定 (.envを読み込み)
│   │   ├── database.py        # SQLAlchemy接続設定
│   │   ├── models.py          # DBモデル (Message)
│   │   ├── schemas.py         # Pydanticスキーマ
│   │   └── connection_manager.py  # WebSocket接続管理
│   ├── .env                   # DATABASE_URL (gitignore対象)
│   ├── requirements.txt
│   └── venv/
└── frontend/
    └── src/
        ├── App.tsx             # チャットUI (参加画面 + メッセージ画面)
        └── App.css
```

## 今後の拡張候補

- ユーザー認証 (JWT等)
- Alembicによるマイグレーション管理
- 複数ルーム/チャンネル対応
- メッセージの既読管理

## 補足

- `backend/.env` の `DATABASE_URL` にはDBパスワードが平文で入っています。リポジトリには絶対にコミットしないこと (`.gitignore` 済み)。
- セットアップ中に一時的なNOPASSWD sudo設定 (`/etc/sudoers.d/temp-nopasswd`) を作成した場合は、作業完了後に `sudo rm /etc/sudoers.d/temp-nopasswd` で削除することを推奨。
