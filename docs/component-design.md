# 認証認可サービス コンポーネント設計

## ドキュメント情報

- **バージョン**: 1.0.0
- **最終更新日**: 2024年
- **ステータス**: Draft

---

## 1. 概要

ユーザー認証、JWT発行、ロール管理を担当するマイクロサービスです。

## 2. ディレクトリ構造

```
src/auth-service/
├── app/
│   ├── main.py                 # FastAPIアプリケーション
│   ├── config.py               # 設定管理
│   ├── models/                 # データモデル
│   │   ├── user.py
│   │   └── role.py
│   ├── schemas/                # Pydanticスキーマ
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── role.py
│   ├── repositories/           # データアクセス層
│   │   ├── user_repository.py
│   │   └── role_repository.py
│   ├── services/               # ビジネスロジック
│   │   ├── auth_service.py
│   │   └── user_service.py
│   ├── api/                    # APIエンドポイント
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── roles.py
│   └── utils/                  # ユーティリティ
│       ├── jwt.py
│       ├── password.py
│       └── dependencies.py
├── tests/
├── infra/                      # IaC定義
│   └── container-app.bicep
├── Dockerfile
└── requirements.txt
```

## 3. 主要機能

### 3.1 認証機能

**ログイン**

```python
class AuthService:
    async def login(self, user_id: str, password: str) -> TokenResponse:
        # 1. ユーザー検証
        user = await self.user_repo.get_by_id(user_id)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")

        # 2. 特権テナント所属チェック
        if not user.is_privileged_tenant:
            raise ForbiddenError("Only privileged tenant users can login")

        # 3. ロール情報取得
        roles = await self.role_repo.get_user_roles(user.id)

        # 4. JWT生成
        token = create_jwt_token({
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "roles": [r.dict() for r in roles]
        })

        return TokenResponse(access_token=token, user=user)
```

**JWT検証**

```python
def verify_jwt_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedError("Invalid token")
```

### 3.2 ユーザー管理

**ユーザー作成**

```python
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        password_hash = hash_password(user_data.password)

        user = User(
            id=generate_uuid(),
            user_id=user_data.user_id,
            name=user_data.name,
            password_hash=password_hash,
            tenant_id=user_data.tenant_id,
            created_at=datetime.utcnow()
        )

        await self.user_repo.create(user)
        return user
```

### 3.3 ロール管理

**ロール情報収集**

```python
class RoleService:
    async def collect_roles_from_services(self) -> List[RoleDefinition]:
        """各サービスからロール定義を収集"""
        roles = []
        services = await self.service_repo.get_all_services()

        for service in services:
            service_roles = await self.http_client.get(
                f"{service.api_url}/api/roles"
            )
            roles.extend(service_roles)

        await self.role_repo.bulk_upsert(roles)
        return roles
```

## 4. データモデル

```python
class User(BaseModel):
    id: str
    user_id: str
    name: str
    password_hash: str
    tenant_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

class Role(BaseModel):
    id: str
    service_id: str
    service_name: str
    role_code: str
    role_name: str
    description: str

class UserRole(BaseModel):
    user_id: str
    role_id: str
    assigned_at: datetime
```

データベース詳細は [データ設計](../../../docs/arch/data/data-model.md) を参照してください。

## 5. 環境変数

```bash
# Database
COSMOS_DB_ENDPOINT=https://xxx.documents.azure.com:443/
COSMOS_DB_KEY=xxx
COSMOS_DB_DATABASE=auth_management

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Service
SERVICE_NAME=auth-service
PORT=8001
```

---

## 変更履歴

| バージョン | 日付 | 変更内容                                   | 作成者             |
| ---------- | ---- | ------------------------------------------ | ------------------ |
| 1.0.0      | 2024 | 初版作成（統合コンポーネント設計から分離） | Architecture Agent |
