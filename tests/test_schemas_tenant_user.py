"""テナントユーザースキーマのテスト"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.tenant_user import (
    TenantUserCreateRequest,
    TenantUserResponse,
    TenantUserListResponse
)


class TestTenantUserCreateRequest:
    """TenantUserCreateRequestスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_validate_with_valid_user_id(self):
            """有効なuser_idでバリデーション成功"""
            # Arrange: 有効なuser_idを準備
            data = {"user_id": "user_123"}
            
            # Act: スキーマ作成
            request = TenantUserCreateRequest(**data)
            
            # Assert: バリデーション成功
            assert request.user_id == "user_123"

        def test_should_accept_user_id_with_alias(self):
            """userId（camelCase）でも受け入れる"""
            # Arrange: camelCaseのデータを準備
            data = {"userId": "user_456"}
            
            # Act: スキーマ作成
            request = TenantUserCreateRequest(**data)
            
            # Assert: 正しく変換される
            assert request.user_id == "user_456"

    class Test異常系:
        """異常系テスト"""

        def test_should_reject_empty_user_id(self):
            """空文字のuser_idを拒否する"""
            # Arrange: 空文字のuser_idを準備
            data = {"user_id": ""}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError) as exc_info:
                TenantUserCreateRequest(**data)
            assert "user_id" in str(exc_info.value)

        def test_should_reject_missing_user_id(self):
            """user_idが欠落している場合エラー"""
            # Arrange: user_idなしのデータ
            data = {}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError) as exc_info:
                TenantUserCreateRequest(**data)
            assert "user_id" in str(exc_info.value) or "userId" in str(exc_info.value)


class TestTenantUserResponse:
    """TenantUserResponseスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_serialize_tenant_user_to_response(self):
            """TenantUserをレスポンスにシリアライズできる"""
            # Arrange: TenantUserデータを準備
            data = {
                "id": "tenant_user_test",
                "tenant_id": "tenant_test",
                "user_id": "user_123",
                "assigned_at": datetime(2026, 2, 1, 10, 0, 0),
                "assigned_by": "user_admin"
            }
            
            # Act: TenantUserResponseを作成
            response = TenantUserResponse(**data)
            
            # Assert: 正しくシリアライズされる
            assert response.id == "tenant_user_test"
            assert response.tenant_id == "tenant_test"
            assert response.user_id == "user_123"

        def test_should_include_user_details_field(self):
            """user_detailsフィールドを含む"""
            # Arrange: user_details付きデータを準備
            data = {
                "id": "tenant_user_test",
                "tenant_id": "tenant_test",
                "user_id": "user_123",
                "user_details": {"username": "test.user", "email": "test@example.com"},
                "assigned_at": datetime(2026, 2, 1, 10, 0, 0),
                "assigned_by": "user_admin"
            }
            
            # Act: TenantUserResponseを作成
            response = TenantUserResponse(**data)
            
            # Assert: user_detailsが含まれる
            assert response.user_details is not None
            assert response.user_details["username"] == "test.user"

        def test_should_handle_none_user_details(self):
            """user_detailsがNoneの場合も適切に処理する"""
            # Arrange: user_details=Noneのデータを準備
            data = {
                "id": "tenant_user_test",
                "tenant_id": "tenant_test",
                "user_id": "user_123",
                "user_details": None,
                "assigned_at": datetime(2026, 2, 1, 10, 0, 0),
                "assigned_by": "user_admin"
            }
            
            # Act: TenantUserResponseを作成
            response = TenantUserResponse(**data)
            
            # Assert: Noneが許可される
            assert response.user_details is None


class TestTenantUserListResponse:
    """TenantUserListResponseスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_serialize_list_with_pagination(self):
            """ユーザー一覧とページネーション情報を含む"""
            # Arrange: データとページネーション情報を準備
            users = [
                TenantUserResponse(
                    id="tenant_user_test",
                    tenant_id="tenant_test",
                    user_id="user_123",
                    assigned_at=datetime(2026, 2, 1, 10, 0, 0),
                    assigned_by="user_admin"
                )
            ]
            pagination = {"skip": 0, "limit": 10, "total": 1}
            
            # Act: TenantUserListResponseを作成
            response = TenantUserListResponse(data=users, pagination=pagination)
            
            # Assert: dataとpaginationが含まれる
            assert len(response.data) == 1
            assert response.pagination["total"] == 1

        def test_should_handle_empty_list(self):
            """空のリストを適切に処理する"""
            # Arrange: 空のdataを準備
            pagination = {"skip": 0, "limit": 10, "total": 0}
            
            # Act: TenantUserListResponseを作成
            response = TenantUserListResponse(data=[], pagination=pagination)
            
            # Assert: 空配列が許可される
            assert len(response.data) == 0
            assert response.pagination["total"] == 0

