# ChatApp

WSL (Debian) 上に構築したリアルタイムチャットアプリ。学習・検証目的のプロジェクトです。

## 構成

- バックエンド: Python + FastAPI + WebSocket (`backend/`)
- フロントエンド: React + TypeScript + Vite (`frontend/`)
- DB: PostgreSQL 17 (WSL内にインストール)

## 機能

- WebSocketによるリアルタイムメッセージ配信、PostgreSQLへの永続化
- **トリップ機能**: `名前#合言葉` の形式で入力すると、`名前◆XXXXXXXXXX` の形でトリップ(なりすまし対策の署名)が付く。合言葉はサーバー側の秘密鍵(pepper)付きHMAC-SHA256でハッシュ化されるのみで、平文はDBに保存されない
- トリップ登録者限定のアイコン画像アップロード(Pillowで検証・リサイズ・再エンコード)

## セキュリティに関する経緯

このプロジェクトを作る過程で、トリップ機能に対して実際に3段階の脆弱性が見つかり、その都度直しています。「一度直して終わり」ではなく、直したら別の穴が見つかる、というのを正直に記録しています。

1. **なりすましの見た目コピー**: トリップは `名前◆トリップ文字列` という見た目で表示していたが、名前欄に直接 `◆` を含む文字列を入力すれば、合言葉なしで本物と全く同じ表示を偽造できた → 名前から `◆` を除去する対応をいったん実施
2. **類似文字での回避**: 実際に使っていたユーザーが、`◆` (U+25C6) ではなく見た目が酷似した別のUnicode文字 `⬥` (U+2B25) を使って同じ穴を再現した → 文字のブラックリストはいたちごっこと判断し、**名前とトリップをDBスキーマ・API・画面表示のすべてで別フィールドに分離**。トリップは常にサーバー計算値のみが専用のバッジ要素に入るため、名前欄にどんな文字列を入れても構造上バッジには混入できなくなった
3. **公開前レビューで発覚した2件**(GitHubに上げる前の見直しで発見):
   - CORS設定が `*.trycloudflare.com` 全体を許可していた(自分のトンネルだけでなく、他人の無関係なトンネル上のページからもAPIを叩けてしまう設定ミス)→ 許可オリジンを明示的なリストに限定、かつ未使用だった `allow_credentials` を無効化
   - アバター画像アップロードに「画像爆弾」対策がなかった(数MBの画像が数億ピクセルに展開され、メモリ・CPUを消費させられる可能性)→ デコード前に解像度をチェックして即座に拒否するよう修正

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

http://localhost:8000 で起動。`GET /messages` で過去メッセージ一覧、`POST /avatar` でアイコンアップロード、`WS /ws` でリアルタイム接続。

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
│   │   ├── main.py                # FastAPIエントリーポイント / WebSocketエンドポイント
│   │   ├── config.py              # 環境変数設定 (.envを読み込み)
│   │   ├── database.py            # SQLAlchemy接続設定
│   │   ├── models.py              # DBモデル (Message)
│   │   ├── schemas.py             # Pydanticスキーマ
│   │   ├── connection_manager.py  # WebSocket接続管理
│   │   ├── tripcode.py            # トリップ(HMAC-SHA256)計算
│   │   └── avatars.py             # アバター画像の検証・保存
│   ├── .env                       # DATABASE_URL, TRIP_SECRET (gitignore対象)
│   ├── requirements.txt
│   └── venv/
└── frontend/
    └── src/
        ├── App.tsx                 # チャットUI (参加画面 + メッセージ画面)
        └── App.css
```

## 今後の拡張候補

- ユーザー認証 (JWT等)
- Alembicによるマイグレーション管理
- 複数ルーム/チャンネル対応
- メッセージの既読管理
- 画像アップロードのレート制限

## 補足

- `backend/.env` には `DATABASE_URL` と `TRIP_SECRET` が平文で入っています。リポジトリには絶対にコミットしないこと (`.gitignore` 済み)。
- 開発中に外部公開する場合はCloudflare Tunnelなどを使う想定。その際は `backend/.env` の `CORS_EXTRA_ORIGIN` に自分のトンネルURLだけを明示的に設定すること(ワイルドカードで `trycloudflare.com` 全体を許可しないこと)。
