"""pytest設定とフィクスチャ"""
import pytest
from typing import AsyncGenerator
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock

from app.models.tenant import Tenant
from app.models.tenant_user import TenantUser
from app.models.domain import Domain
from app.utils.jwt import TokenData


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    非同期HTTPクライアント
    
    Note: app.mainのインポートは実際のmain.pyが実装された後に有効化
    """
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# ===========================
# サンプルテナントデータ
# ===========================

@pytest.fixture
def sample_tenant_data():
    """サンプルテナント作成データ"""
    return {
        "name": "test-corp",
        "displayName": "Test Corporation",
        "plan": "standard",
        "maxUsers": 100,
        "metadata": {
            "industry": "IT",
            "country": "JP"
        }
    }


@pytest.fixture
def sample_tenant():
    """サンプルTenantモデル"""
    return Tenant(
        id="tenant_test",
        tenant_id="tenant_test",
        name="test",
        display_name="Test Tenant",
        is_privileged=False,
        status="active",
        plan="standard",
        user_count=0,
        max_users=100,
        metadata={},
        created_at=datetime(2026, 2, 1, 10, 0, 0),
        updated_at=datetime(2026, 2, 1, 10, 0, 0),
        created_by="user_admin_001",
        updated_by="user_admin_001",
    )


@pytest.fixture
def privileged_tenant():
    """特権テナント"""
    return Tenant(
        id="tenant_privileged",
        tenant_id="tenant_privileged",
        name="privileged",
        display_name="管理会社",
        is_privileged=True,
        status="active",
        plan="privileged",
        user_count=5,
        max_users=50,
        metadata={},
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=datetime(2026, 1, 1, 0, 0, 0),
        created_by=None,
        updated_by=None,
    )


@pytest.fixture
def regular_tenant():
    """一般テナント"""
    return Tenant(
        id="tenant_acme",
        tenant_id="tenant_acme",
        name="acme",
        display_name="Acme Corporation",
        is_privileged=False,
        status="active",
        plan="standard",
        user_count=25,
        max_users=100,
        metadata={
            "industry": "Manufacturing",
            "country": "US"
        },
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=datetime(2026, 1, 20, 15, 0, 0),
        created_by="user_admin_001",
        updated_by="user_admin_001",
    )


@pytest.fixture
def tenant_with_users():
    """ユーザーが存在するテナント（削除不可）"""
    return Tenant(
        id="tenant_populated",
        tenant_id="tenant_populated",
        name="populated",
        display_name="Populated Tenant",
        is_privileged=False,
        status="active",
        plan="standard",
        user_count=10,  # ユーザーが存在
        max_users=100,
        metadata={},
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=datetime(2026, 1, 1, 0, 0, 0),
        created_by="user_admin_001",
        updated_by="user_admin_001",
    )


# ===========================
# JWT / TokenData フィクスチャ
# ===========================

@pytest.fixture
def privileged_token_data():
    """特権テナントのTokenData"""
    return TokenData(
        user_id="user_admin_001",
        tenant_id="tenant_privileged",
        username="admin",
        roles=["tenant-management:全体管理者"],
    )


@pytest.fixture
def regular_token_data():
    """一般テナントのTokenData"""
    return TokenData(
        user_id="user_regular_001",
        tenant_id="tenant_acme",
        username="john.doe",
        roles=["tenant-management:閲覧者"],
    )


@pytest.fixture
def manager_token_data():
    """管理者ロールのTokenData"""
    return TokenData(
        user_id="user_manager_001",
        tenant_id="tenant_acme",
        username="manager",
        roles=["tenant-management:管理者"],
    )


# ===========================
# Cosmos DB モックヘルパー
# ===========================

@pytest.fixture
def mock_cosmos_container():
    """Cosmos DB Containerのモック"""
    return MagicMock()


class AsyncIteratorMock:
    """非同期イテレータのモック"""
    
    def __init__(self, items: list):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


def create_mock_query_result(items: list):
    """
    Cosmos DBクエリ結果のモック作成ヘルパー
    
    Args:
        items: 返却するアイテムのリスト
    
    Returns:
        非同期イテレータ
    """
    return AsyncIteratorMock(items)


# ===========================
# 境界値テストデータ
# ===========================

INVALID_TENANT_NAMES = [
    ("", "空文字列"),
    ("ab", "短すぎる(2文字)"),
    ("a" * 101, "長すぎる(101文字)"),
    ("test tenant", "スペース含む"),
    ("test@corp", "不正な文字(@)"),
    ("test<script>", "不正な文字(<>)"),
]

VALID_TENANT_NAMES = [
    ("abc", "最小長(3文字)"),
    ("a" * 100, "最大長(100文字)"),
    ("test-corp", "ハイフン含む"),
    ("test_corp", "アンダースコア含む"),
    ("test123", "数字含む"),
    ("TEST", "大文字"),
]

INVALID_DISPLAY_NAMES = [
    ("a" * 201, "長すぎる(201文字)"),
]

VALID_DISPLAY_NAMES = [
    ("A", "最小長(1文字)"),
    ("a" * 200, "最大長(200文字)"),
    ("テスト株式会社", "日本語"),
    ("Test Corp Inc.", "特殊文字含む"),
]

INVALID_PLANS = [
    "ultra",
    "enterprise",
    "STANDARD",  # 大文字
    "",
]

VALID_PLANS = [
    "free",
    "standard",
    "premium",
]

INVALID_MAX_USERS = [
    0,
    -1,
    -100,
    10001,
    100000,
]

VALID_MAX_USERS = [
    1,      # 最小
    100,    # デフォルト
    5000,
    10000,  # 最大
]


# ===========================
# TenantUser フィクスチャ
# ===========================

@pytest.fixture
def sample_tenant_user():
    """サンプルTenantUser"""
    return TenantUser(
        id="tenant_user_tenant_test_user_123",
        tenant_id="tenant_test",
        user_id="user_123",
        assigned_at=datetime(2026, 2, 1, 10, 0, 0),
        assigned_by="user_admin_001",
    )


@pytest.fixture
def sample_tenant_user_data():
    """サンプルTenantUser作成データ"""
    return {
        "userId": "user_456",
    }


# ===========================
# Domain フィクスチャ
# ===========================

@pytest.fixture
def sample_domain():
    """サンプルDomain（未検証）"""
    return Domain(
        id="domain_test_example_com",
        tenant_id="tenant_test",
        domain="example.com",
        verified=False,
        verification_token="txt-verification-abc123def456",
        verified_at=None,
        verified_by=None,
        created_at=datetime(2026, 2, 1, 10, 0, 0),
        created_by="user_admin_001",
    )


@pytest.fixture
def verified_domain():
    """検証済みDomain"""
    return Domain(
        id="domain_test_verified_com",
        tenant_id="tenant_test",
        domain="verified.com",
        verified=True,
        verification_token="txt-verification-xyz789",
        verified_at=datetime(2026, 2, 1, 11, 0, 0),
        verified_by="user_admin_001",
        created_at=datetime(2026, 2, 1, 10, 0, 0),
        created_by="user_admin_001",
    )


@pytest.fixture
def sample_domain_data():
    """サンプルDomain作成データ"""
    return {
        "domain": "newdomain.com",
    }


# ===========================
# 認証サービスクライアント モック
# ===========================

@pytest.fixture
def mock_auth_service_user_response():
    """認証サービスからのユーザー詳細レスポンス"""
    return {
        "id": "user_123",
        "tenantId": "tenant_test",
        "username": "test.user",
        "email": "test.user@example.com",
        "isActive": True,
        "createdAt": "2026-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_httpx_client_success():
    """HTTPXクライアントのモック（成功）"""
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    mock.get = AsyncMock()
    return mock


# ===========================
# DNS モック
# ===========================

@pytest.fixture
def mock_dns_resolver():
    """DNSリゾルバーのモック"""
    from unittest.mock import MagicMock
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_dns_txt_records():
    """DNS TXTレコードのモックデータ"""
    return [
        "txt-verification-abc123def456",
        "v=spf1 include:_spf.google.com ~all"
    ]


# ===========================
# 境界値テストデータ (タスク06)
# ===========================

INVALID_DOMAINS = [
    ("", "空文字列"),
    ("ab", "短すぎる(2文字)"),
    ("a" * 254, "長すぎる(254文字)"),
    ("localhost", "禁止ドメイン"),
    ("example.com", "禁止ドメイン"),
    ("127.0.0.1", "IPアドレス（禁止）"),
    ("test..com", "連続ドット"),
    (".test.com", "先頭ドット"),
    ("test.com.", "末尾ドット"),
    ("test_domain.com", "アンダースコア含む"),
    ("test domain.com", "スペース含む"),
    ("тест.com", "Cyrillic文字（ホモグラフ攻撃）"),
]

VALID_DOMAINS = [
    ("abc.com", "最小構成"),
    ("a-b.co.jp", "ハイフン含む"),
    ("subdomain.example.org", "サブドメイン"),
    ("long-domain-name-with-multiple-parts.example.com", "長いドメイン"),
    ("test123.net", "数字含む"),
]
