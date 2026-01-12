# User Management Service

CRUD 操作とテナント分離を備えたユーザー管理サービス

## 🎯 概要

このサービスは、マルチテナント環境でのユーザー管理機能を提供します。Azure CosmosDB をデータストアとして使用し、RESTful API を通じてユーザーの CRUD 操作、検索、ページネーション、監査ログ機能を提供します。

## 🔧 技術スタック

- **Python**: 3.11+
- **Framework**: FastAPI
- **Database**: Azure CosmosDB
- **Cache**: Redis
- **Authentication**: JWT (JSON Web Token)
- **Password Hashing**: bcrypt
- **API Documentation**: OpenAPI (Swagger)
- **Default Port**: 3002

## 📋 機能

- ✅ ユーザー CRUD 操作
- ✅ テナントベースのユーザーフィルタリング
- ✅ ユーザープロファイル管理
- ✅ ユーザー検索とページネーション（高度フィルタリング対応）
- ✅ 監査ログ機能
- ✅ JWT 認証
- ✅ 入力検証とサニタイゼーション
- ✅ OpenAPI ドキュメント
- ✅ メールドメイン検証（内部ユーザー用）
- ✅ パスワードハッシング（bcrypt）
- ✅ テナント・ユーザー関係管理（複数テナント紐付け）
- ✅ Redis キャッシング（テナントユーザー一覧）
- ✅ バルクユーザー作成（最大100件）
- ✅ ロールベースアクセス制御

## 🚀 セットアップ

### 前提条件

- Python 3.11 以上
- Azure CosmosDB アカウント
- JWT 認証サービス（ws-demo-poly3）

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
PORT=3002
ENVIRONMENT=development

# CosmosDB Configuration
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-db-key
COSMOS_DATABASE_NAME=UserManagement
COSMOS_CONTAINER_NAME=Users
COSMOS_AUDIT_CONTAINER_NAME=AuditLogs

# Redis Configuration (for caching)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 3002
```

````

### 本番モード

```bash
cd src && uvicorn app.main:app --host 0.0.0.0 --port 8000
````

または

```bash
PYTHONPATH=src uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 API ドキュメント

サービスを起動した後、以下の URL で API ドキュメントにアクセスできます:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🔑 認証

すべての API エンドポイント（ヘルスチェックとドキュメントを除く）は、以下のヘッダーが必要です:

```
Authorization: Bearer <JWT_TOKEN>
X-Tenant-ID: <TENANT_ID>
```

## 📝 API エンドポイント

### ヘルスチェック

- `GET /health` - サービスの稼働状況を確認

### ユーザー管理

- `POST /api/v1/users` - 新しいユーザーを作成（メールドメイン検証対応）
- `GET /api/v1/users/{user_id}` - ユーザー詳細を取得
- `PUT /api/v1/users/{user_id}` - ユーザー情報を更新
- `DELETE /api/v1/users/{user_id}` - ユーザーを削除（ソフトデリート）
- `GET /api/v1/users` - ユーザーを検索（高度フィルタリング、ページネーション対応）
- `POST /api/v1/users/bulk` - ユーザー一括作成（最大100件）
- `GET /api/v1/users/{user_id}/tenants` - ユーザーの所属テナント一覧を取得（Redis キャッシュ付き）

### テナント管理

- `POST /api/tenants` - 新しいテナントを作成
- `GET /api/tenants` - テナント一覧を取得
- `GET /api/tenants/{tenant_id}` - テナント詳細を取得
- `PUT /api/tenants/{tenant_id}` - テナント情報を更新
- `DELETE /api/tenants/{tenant_id}` - テナントを削除
- `POST /api/tenants/{tenant_id}/admins` - テナント管理者を割り当て

### テナントユーザー管理

- `POST /api/tenants/{tenant_id}/users` - テナントにユーザーを追加
- `GET /api/tenants/{tenant_id}/users` - テナント内のユーザー一覧を取得（Redis キャッシュ付き）
- `DELETE /api/tenants/{tenant_id}/users/{user_id}` - テナントからユーザーを削除

### リクエスト例

#### ユーザー作成（パスワード付き）

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
    "password": "securePassword123",
    "user_type": "external",
    "roles": ["user"],
    "permissions": ["users.read"],
    "profile": {
      "phone_number": "+81-90-1234-5678",
      "department": "Engineering",
      "job_title": "Software Engineer"
    },
    "status": "ACTIVE"
  }'
```

#### ユーザー検索（高度フィルタリング）

```bash
curl -X GET "http://localhost:8000/api/v1/users?search_term=john&user_type=external&status=ACTIVE&page_number=1&page_size=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: tenant-123"
```

#### バルクユーザー作成

```bash
curl -X POST http://localhost:8000/api/v1/users/bulk \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {
        "tenant_id": "tenant-123",
        "email": "user1@example.com",
        "username": "user1",
        "first_name": "User",
        "last_name": "One"
      },
      {
        "tenant_id": "tenant-123",
        "email": "user2@example.com",
        "username": "user2",
        "first_name": "User",
        "last_name": "Two"
      }
    ]
  }'
```

#### テナントにユーザーを追加

```bash
curl -X POST http://localhost:8000/api/tenants/tenant-123/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-456",
    "roles": ["user", "viewer"],
    "permissions": ["users.read", "services.read"]
  }'
```

#### ユーザーの所属テナント一覧を取得

```bash
curl -X GET http://localhost:8000/api/v1/users/user-456/tenants \
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

- すべての API エンドポイントで JWT 認証が必要
- テナント ID の検証により、マルチテナント分離を実現
- 入力検証とサニタイゼーションを実装
- 監査ログによるすべての操作の追跡
- bcrypt によるパスワードハッシング
- 内部ユーザー作成時のメールドメイン検証
- ロールベースアクセス制御（RBAC）
- Redis キャッシュによるパフォーマンス向上

## 📦 依存関係

このサービスは以下に依存しています:

- **Takas0522/ws-demo-poly3#1** - JWT 認証サービス
- **Takas0522/ws-demo-poly-integration#6** - 共有型ライブラリ
- **Takas0522/ws-demo-poly-integration#4** - CosmosDB スキーマ

## 📄 ライセンス

MIT License

## 👥 貢献

プルリクエストを歓迎します。大きな変更の場合は、まず issue を開いて変更内容を議論してください。
