# Tenant Management Service

マルチテナント管理アプリケーションのテナント管理サービスです。テナントのCRUD操作、特権テナント保護、テナント分離機能を提供します。

## 機能

### Phase 1実装済み機能
- ✅ テナントCRUD操作（作成・取得・更新・削除）
- ✅ 特権テナント保護機能
- ✅ テナント一覧取得（ページネーション）
- ✅ テナント名の一意性チェック
- ✅ JWT認証
- ✅ テナント分離
- ✅ 監査ログ（作成者・更新者の追跡）
- ✅ テナント所属ユーザー管理（タスク06）
  - ユーザー招待（認証サービス連携）
  - ユーザー一覧取得（ユーザー詳細並列取得）
  - ユーザー削除
  - user_count自動更新
- ✅ ドメイン管理（タスク06）
  - 独自ドメイン追加
  - DNS TXTレコード検証
  - ドメイン一覧取得
  - ドメイン削除

### Phase 2で実装予定
- ⏭ ロールベース認可（閲覧者、管理者、全体管理者）
- ⏭ テナントの論理削除と物理削除の分離
- ⏭ 関連データのカスケード削除
- ⏭ ドメインベースのメールアドレス制限

## アーキテクチャ

```
app/
├── main.py              # FastAPIアプリケーション
├── config.py            # 設定
├── dependencies.py      # 依存注入
├── models/              # データモデル
│   └── tenant.py
├── repositories/        # データアクセス層
│   └── tenant_repository.py
├── services/            # ビジネスロジック層
│   └── tenant_service.py
├── api/                 # APIエンドポイント
│   └── tenants.py
├── schemas/             # リクエスト/レスポンススキーマ
│   └── tenant.py
└── utils/               # ユーティリティ
    └── jwt.py           # JWT検証
```

## 技術スタック

- **フレームワーク**: FastAPI 0.109.2
- **言語**: Python 3.11+
- **データベース**: Azure Cosmos DB
- **認証**: JWT
- **バリデーション**: Pydantic v2

## セットアップ

### 環境変数

`.env.example`を参考に`.env`ファイルを作成：

```bash
# アプリケーション設定
SERVICE_NAME=tenant-management-service
ENVIRONMENT=development
LOG_LEVEL=INFO
API_VERSION=v1

# Cosmos DB設定
COSMOS_DB_CONNECTION_STRING=<your-cosmos-db-connection-string>
COSMOS_DB_DATABASE_NAME=management-app
COSMOS_DB_CONTAINER_NAME=tenant

# JWT設定
JWT_SECRET_KEY=<your-jwt-secret-key-64-bytes-or-longer>
JWT_ALGORITHM=HS256

# 特権テナントID
PRIVILEGED_TENANT_IDS=tenant_privileged

# Application Insights
APPINSIGHTS_INSTRUMENTATIONKEY=<your-app-insights-key>

# CORS設定
ALLOWED_ORIGINS=http://localhost:3000
```

### インストール

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# または開発環境用
pip install -r requirements-dev.txt
```

### 起動

```bash
# 開発サーバー起動（自動リロード有効）
python -m app.main

# または uvicorn コマンド
uvicorn app.main:app --reload --port 8001
```

## API仕様

### ベースURL
```
http://localhost:8001/api/v1
```

### エンドポイント

#### 1. GET /tenants - テナント一覧取得

**リクエスト**:
```bash
curl -X GET "http://localhost:8001/api/v1/tenants?status=active&skip=0&limit=20" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (200 OK):
```json
{
  "data": [
    {
      "id": "tenant_acme",
      "name": "acme",
      "displayName": "Acme Corporation",
      "isPrivileged": false,
      "status": "active",
      "plan": "standard",
      "userCount": 25,
      "maxUsers": 100,
      "createdAt": "2026-01-01T00:00:00Z",
      "updatedAt": "2026-01-20T15:00:00Z"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 15
  }
}
```

#### 2. GET /tenants/{tenant_id} - テナント詳細取得

**リクエスト**:
```bash
curl -X GET "http://localhost:8001/api/v1/tenants/tenant_acme" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (200 OK):
```json
{
  "id": "tenant_acme",
  "name": "acme",
  "displayName": "Acme Corporation",
  "isPrivileged": false,
  "status": "active",
  "plan": "standard",
  "userCount": 25,
  "maxUsers": 100,
  "metadata": {
    "industry": "Manufacturing",
    "country": "US"
  },
  "createdAt": "2026-01-01T00:00:00Z",
  "updatedAt": "2026-01-20T15:00:00Z",
  "createdBy": "user_admin_001",
  "updatedBy": "user_admin_001"
}
```

#### 3. POST /tenants - テナント新規作成

**リクエスト**:
```bash
curl -X POST "http://localhost:8001/api/v1/tenants" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example-corp",
    "displayName": "Example Corporation",
    "plan": "standard",
    "maxUsers": 50,
    "metadata": {
      "industry": "IT",
      "country": "JP"
    }
  }'
```

**レスポンス** (201 Created):
```json
{
  "id": "tenant_example-corp",
  "name": "example-corp",
  "displayName": "Example Corporation",
  "isPrivileged": false,
  "status": "active",
  "plan": "standard",
  "userCount": 0,
  "maxUsers": 50,
  "metadata": {
    "industry": "IT",
    "country": "JP"
  },
  "createdAt": "2026-02-01T10:00:00Z",
  "updatedAt": "2026-02-01T10:00:00Z",
  "createdBy": "user_admin_001"
}
```

#### 4. PUT /tenants/{tenant_id} - テナント更新

**リクエスト**:
```bash
curl -X PUT "http://localhost:8001/api/v1/tenants/tenant_example-corp" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "Example Corp (Updated)",
    "maxUsers": 100
  }'
```

**レスポンス** (200 OK):
更新後のテナント情報

#### 5. DELETE /tenants/{tenant_id} - テナント削除

**リクエスト**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/tenants/tenant_example-corp" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (204 No Content)

#### 6. POST /tenants/{tenant_id}/users - ユーザー招待

**リクエスト**:
```bash
curl -X POST "http://localhost:8001/api/v1/tenants/tenant_acme/users" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user_550e8400-e29b-41d4-a716-446655440000"
  }'
```

**レスポンス** (201 Created):
```json
{
  "id": "tenant_user_tenant_acme_user_550e8400",
  "tenantId": "tenant_acme",
  "userId": "user_550e8400-e29b-41d4-a716-446655440000",
  "userDetails": {
    "username": "john.doe",
    "displayName": "John Doe",
    "email": "john@example.com"
  },
  "assignedAt": "2026-02-01T10:00:00Z",
  "assignedBy": "system"
}
```

#### 7. GET /tenants/{tenant_id}/users - テナント所属ユーザー一覧

**リクエスト**:
```bash
curl -X GET "http://localhost:8001/api/v1/tenants/tenant_acme/users?skip=0&limit=20&include_total=true" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (200 OK):
```json
{
  "data": [
    {
      "id": "tenant_user_tenant_acme_user_550e8400",
      "tenantId": "tenant_acme",
      "userId": "user_550e8400-e29b-41d4-a716-446655440000",
      "userDetails": {
        "username": "john.doe",
        "email": "john@example.com"
      },
      "assignedAt": "2026-01-15T10:00:00Z",
      "assignedBy": "system"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 5
  }
}
```

#### 8. DELETE /tenants/{tenant_id}/users/{user_id} - ユーザー削除

**リクエスト**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/tenants/tenant_acme/users/user_550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (204 No Content)

#### 9. POST /tenants/{tenant_id}/domains - ドメイン追加

**リクエスト**:
```bash
curl -X POST "http://localhost:8001/api/v1/tenants/tenant_acme/domains" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com"
  }'
```

**レスポンス** (201 Created):
```json
{
  "id": "domain_tenant_acme_example_com",
  "tenantId": "tenant_acme",
  "domain": "example.com",
  "verified": false,
  "verificationToken": "txt-verification-a1b2c3d4e5f6...",
  "verificationInstructions": {
    "step1": "DNSプロバイダーにログイン",
    "step2": "以下のTXTレコードを追加:",
    "recordName": "_tenant_verification.example.com",
    "recordType": "TXT",
    "recordValue": "txt-verification-a1b2c3d4e5f6..."
  },
  "createdAt": "2026-02-01T11:00:00Z",
  "createdBy": "system"
}
```

#### 10. POST /tenants/{tenant_id}/domains/{domain_id}/verify - ドメイン検証

**リクエスト**:
```bash
curl -X POST "http://localhost:8001/api/v1/tenants/tenant_acme/domains/domain_tenant_acme_example_com/verify" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (200 OK):
```json
{
  "id": "domain_tenant_acme_example_com",
  "domain": "example.com",
  "verified": true,
  "verifiedAt": "2026-02-01T11:30:00Z",
  "verifiedBy": "system"
}
```

#### 11. GET /tenants/{tenant_id}/domains - ドメイン一覧取得

**リクエスト**:
```bash
curl -X GET "http://localhost:8001/api/v1/tenants/tenant_acme/domains?verified=true" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (200 OK):
```json
{
  "data": [
    {
      "id": "domain_tenant_acme_example_com",
      "tenantId": "tenant_acme",
      "domain": "example.com",
      "verified": true,
      "verifiedAt": "2026-02-01T11:30:00Z",
      "createdAt": "2026-02-01T11:00:00Z"
    }
  ]
}
```

#### 12. DELETE /tenants/{tenant_id}/domains/{domain_id} - ドメイン削除

**リクエスト**:
```bash
curl -X DELETE "http://localhost:8001/api/v1/tenants/tenant_acme/domains/domain_tenant_acme_example_com" \
  -H "Authorization: Bearer <token>"
```

**レスポンス** (204 No Content)

### エラーコード

| コード | HTTPステータス | 説明 |
|--------|--------------|------|
| 401 | Unauthorized | JWT認証失敗 |
| 403 | Forbidden | 特権テナントへのアクセス、テナント分離違反 |
| 404 | Not Found | テナント、ユーザー、ドメインが存在しない |
| 409 | Conflict | テナント名の重複、ユーザーの重複招待 |
| 422 | Unprocessable Entity | バリデーションエラー、ドメイン検証失敗 |
| 400 | Bad Request | 最大ユーザー数超過、不正なパラメータ |
| 503 | Service Unavailable | 認証サービス不可 |

## ビジネスロジック

### 特権テナント保護

特権テナント（`is_privileged=true`）は以下の操作が禁止されます：
- 更新（PUT /tenants/{tenant_id}）
- 削除（DELETE /tenants/{tenant_id}）

```python
if tenant.is_privileged:
    raise ValueError("Privileged tenant cannot be modified")
```

### テナント分離

特権テナント以外のユーザーは、自分のテナントのデータのみにアクセスできます：

```python
privileged = is_privileged_tenant(current_user.tenant_id)
if not privileged and current_user.tenant_id != tenant_id:
    raise HTTPException(status_code=403, detail="Cannot access data from other tenants")
```

### テナント名の一意性

アクティブなテナント間でテナント名は一意である必要があります：

```python
existing = await self.tenant_repository.find_by_name(data.name)
if existing:
    raise ValueError(f"Tenant name '{data.name}' already exists")
```

削除済みテナント名の再利用は可能です。

### ユーザー数管理（Phase 1）

Phase 1ではユーザー数は手動管理です。タスク06（TenantUser管理）実装時に自動更新されます：

```python
# タスク06で使用予定
async def increment_user_count(self, tenant_id: str) -> None:
    """ユーザー追加時にカウントをインクリメント"""
    ...

async def decrement_user_count(self, tenant_id: str) -> None:
    """ユーザー削除時にカウントをデクリメント"""
    ...
```

## テスト

### 単体テスト実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# カバレッジレポート表示
open htmlcov/index.html
```

### レイヤー別テスト実行

```bash
# Model層テスト
pytest tests/test_models_*.py -v

# Schema層テスト
pytest tests/test_schemas_*.py -v

# Repository層テスト
pytest tests/test_repositories_*.py -v

# Service層テスト
pytest tests/test_services_*.py -v

# API層テスト
pytest tests/test_api_*.py -v
```

### タスク06関連テスト

```bash
# TenantUser管理テスト
pytest tests/test_models_tenant_user.py \
       tests/test_schemas_tenant_user.py \
       tests/test_repositories_tenant_user.py \
       tests/test_services_tenant_user.py \
       tests/test_api_tenant_users.py \
       -v --cov=app

# Domain管理テスト
pytest tests/test_models_domain.py \
       tests/test_schemas_domain.py \
       tests/test_repositories_domain.py \
       tests/test_services_domain.py \
       tests/test_api_domains.py \
       -v --cov=app

# AuthServiceClientテスト
pytest tests/test_services_auth_client.py -v
```

### テストケース数
- **合計**: 133件
  - Model層: 11件
  - Schema層: 21件
  - Repository層: 22件
  - Service層: 54件
  - API層: 25件

### カバレッジ目標
- 行カバレッジ: 80%以上
- 分岐カバレッジ: 70%以上

詳細は[テスト設計書](/workspace/docs/管理アプリ/Phase1-MVP開発/Specs/06-テナント管理サービス-ユーザー・ドメイン管理-テスト設計書.md)を参照。

## ビルド確認

```bash
# インポートチェック
python -c "from app.main import app; print('✓ All imports successful')"
```

## ライセンス

Proprietary - All rights reserved

## 関連ドキュメント

- [機能仕様書（タスク05）](/workspace/docs/管理アプリ/Phase1-MVP開発/Specs/05-テナント管理サービス-コアAPI.md)
- [機能仕様書（タスク06）](/workspace/docs/管理アプリ/Phase1-MVP開発/Specs/06-テナント管理サービス-ユーザー・ドメイン管理.md)
- [テスト設計書（タスク06）](/workspace/docs/管理アプリ/Phase1-MVP開発/Specs/06-テナント管理サービス-ユーザー・ドメイン管理-テスト設計書.md)
- [テストプランレポート（タスク06）](/workspace/docs/管理アプリ/Phase1-MVP開発/Specs/06-テナント管理サービス-ユーザー・ドメイン管理-テストプランレポート.md)
- [アーキテクチャ概要](/workspace/docs/arch/overview.md)
- [コンポーネント設計](/workspace/docs/arch/components/README.md)
- [API設計](/workspace/docs/arch/api/README.md)
- [データモデル設計](/workspace/docs/arch/data/README.md)
