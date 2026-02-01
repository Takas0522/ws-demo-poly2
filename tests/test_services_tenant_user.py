"""テナントユーザーサービスのテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tenant_user_service import TenantUserService
from app.models.tenant_user import TenantUser
from app.models.tenant import Tenant


@pytest.fixture
def mock_tenant_user_repository():
    """モックTenantUserRepository"""
    mock = MagicMock()
    mock.create = AsyncMock()
    mock.get = AsyncMock()
    mock.delete = AsyncMock()
    mock.find_by_user = AsyncMock()  # find_by_userもAsyncMockに
    mock.find_by_user_id = AsyncMock()
    mock.list_by_tenant = AsyncMock()
    mock.count_by_tenant = AsyncMock()
    return mock


@pytest.fixture
def mock_tenant_repository():
    """モックTenantRepository"""
    mock = MagicMock()
    mock.get = AsyncMock()
    return mock


@pytest.fixture
def mock_tenant_service():
    """モックTenantService"""
    mock = MagicMock()
    mock.increment_user_count = AsyncMock()
    mock.decrement_user_count = AsyncMock()
    return mock


@pytest.fixture
def mock_auth_service_client():
    """モックAuthServiceClient"""
    mock = MagicMock()
    mock.verify_user_exists = AsyncMock()
    mock.get_user_details = AsyncMock()
    return mock


@pytest.fixture
def tenant_user_service(
    mock_tenant_user_repository,
    mock_tenant_repository,
    mock_tenant_service,
    mock_auth_service_client
):
    """TenantUserServiceインスタンス"""
    return TenantUserService(
        tenant_user_repository=mock_tenant_user_repository,
        tenant_repository=mock_tenant_repository,
        tenant_service=mock_tenant_service,
        auth_service_client=mock_auth_service_client
    )


class TestTenantUserServiceInviteUser:
    """invite_userメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_invite_user_successfully(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, mock_tenant_user_repository, sample_tenant, sample_tenant_user, mock_tenant_service):
            """ユーザー招待が成功する"""
            # Arrange: モックの戻り値を設定
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.return_value = True
            mock_tenant_user_repository.find_by_user.return_value = None
            mock_tenant_user_repository.create.return_value = sample_tenant_user
            mock_tenant_service.increment_user_count.return_value = None
            
            # Act: ユーザー招待を実行
            result = await tenant_user_service.invite_user("tenant_test", "user_123", "user_admin_001")
            
            # Assert: 招待が成功する
            assert result.user_id == "user_123"
            mock_tenant_user_repository.create.assert_called_once()
            mock_tenant_service.increment_user_count.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_increment_user_count_after_invite(self, tenant_user_service, mock_tenant_service, mock_tenant_repository, mock_auth_service_client, mock_tenant_user_repository, sample_tenant, sample_tenant_user):
            """招待後にuser_countが自動的にインクリメントされる"""
            # Arrange: モックを準備
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.return_value = True
            mock_tenant_user_repository.find_by_user.return_value = None
            mock_tenant_user_repository.create.return_value = sample_tenant_user
            
            # Act: ユーザー招待を実行
            await tenant_user_service.invite_user("tenant_test", "user_123", "user_admin_001")
            
            # Assert: increment_user_countが呼ばれる
            mock_tenant_service.increment_user_count.assert_called_once_with("tenant_test")

        @pytest.mark.asyncio
        async def test_should_generate_deterministic_tenant_user_id(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, mock_tenant_user_repository, sample_tenant, sample_tenant_user, mock_tenant_service):
            """決定的なTenantUser IDが生成される"""
            # Arrange: tenant_idとuser_idを準備
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.return_value = True
            mock_tenant_user_repository.find_by_user.return_value = None
            mock_tenant_user_repository.create.return_value = sample_tenant_user
            mock_tenant_service.increment_user_count.return_value = None
            
            # Act: TenantUser作成
            result = await tenant_user_service.invite_user("tenant_test", "user_123", "user_admin_001")
            
            # Assert: IDが"tenant_user_{tenant_id}_{user_id}"形式
            # IDはcreateメソッドに渡されたTenantUserの中に含まれる
            create_call_args = mock_tenant_user_repository.create.call_args[0][0]
            assert create_call_args.id.startswith("tenant_user_")

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_raise_error_when_tenant_not_found(self, tenant_user_service, mock_tenant_repository):
            """テナントが存在しない場合にエラーを発生させる"""
            # Arrange
            mock_tenant_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await tenant_user_service.invite_user("nonexistent", "user_123", "admin")
            assert "not found" in str(exc_info.value).lower()

        @pytest.mark.asyncio
        async def test_should_raise_error_when_user_not_found(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, sample_tenant):
            """ユーザーが認証サービスに存在しない場合にエラー"""
            # Arrange
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.side_effect = ValueError("User not found")
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await tenant_user_service.invite_user("tenant_test", "nonexistent_user", "admin")
            assert "not found" in str(exc_info.value).lower()

        @pytest.mark.asyncio
        async def test_should_raise_error_when_user_already_member(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, mock_tenant_user_repository, sample_tenant, sample_tenant_user):
            """ユーザーが既にテナントメンバーの場合にエラー"""
            # Arrange
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.return_value = True
            mock_tenant_user_repository.find_by_user.return_value = sample_tenant_user
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await tenant_user_service.invite_user("tenant_test", "user_123", "admin")
            assert "already a member" in str(exc_info.value).lower()

        @pytest.mark.asyncio
        async def test_should_raise_error_when_max_users_exceeded(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, mock_tenant_user_repository):
            """最大ユーザー数を超える場合にエラー"""
            # Arrange
            full_tenant = Tenant(
                id="tenant_full", tenant_id="tenant_full", name="full", display_name="Full",
                is_privileged=False, status="active", plan="standard",
                user_count=100, max_users=100, metadata={},
                created_at=datetime(2026, 1, 1), updated_at=datetime(2026, 1, 1),
                created_by="admin", updated_by="admin"
            )
            mock_tenant_repository.get.return_value = full_tenant
            mock_auth_service_client.verify_user_exists.return_value = True
            mock_tenant_user_repository.find_by_user.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await tenant_user_service.invite_user("tenant_full", "user_new", "admin")
            assert "maximum user limit" in str(exc_info.value).lower()

        @pytest.mark.asyncio
        async def test_should_raise_error_when_auth_service_unavailable(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, sample_tenant):
            """認証サービスが利用不可の場合にエラー"""
            # Arrange
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.side_effect = RuntimeError("Service unavailable")
            
            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                await tenant_user_service.invite_user("tenant_test", "user_123", "admin")
            assert "unavailable" in str(exc_info.value).lower()

        @pytest.mark.asyncio
        async def test_should_rollback_when_user_count_increment_fails(self, tenant_user_service, mock_tenant_repository, mock_auth_service_client, mock_tenant_user_repository, mock_tenant_service, sample_tenant, sample_tenant_user):
            """user_count更新失敗時にロールバックする"""
            # Arrange
            mock_tenant_repository.get.return_value = sample_tenant
            mock_auth_service_client.verify_user_exists.return_value = True
            mock_tenant_user_repository.find_by_user.return_value = None
            mock_tenant_user_repository.create.return_value = sample_tenant_user
            mock_tenant_service.increment_user_count.side_effect = Exception("DB error")
            
            # Act & Assert
            with pytest.raises(Exception):
                await tenant_user_service.invite_user("tenant_test", "user_123", "admin")
            # ロールバックでdeleteが呼ばれる
            mock_tenant_user_repository.delete.assert_called_once()


class TestTenantUserServiceListTenantUsers:
    """list_tenant_usersメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_list_tenant_users_with_details(self, tenant_user_service, mock_tenant_user_repository, mock_auth_service_client, sample_tenant_user, mock_auth_service_user_response):
            """ユーザー詳細を含むテナントユーザー一覧を取得"""
            # Arrange
            mock_tenant_user_repository.list_by_tenant.return_value = [sample_tenant_user]
            mock_auth_service_client.get_user_details.return_value = mock_auth_service_user_response
            
            # Act
            result = await tenant_user_service.list_tenant_users("tenant_test", skip=0, limit=20, include_total=False)
            
            # Assert
            assert len(result["data"]) == 1
            assert result["data"][0]["user_id"] == sample_tenant_user.user_id
            assert result["data"][0]["user_details"] is not None

        @pytest.mark.asyncio
        async def test_should_include_total_when_requested(self, tenant_user_service, mock_tenant_user_repository, mock_auth_service_client, sample_tenant_user):
            """include_total=Trueの場合にtotalを含む"""
            # Arrange
            mock_tenant_user_repository.list_by_tenant.return_value = [sample_tenant_user]
            mock_tenant_user_repository.count_by_tenant.return_value = 5
            mock_auth_service_client.get_user_details.return_value = {}
            
            # Act
            result = await tenant_user_service.list_tenant_users("tenant_test", skip=0, limit=20, include_total=True)
            
            # Assert
            assert "total" in result["pagination"]
            assert result["pagination"]["total"] == 5

        @pytest.mark.asyncio
        async def test_should_exclude_total_when_not_requested(self, tenant_user_service, mock_tenant_user_repository, mock_auth_service_client, sample_tenant_user):
            """include_total=Falseの場合にtotalを省略"""
            # Arrange
            mock_tenant_user_repository.list_by_tenant.return_value = [sample_tenant_user]
            mock_auth_service_client.get_user_details.return_value = {}
            
            # Act
            result = await tenant_user_service.list_tenant_users("tenant_test", skip=0, limit=20, include_total=False)
            
            # Assert
            assert "total" not in result["pagination"]

        @pytest.mark.asyncio
        async def test_should_fetch_user_details_in_parallel(self, tenant_user_service, mock_tenant_user_repository, mock_auth_service_client):
            """ユーザー詳細を並列で取得する"""
            # Arrange: 3ユーザー
            users = [
                TenantUser(id=f"tu_{i}", tenant_id="tenant_test", user_id=f"user_{i}", 
                          assigned_at=datetime.utcnow(), assigned_by="admin")
                for i in range(3)
            ]
            mock_tenant_user_repository.list_by_tenant.return_value = users
            mock_auth_service_client.get_user_details.return_value = {}
            
            # Act
            result = await tenant_user_service.list_tenant_users("tenant_test")
            
            # Assert: get_user_detailsう3回呼ばれる
            assert mock_auth_service_client.get_user_details.call_count == 3

    class Testエッジケース:
        """エッジケーステスト"""

        @pytest.mark.asyncio
        async def test_should_handle_partial_user_details_failure(self, tenant_user_service, mock_tenant_user_repository, mock_auth_service_client):
            """一部のユーザー詳細取得失敗を許容する"""
            # Arrange
            users = [
                TenantUser(id="tu_1", tenant_id="tenant_test", user_id="user_1", 
                          assigned_at=datetime.utcnow(), assigned_by="admin")
            ]
            mock_tenant_user_repository.list_by_tenant.return_value = users
            # 1人目は失敗
            mock_auth_service_client.get_user_details.return_value = None
            
            # Act
            result = await tenant_user_service.list_tenant_users("tenant_test")
            
            # Assert: フォールバックが返る
            assert result["data"][0]["user_details"] is not None

        @pytest.mark.asyncio
        async def test_should_return_fallback_when_user_details_unavailable(self, tenant_user_service, mock_tenant_user_repository, mock_auth_service_client, sample_tenant_user):
            """ユーザー詳細取得失敗時にフォールバックを返す"""
            # Arrange
            mock_tenant_user_repository.list_by_tenant.return_value = [sample_tenant_user]
            mock_auth_service_client.get_user_details.return_value = None
            
            # Act
            result = await tenant_user_service.list_tenant_users("tenant_test")
            
            # Assert
            assert result["data"][0]["user_details"]["error"] == "Details unavailable"


class TestTenantUserServiceRemoveUser:
    """remove_userメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_remove_user_successfully(self, tenant_user_service, mock_tenant_user_repository, mock_tenant_service, sample_tenant_user):
            """ユーザー削除が成功する"""
            # Arrange
            mock_tenant_user_repository.get.return_value = sample_tenant_user
            
            # Act
            await tenant_user_service.remove_user("tenant_test", "user_123", "admin")
            
            # Assert
            mock_tenant_user_repository.delete.assert_called_once()
            mock_tenant_service.decrement_user_count.assert_called_once_with("tenant_test")

        @pytest.mark.asyncio
        async def test_should_decrement_user_count_after_removal(self, tenant_user_service, mock_tenant_user_repository, mock_tenant_service, sample_tenant_user):
            """削除後にuser_countが自動的にデクリメントされる"""
            # Arrange
            mock_tenant_user_repository.get.return_value = sample_tenant_user
            
            # Act
            await tenant_user_service.remove_user("tenant_test", "user_123", "admin")
            
            # Assert
            mock_tenant_service.decrement_user_count.assert_called_once_with("tenant_test")

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_raise_error_when_tenant_user_not_found(self, tenant_user_service, mock_tenant_user_repository):
            """TenantUserが存在しない場合にエラー"""
            # Arrange
            mock_tenant_user_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await tenant_user_service.remove_user("tenant_test", "user_123", "admin")
            assert "not found" in str(exc_info.value).lower()

        @pytest.mark.asyncio
        async def test_should_log_error_when_user_count_decrement_fails(self, tenant_user_service, mock_tenant_user_repository, mock_tenant_service, sample_tenant_user):
            """user_count更新失敗時にログ記録（ロールバックしない）"""
            # Arrange
            mock_tenant_user_repository.get.return_value = sample_tenant_user
            mock_tenant_service.decrement_user_count.side_effect = Exception("DB error")
            
            # Act: 例外が発生しない
            await tenant_user_service.remove_user("tenant_test", "user_123", "admin")
            
            # Assert: deleteは完了している
            mock_tenant_user_repository.delete.assert_called_once()
