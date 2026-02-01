"""ドメインモデルのテスト"""
import pytest
from datetime import datetime
from app.models.domain import Domain


class TestDomainModel:
    """Domainモデルのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_create_domain_with_valid_data(self, sample_domain):
            """有効なデータでDomainを作成できる"""
            # Arrange: フィクスチャから取得
            domain = sample_domain
            
            # Act: 属性を検証
            
            # Assert: 期待する構造を持っている
            assert domain.id == "domain_test_example_com"
            assert domain.domain == "example.com"
            assert domain.verified == False
            # TODO: 詳細な検証を工程3-5で実装

        def test_should_have_verified_false_by_default(self):
            """verifiedフィールドがデフォルトでFalseである"""
            # Arrange: verifiedを省略してDomain作成
            domain = Domain(
                id="domain_test",
                tenant_id="tenant_test",
                domain="test.com",
                verification_token="token123",
                created_at=datetime(2026, 2, 1, 10, 0, 0),
                created_by="user_admin"
            )
            
            # Act: verifiedを確認
            verified = domain.verified
            
            # Assert: False
            assert verified == False

        def test_should_convert_fields_to_camelcase_alias(self):
            """フィールドがcamelCaseエイリアスに変換される"""
            # Arrange: Domainを作成
            domain = Domain(
                id="domain_test",
                tenant_id="tenant_test",
                domain="test.com",
                verification_token="token123",
                created_at=datetime(2026, 2, 1, 10, 0, 0),
                created_by="user_admin"
            )
            
            # Act: model_dump(by_alias=True)を実行
            data = domain.model_dump(by_alias=True)
            
            # Assert: キャメルケースになっている
            assert "tenantId" in data
            assert "verificationToken" in data
            assert "verifiedAt" in data
            assert "verifiedBy" in data
            assert "createdAt" in data
            assert "createdBy" in data

        def test_should_serialize_to_json_with_alias(self):
            """エイリアスを使用してJSONにシリアライズできる"""
            # Arrange: Domainを作成
            domain = Domain(
                id="domain_test",
                tenant_id="tenant_test",
                domain="test.com",
                verified=True,
                verification_token="token123",
                created_at=datetime(2026, 2, 1, 10, 0, 0),
                created_by="user_admin"
            )
            
            # Act: model_dump_json(by_alias=True)を実行
            json_str = domain.model_dump_json(by_alias=True)
            
            # Assert: JSON文字列が正しい
            assert '"tenantId":"tenant_test"' in json_str.replace(" ", "")
            assert '"verificationToken":"token123"' in json_str.replace(" ", "")
            assert '"verified":true' in json_str.replace(" ", "")

    class Test境界値:
        """境界値テスト"""

        def test_should_handle_optional_fields_with_none(self):
            """OptionalフィールドがNone値を適切に処理する"""
            # Arrange: verified_at, verified_byをNoneにしてDomain作成
            domain = Domain(
                id="domain_test",
                tenant_id="tenant_test",
                domain="test.com",
                verification_token="token123",
                verified_at=None,
                verified_by=None,
                created_at=datetime(2026, 2, 1, 10, 0, 0),
                created_by="user_admin"
            )
            
            # Act: Noneフィールドを確認
            
            # Assert: Noneが許可される
            assert domain.verified_at is None
            assert domain.verified_by is None

        def test_should_convert_datetime_to_iso8601_format(self):
            """日時フィールドがISO8601形式に変換される"""
            # Arrange: 特定の日時でDomainを作成
            domain = Domain(
                id="domain_test",
                tenant_id="tenant_test",
                domain="test.com",
                verification_token="token123",
                created_at=datetime(2026, 2, 1, 10, 0, 0),
                verified_at=datetime(2026, 2, 1, 11, 0, 0),
                created_by="user_admin",
                verified_by="user_admin"
            )
            
            # Act: JSONにシリアライズ
            json_str = domain.model_dump_json(by_alias=True)
            
            # Assert: ISO8601形式（末尾Z付き）
            assert '"createdAt":"2026-02-01T10:00:00Z"' in json_str.replace(" ", "")
            assert '"verifiedAt":"2026-02-01T11:00:00Z"' in json_str.replace(" ", "")

