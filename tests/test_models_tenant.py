"""
テナントモデル層のユニットテスト

テストケース:
- TC-M001 ~ TC-M015: Tenantモデル、TenantCreate、TenantUpdateのバリデーション
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.tenant import Tenant, TenantCreate, TenantUpdate
from tests.conftest import (
    INVALID_TENANT_NAMES,
    VALID_TENANT_NAMES,
    INVALID_DISPLAY_NAMES,
    VALID_DISPLAY_NAMES,
    INVALID_PLANS,
    VALID_PLANS,
    INVALID_MAX_USERS,
    VALID_MAX_USERS,
)


class TestTenantModel:
    """Tenantモデルのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_tenant_モデル作成_デフォルト値(self):
            """
            テストケース: TC-M001
            目的: Tenantモデルのデフォルト値が正しく設定されることを検証
            前提条件: 必須フィールドのみ指定
            実行手順:
              1. 必須フィールド(id, tenant_id, name, display_name)のみ指定
              2. Tenantオブジェクトを作成
            期待結果:
              - type="tenant"
              - status="active"
              - plan="standard"
              - user_count=0
              - max_users=100
              - is_privileged=False
              - created_at, updated_atが設定される
            """
            # Arrange & Act
            tenant = Tenant(
                id="tenant_test",
                tenant_id="tenant_test",
                name="test",
                display_name="Test Tenant",
            )

            # Assert
            assert tenant.id == "tenant_test"
            assert tenant.tenant_id == "tenant_test"
            assert tenant.name == "test"
            assert tenant.display_name == "Test Tenant"
            assert tenant.type == "tenant"
            assert tenant.status == "active"
            assert tenant.plan == "standard"
            assert tenant.user_count == 0
            assert tenant.max_users == 100
            assert tenant.is_privileged is False
            assert isinstance(tenant.created_at, datetime)
            assert isinstance(tenant.updated_at, datetime)

        def test_tenant_モデル作成_全フィールド指定(self):
            """
            テストケース: TC-M002
            目的: 全フィールドを指定してTenantモデルが作成できることを検証
            前提条件: すべてのフィールドに有効な値を指定
            実行手順:
              1. すべてのフィールドを指定してTenantオブジェクトを作成
            期待結果:
              - すべてのフィールドが指定した値で設定される
            """
            # Arrange
            created_at = datetime(2026, 2, 1, 10, 0, 0)
            updated_at = datetime(2026, 2, 1, 12, 0, 0)
            metadata = {"industry": "IT", "country": "JP"}

            # Act
            tenant = Tenant(
                id="tenant_full",
                tenant_id="tenant_full",
                type="tenant",
                name="fulltest",
                display_name="Full Test Tenant",
                is_privileged=True,
                status="suspended",
                plan="premium",
                user_count=50,
                max_users=500,
                metadata=metadata,
                created_at=created_at,
                updated_at=updated_at,
                created_by="user_001",
                updated_by="user_002",
            )

            # Assert
            assert tenant.id == "tenant_full"
            assert tenant.tenant_id == "tenant_full"
            assert tenant.type == "tenant"
            assert tenant.name == "fulltest"
            assert tenant.display_name == "Full Test Tenant"
            assert tenant.is_privileged is True
            assert tenant.status == "suspended"
            assert tenant.plan == "premium"
            assert tenant.user_count == 50
            assert tenant.max_users == 500
            assert tenant.metadata == metadata
            assert tenant.created_at == created_at
            assert tenant.updated_at == updated_at
            assert tenant.created_by == "user_001"
            assert tenant.updated_by == "user_002"

        def test_tenant_キャメルケースエイリアス(self):
            """
            テストケース: TC-M003
            目的: エイリアス(CamelCase)が正しく機能することを検証
            前提条件: エイリアスを使用してモデルをインスタンス化
            実行手順:
              1. キャメルケースのエイリアスでTenantを作成
              2. 各フィールドが正しく変換される
            期待結果:
              - tenant_id <-> tenantId
              - display_name <-> displayName
              - is_privileged <-> isPrivileged
              - user_count <-> userCount
              - max_users <-> maxUsers
              - created_at <-> createdAt
              - updated_at <-> updatedAt
              - created_by <-> createdBy
              - updated_by <-> updatedBy
            """
            # Arrange
            data = {
                "id": "tenant_alias",
                "tenantId": "tenant_alias",
                "name": "alias",
                "displayName": "Alias Test",
                "isPrivileged": True,
                "userCount": 10,
                "maxUsers": 200,
                "createdAt": "2026-02-01T10:00:00Z",
                "updatedAt": "2026-02-01T10:00:00Z",
                "createdBy": "user_admin",
                "updatedBy": "user_admin",
            }

            # Act
            tenant = Tenant(**data)

            # Assert
            assert tenant.tenant_id == "tenant_alias"
            assert tenant.display_name == "Alias Test"
            assert tenant.is_privileged is True
            assert tenant.user_count == 10
            assert tenant.max_users == 200
            assert tenant.created_by == "user_admin"
            assert tenant.updated_by == "user_admin"

        def test_tenant_JSON変換(self):
            """
            テストケース: TC-M004
            目的: model_dump(by_alias=True)でキャメルケースに変換されることを検証
            前提条件: Tenantオブジェクトが存在
            実行手順:
              1. Tenantオブジェクトを作成
              2. model_dump(by_alias=True)を実行
            期待結果:
              - キャメルケースのキーで辞書が返される
              - datetimeがISOフォーマット(+Z)で文字列化される
            """
            # Arrange
            tenant = Tenant(
                id="tenant_json",
                tenant_id="tenant_json",
                name="json",
                display_name="JSON Test",
                user_count=5,
                max_users=100,
            )

            # Act
            data = tenant.model_dump(by_alias=True)

            # Assert
            assert "tenantId" in data
            assert "displayName" in data
            assert "isPrivileged" in data
            assert "userCount" in data
            assert "maxUsers" in data
            assert "createdAt" in data
            assert "updatedAt" in data
            assert data["tenantId"] == "tenant_json"
            assert data["displayName"] == "JSON Test"
            assert data["userCount"] == 5

    class Test異常系:
        """異常系テスト"""

        def test_tenant_必須フィールド欠如_id(self):
            """
            テストケース: TC-M005
            目的: 必須フィールド(id)欠如時にValidationErrorが発生することを検証
            前提条件: idを指定せずにモデルを作成
            実行手順:
              1. idなしでTenantオブジェクト作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                Tenant(
                    tenant_id="tenant_test",
                    name="test",
                    display_name="Test",
                )

        def test_tenant_必須フィールド欠如_tenant_id(self):
            """
            テストケース: TC-M006
            目的: 必須フィールド(tenant_id)欠如時にValidationErrorが発生することを検証
            前提条件: tenant_idを指定せずにモデルを作成
            実行手順:
              1. tenant_idなしでTenantオブジェクト作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                Tenant(
                    id="tenant_test",
                    name="test",
                    display_name="Test",
                )

        def test_tenant_必須フィールド欠如_name(self):
            """
            テストケース: TC-M007
            目的: 必須フィールド(name)欠如時にValidationErrorが発生することを検証
            前提条件: nameを指定せずにモデルを作成
            実行手順:
              1. nameなしでTenantオブジェクト作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                Tenant(
                    id="tenant_test",
                    tenant_id="tenant_test",
                    display_name="Test",
                )


class TestTenantCreateModel:
    """TenantCreateモデルのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_tenant_create_正常なデータ(self):
            """
            テストケース: TC-M008
            目的: 有効なデータでTenantCreateモデルが作成できることを検証
            前提条件: すべてのフィールドに有効な値を指定
            実行手順:
              1. 有効なデータでTenantCreateオブジェクトを作成
            期待結果:
              - 正常に作成される
              - すべてのフィールドが設定される
            """
            # Arrange & Act
            tenant_create = TenantCreate(
                name="test-corp",
                display_name="Test Corporation",
                plan="standard",
                max_users=100,
                metadata={"industry": "IT"},
            )

            # Assert
            assert tenant_create.name == "test-corp"
            assert tenant_create.display_name == "Test Corporation"
            assert tenant_create.plan == "standard"
            assert tenant_create.max_users == 100
            assert tenant_create.metadata == {"industry": "IT"}

        def test_tenant_create_キャメルケース入力(self):
            """
            テストケース: TC-M008-2
            目的: キャメルケースのフィールド名で入力できることを検証
            前提条件: キャメルケースのフィールド名でデータを指定
            実行手順:
              1. displayName, maxUsersをキャメルケースで指定
              2. TenantCreateオブジェクトを作成
            期待結果:
              - 正常に作成される
              - display_name, max_usersに値が設定される
            """
            # Arrange
            data = {
                "name": "test-corp",
                "displayName": "Test Corporation",
                "plan": "premium",
                "maxUsers": 500,
            }

            # Act
            tenant_create = TenantCreate(**data)

            # Assert
            assert tenant_create.name == "test-corp"
            assert tenant_create.display_name == "Test Corporation"
            assert tenant_create.plan == "premium"
            assert tenant_create.max_users == 500

    class Test異常系:
        """異常系テスト"""

        def test_tenant_create_必須フィールド欠如_name(self):
            """
            テストケース: TC-M008-3
            目的: 必須フィールド(name)欠如時にValidationErrorが発生することを検証
            前提条件: nameを指定せずにモデルを作成
            実行手順:
              1. nameなしでTenantCreateオブジェクト作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantCreate(display_name="Test")

        def test_tenant_create_必須フィールド欠如_display_name(self):
            """
            テストケース: TC-M008-4
            目的: 必須フィールド(display_name)欠如時にValidationErrorが発生することを検証
            前提条件: display_nameを指定せずにモデルを作成
            実行手順:
              1. display_nameなしでTenantCreateオブジェクト作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantCreate(name="test")

        @pytest.mark.parametrize("invalid_name,description", INVALID_TENANT_NAMES)
        def test_tenant_create_不正なname形式(self, invalid_name, description):
            """
            テストケース: TC-M009
            目的: 不正なname形式でValidationErrorが発生することを検証
            前提条件: name検証ルールが定義されている
            実行手順:
              1. 不正なname(空、短すぎる、長すぎる、不正文字)でTenantCreate作成
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantCreate(name=invalid_name, display_name="Test")

        @pytest.mark.parametrize("invalid_plan", INVALID_PLANS)
        def test_tenant_create_不正なplan(self, invalid_plan):
            """
            テストケース: TC-M010
            目的: 不正なplan値でValidationErrorが発生することを検証
            前提条件: planはfree/standard/premiumのみ許可
            実行手順:
              1. 不正なplan値でTenantCreate作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantCreate(name="test", display_name="Test", plan=invalid_plan)

    class Test境界値:
        """境界値テスト"""

        @pytest.mark.parametrize("valid_name,description", VALID_TENANT_NAMES)
        def test_tenant_create_name境界値_有効(self, valid_name, description):
            """
            テストケース: TC-M011, TC-M012
            目的: name境界値(3文字、100文字)で正常に作成できることを検証
            前提条件: nameは3-100文字
            実行手順:
              1. 境界値のnameでTenantCreate作成
            期待結果:
              - 正常に作成される
            """
            # Arrange & Act
            tenant_create = TenantCreate(name=valid_name, display_name="Test")

            # Assert
            assert tenant_create.name == valid_name
            assert tenant_create.display_name == "Test"

        @pytest.mark.parametrize("max_users", VALID_MAX_USERS)
        def test_tenant_create_max_users境界値_有効(self, max_users):
            """
            テストケース: TC-M013, TC-M014
            目的: max_users境界値(1、10000)で正常に作成できることを検証
            前提条件: max_usersは1-10000
            実行手順:
              1. 境界値のmax_usersでTenantCreate作成
            期待結果:
              - 正常に作成される
            """
            # Arrange & Act
            tenant_create = TenantCreate(name="test", display_name="Test", max_users=max_users)

            # Assert
            assert tenant_create.max_users == max_users

        @pytest.mark.parametrize("invalid_max_users", INVALID_MAX_USERS)
        def test_tenant_create_max_users境界値_無効(self, invalid_max_users):
            """
            テストケース: TC-M014-2
            目的: max_users境界値外(0、-1、10001)でエラーになることを検証
            前提条件: max_usersは1-10000
            実行手順:
              1. 境界値外のmax_usersでTenantCreate作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantCreate(name="test", display_name="Test", max_users=invalid_max_users)


class TestTenantUpdateModel:
    """TenantUpdateモデルのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_tenant_update_部分更新_display_nameのみ(self):
            """
            テストケース: TC-M015
            目的: 部分更新(display_nameのみ)が可能であることを検証
            前提条件: TenantUpdateは全フィールドOptional
            実行手順:
              1. display_nameのみ指定してTenantUpdateオブジェクトを作成
            期待結果:
              - 正常に作成される
              - display_nameのみ値が設定され、他はNone
            """
            # Arrange & Act
            tenant_update = TenantUpdate(display_name="Updated Name")

            # Assert
            assert tenant_update.display_name == "Updated Name"
            assert tenant_update.plan is None
            assert tenant_update.max_users is None
            assert tenant_update.metadata is None

        def test_tenant_update_部分更新_planのみ(self):
            """
            テストケース: TC-M015-2
            目的: 部分更新(planのみ)が可能であることを検証
            前提条件: TenantUpdateは全フィールドOptional
            実行手順:
              1. planのみ指定してTenantUpdateオブジェクトを作成
            期待結果:
              - 正常に作成される
              - planのみ値が設定され、他はNone
            """
            # Arrange & Act
            tenant_update = TenantUpdate(plan="premium")

            # Assert
            assert tenant_update.plan == "premium"
            assert tenant_update.display_name is None
            assert tenant_update.max_users is None

        def test_tenant_update_全フィールド更新(self):
            """
            テストケース: TC-M015-3
            目的: 全フィールドを更新できることを検証
            前提条件: すべてのフィールドに有効な値を指定
            実行手順:
              1. すべてのフィールドを指定してTenantUpdateオブジェクトを作成
            期待結果:
              - 正常に作成される
              - すべてのフィールドが設定される
            """
            # Arrange & Act
            tenant_update = TenantUpdate(
                display_name="Updated Name",
                plan="premium",
                max_users=1000,
                metadata={"key": "value"},
            )

            # Assert
            assert tenant_update.display_name == "Updated Name"
            assert tenant_update.plan == "premium"
            assert tenant_update.max_users == 1000
            assert tenant_update.metadata == {"key": "value"}

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.parametrize("invalid_display_name,description", INVALID_DISPLAY_NAMES)
        def test_tenant_update_不正なdisplay_name(self, invalid_display_name, description):
            """
            テストケース: TC-M015-4
            目的: 不正なdisplay_name形式でValidationErrorが発生することを検証
            前提条件: display_nameは1-200文字
            実行手順:
              1. 不正なdisplay_name(空、長すぎる)でTenantUpdate作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantUpdate(display_name=invalid_display_name)

        @pytest.mark.parametrize("invalid_plan", INVALID_PLANS)
        def test_tenant_update_不正なplan(self, invalid_plan):
            """
            テストケース: TC-M015-5
            目的: 不正なplan値でValidationErrorが発生することを検証
            前提条件: planはfree/standard/premiumのみ許可
            実行手順:
              1. 不正なplan値でTenantUpdate作成を試みる
            期待結果:
              - ValidationErrorが発生
            """
            # Act & Assert
            with pytest.raises(ValidationError):
                TenantUpdate(plan=invalid_plan)
