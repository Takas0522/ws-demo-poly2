# 認証認可サービス API 仕様書

## ドキュメント情報

- **バージョン**: 1.0.0
- **最終更新日**: 2024年
- **ステータス**: Draft
- **共通仕様**: [共通API仕様](../../../docs/arch/api/api-specification.md) を参照

---

## 概要

**ベースURL**: `http://localhost:8001/api/v1`

認証認可サービスは、ユーザー認証、JWT発行・検証、ロール管理機能を提供します。

---

## 1. 認証エンドポイント

### 1.1 ログイン

```http
POST /auth/login
```

**リクエスト**:

```json
{
  "user_id": "admin@example.com",
  "password": "password123"
}
```

**レスポンス** (200):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "user-uuid",
    "user_id": "admin@example.com",
    "name": "管理者",
    "tenant_id": "tenant-uuid",
    "roles": [
      {
        "service_id": "service-uuid",
        "service_name": "テナント管理サービス",
        "role_code": "global_admin",
        "role_name": "全体管理者"
      }
    ]
  }
}
```

**エラー** (401):

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid user_id or password"
  }
}
```

**エラー** (403):

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Only privileged tenant users can login"
  }
}
```

### 1.2 トークン検証

```http
POST /auth/verify
```

**リクエスト**:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**レスポンス** (200):

```json
{
  "valid": true,
  "payload": {
    "user_id": "user-uuid",
    "tenant_id": "tenant-uuid",
    "roles": [...]
  }
}
```

**エラー** (401):

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

### 1.3 現在のユーザー情報取得

```http
GET /auth/me
Authorization: Bearer {token}
```

**レスポンス** (200):

```json
{
  "id": "user-uuid",
  "user_id": "admin@example.com",
  "name": "管理者",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "last_login_at": "2024-01-25T09:00:00Z",
  "roles": [...]
}
```

---

## 2. ユーザー管理エンドポイント

### 2.1 ユーザー一覧取得

```http
GET /users?page=1&per_page=20&tenant_id={tenant_id}
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "data": [
    {
      "id": "user-uuid",
      "user_id": "user@example.com",
      "name": "山田太郎",
      "tenant_id": "tenant-uuid",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

### 2.2 ユーザー詳細取得

```http
GET /users/{user_id}
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "id": "user-uuid",
  "user_id": "user@example.com",
  "name": "山田太郎",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "last_login_at": "2024-01-25T09:00:00Z",
  "roles": [
    {
      "id": "role-uuid",
      "service_id": "service-uuid",
      "service_name": "テナント管理サービス",
      "role_code": "admin",
      "role_name": "管理者"
    }
  ]
}
```

### 2.3 ユーザー作成

```http
POST /users
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**リクエスト**:

```json
{
  "user_id": "newuser@example.com",
  "name": "新規ユーザー",
  "password": "initialPassword123",
  "tenant_id": "tenant-uuid"
}
```

**レスポンス** (201):

```json
{
  "id": "user-uuid",
  "user_id": "newuser@example.com",
  "name": "新規ユーザー",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "created_at": "2024-01-25T10:00:00Z"
}
```

**エラー** (409):

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "User ID already exists"
  }
}
```

### 2.4 ユーザー更新

```http
PUT /users/{user_id}
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**リクエスト**:

```json
{
  "name": "更新後の名前",
  "is_active": true
}
```

**レスポンス** (200):

```json
{
  "id": "user-uuid",
  "user_id": "user@example.com",
  "name": "更新後の名前",
  "tenant_id": "tenant-uuid",
  "is_active": true,
  "updated_at": "2024-01-25T11:00:00Z"
}
```

### 2.5 ユーザー削除

```http
DELETE /users/{user_id}
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**レスポンス** (204): No Content

---

## 3. ロール管理エンドポイント

### 3.1 ロール一覧取得

```http
GET /roles?service_id={service_id}
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "data": [
    {
      "id": "role-uuid",
      "service_id": "service-uuid",
      "service_name": "テナント管理サービス",
      "role_code": "global_admin",
      "role_name": "全体管理者",
      "description": "特権テナントに対する操作が可能",
      "permissions": ["tenant:*"]
    }
  ]
}
```

### 3.2 ユーザーロール取得

```http
GET /users/{user_id}/roles
Authorization: Bearer {token}
```

**必要ロール**: 閲覧者以上

**レスポンス** (200):

```json
{
  "user_id": "user-uuid",
  "roles": [
    {
      "id": "role-uuid",
      "service_id": "service-uuid",
      "service_name": "テナント管理サービス",
      "role_code": "admin",
      "role_name": "管理者",
      "assigned_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 3.3 ユーザーロール割り当て

```http
POST /users/{user_id}/roles
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**リクエスト**:

```json
{
  "role_id": "role-uuid"
}
```

**レスポンス** (201):

```json
{
  "user_id": "user-uuid",
  "role_id": "role-uuid",
  "assigned_at": "2024-01-25T10:00:00Z"
}
```

**エラー** (403):

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Cannot assign role from service not available to user's tenant"
  }
}
```

### 3.4 ユーザーロール削除

```http
DELETE /users/{user_id}/roles/{role_id}
Authorization: Bearer {token}
```

**必要ロール**: 全体管理者

**レスポンス** (204): No Content

---

## エンドポイント一覧

| メソッド | エンドポイント                            | 説明               | 必要ロール |
| -------- | ----------------------------------------- | ------------------ | ---------- |
| POST     | `/api/v1/auth/login`                      | ログイン           | -          |
| POST     | `/api/v1/auth/verify`                     | トークン検証       | -          |
| GET      | `/api/v1/auth/me`                         | 現在のユーザー情報 | 認証済み   |
| GET      | `/api/v1/users`                           | ユーザー一覧       | 閲覧者以上 |
| GET      | `/api/v1/users/{user_id}`                 | ユーザー詳細       | 閲覧者以上 |
| POST     | `/api/v1/users`                           | ユーザー作成       | 全体管理者 |
| PUT      | `/api/v1/users/{user_id}`                 | ユーザー更新       | 全体管理者 |
| DELETE   | `/api/v1/users/{user_id}`                 | ユーザー削除       | 全体管理者 |
| GET      | `/api/v1/roles`                           | ロール一覧         | 閲覧者以上 |
| GET      | `/api/v1/users/{user_id}/roles`           | ユーザーロール取得 | 閲覧者以上 |
| POST     | `/api/v1/users/{user_id}/roles`           | ロール割り当て     | 全体管理者 |
| DELETE   | `/api/v1/users/{user_id}/roles/{role_id}` | ロール削除         | 全体管理者 |

---

## 変更履歴

| バージョン | 日付 | 変更内容                                | 作成者             |
| ---------- | ---- | --------------------------------------- | ------------------ |
| 1.0.0      | 2024 | 初版作成（統合APIドキュメントから分離） | Architecture Agent |
