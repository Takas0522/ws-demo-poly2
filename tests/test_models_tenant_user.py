"""テナントユーザーモデルのテスト"""
import pytest
from datetime import datetime
from app.models.tenant_user import TenantUser


class TestTenantUserModel:
    """TenantUserモデルのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_create_tenant_user_with_valid_data(self, sample_tenant_user):
            """有効なデータでTenantUserを作成できる"""
            # Arrange: フィクスチャから取得
            tenant_user = sample_tenant_user
            
            # Act: 属性を検証
            
            # Assert: 期待する構造を持っている
            assert tenant_user.id == "tenant_user_tenant_test_user_123"
            assert tenant_user.tenant_id == "tenant_test"
            assert tenant_user.user_id == "user_123"
            assert tenant_user.type == "tenant_user"
            # TODO: 詳細な検証を工程3-5で実装

        def test_should_convert_fields_to_camelcase_alias(self):
            """フィールドがcamelCaseエイリアスに変換される"""
            # Arrange: TenantUserを作成
            tenant_user = TenantUser(
                id="tenant_user_test",
                tenant_id="tenant_test",
                user_id="user_123",
                assigned_at=datetime(2026, 2, 1, 10, 0, 0),
                assigned_by="user_admin"
            )
            
            # Act: model_dump(by_alias=True)を実行
            data = tenant_user.model_dump(by_alias=True)
            
            # Assert: キャメルケースになっている
            assert "tenantId" in data
            assert "userId" in data
            assert "assignedAt" in data
            assert "assignedBy" in data
            assert data["tenantId"] == "tenant_test"
            assert data["userId"] == "user_123"

        def test_should_serialize_to_json_with_alias(self):
            """エイリアスを使用してJSONにシリアライズできる"""
            # Arrange: TenantUserを作成
            tenant_user = TenantUser(
                id="tenant_user_test",
                tenant_id="tenant_test",
                user_id="user_123",
                assigned_at=datetime(2026, 2, 1, 10, 0, 0),
                assigned_by="user_admin"
            )
            
            # Act: model_dump_json(by_alias=True)を実行
            json_str = tenant_user.model_dump_json(by_alias=True)
            
            # Assert: JSON文字列が正しい
            assert '"tenantId":"tenant_test"' in json_str.replace(" ", "")
            assert '"userId":"user_123"' in json_str.replace(" ", "")
            assert '"assignedBy":"user_admin"' in json_str.replace(" ", "")

    class Test境界値:
        """境界値テスト"""

        def test_should_convert_datetime_to_iso8601_format(self):
            """日時フィールドがISO8601形式に変換される"""
            # Arrange: 特定の日時でTenantUserを作成
            tenant_user = TenantUser(
                id="tenant_user_test",
                tenant_id="tenant_test",
                user_id="user_123",
                assigned_at=datetime(2026, 2, 1, 10, 0, 0),
                assigned_by="user_admin"
            )
            
            # Act: JSONにシリアライズ
            json_str = tenant_user.model_dump_json(by_alias=True)
            
            # Assert: ISO8601形式（末尾Z付き）
            assert '"assignedAt":"2026-02-01T10:00:00Z"' in json_str.replace(" ", "")

        def test_should_handle_assigned_at_with_default_value(self):
            """assigned_atがデフォルト値（現在時刻）を持つ"""
            # Arrange: assigned_atを省略してTenantUser作成
            before = datetime.utcnow()
            tenant_user = TenantUser(
                id="tenant_user_test",
                tenant_id="tenant_test",
                user_id="user_123",
                assigned_by="user_admin"
            )
            after = datetime.utcnow()
            
            # Act: assigned_atを確認
            assigned_at = tenant_user.assigned_at
            
            # Assert: 現在時刻に近い
            assert before <= assigned_at <= after

