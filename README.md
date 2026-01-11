# User Management Service

CRUD操作とテナント分離を備えたユーザー管理サービス

## 🎯 概要

このサービスは、マルチテナント環境でのユーザー管理機能を提供します。Azure CosmosDBをデータストアとして使用し、RESTful APIを通じてユーザーのCRUD操作、検索、ページネーション、監査ログ機能を提供します。

## 🔧 技術スタック

- **Python**: 3.11+
- **Framework**: FastAPI
- **Database**: Azure CosmosDB
- **Authentication**: JWT (JSON Web Token)
- **API Documentation**: OpenAPI (Swagger)

## 📋 機能

- ✅ ユーザーCRUD操作
- ✅ テナントベースのユーザーフィルタリング
- ✅ ユーザープロファイル管理
- ✅ ユーザー検索とページネーション
- ✅ 監査ログ機能
- ✅ JWT認証
- ✅ 入力検証とサニタイゼーション
- ✅ OpenAPIドキュメント

## 🚀 セットアップ

### 前提条件

- Python 3.11以上
- Azure CosmosDBアカウント
- JWT認証サービス（ws-demo-poly3）

### インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/Takas0522/ws-demo-poly2.git
cd ws-demo-poly2/src/user-management-service
```

2. 仮想環境を作成して有効化:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

4. 環境変数を設定:
```bash
cp .env.example .env
# .envファイルを編集して適切な値を設定
```

### 環境変数

`.env`ファイルで以下の環境変数を設定してください:

```
# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# CosmosDB Configuration
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-db-key
COSMOS_DATABASE_NAME=UserManagement
COSMOS_CONTAINER_NAME=Users
COSMOS_AUDIT_CONTAINER_NAME=AuditLogs

# JWT Configuration
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ISSUER=auth-service

# Logging
LOG_LEVEL=INFO
```

## 🏃 実行

### 開発モード

```bash
cd src && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

または

```bash
PYTHONPATH=src uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 本番モード

```bash
cd src && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

または

```bash
PYTHONPATH=src uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 APIドキュメント

サービスを起動した後、以下のURLでAPIドキュメントにアクセスできます:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🔑 認証

すべてのAPIエンドポイント（ヘルスチェックとドキュメントを除く）は、以下のヘッダーが必要です:

```
Authorization: Bearer <JWT_TOKEN>
X-Tenant-ID: <TENANT_ID>
```

## 📝 APIエンドポイント

### ヘルスチェック

- `GET /health` - サービスの稼働状況を確認

### ユーザー管理

- `POST /api/v1/users` - 新しいユーザーを作成
- `GET /api/v1/users/{user_id}` - ユーザー詳細を取得
- `PUT /api/v1/users/{user_id}` - ユーザー情報を更新
- `DELETE /api/v1/users/{user_id}` - ユーザーを削除（ソフトデリート）
- `GET /api/v1/users` - ユーザーを検索（ページネーション対応）

### リクエスト例

#### ユーザー作成

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-123",
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
      "phone_number": "+81-90-1234-5678",
      "department": "Engineering",
      "job_title": "Software Engineer"
    },
    "status": "ACTIVE"
  }'
```

#### ユーザー検索

```bash
curl -X GET "http://localhost:8000/api/v1/users?search_term=john&page_number=1&page_size=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: tenant-123"
```

## 🧪 テスト

### ユニットテストの実行

```bash
pytest tests/
```

### カバレッジレポート

```bash
pytest --cov=app --cov-report=html tests/
```

## 🔒 セキュリティ

- すべてのAPIエンドポイントでJWT認証が必要
- テナントIDの検証により、マルチテナント分離を実現
- 入力検証とサニタイゼーションを実装
- 監査ログによるすべての操作の追跡

## 📦 依存関係

このサービスは以下に依存しています:

- **Takas0522/ws-demo-poly3#1** - JWT認証サービス
- **Takas0522/ws-demo-poly-integration#6** - 共有型ライブラリ
- **Takas0522/ws-demo-poly-integration#4** - CosmosDBスキーマ

## 📄 ライセンス

MIT License

## 👥 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。
