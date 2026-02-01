"""テナントユーザーリポジトリのテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.tenant_user import TenantUser
from app.repositories.tenant_user_repository import TenantUserRepository


@pytest.fixture
def mock_container():
    """モックCosmosコンテナ"""
    mock = MagicMock()
    # createメソッドのモック (async)
    mock.create_item = AsyncMock()
    # readメソッドのモック (async)
    mock.read_item = AsyncMock()
    # deleteメソッドのモック (async)
    mock.delete_item = AsyncMock()
    # queryメソッドのモック
    mock.query_items = MagicMock()
    return mock


@pytest.fixture
def tenant_user_repository(mock_container):
    """TenantUserRepositoryインスタンス"""
    return TenantUserRepository(mock_container)


class TestTenantUserRepository:
    """TenantUserRepositoryのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_create_tenant_user(self, tenant_user_repository, mock_container, sample_tenant_user):
            """TenantUserを作成できる"""
            # Arrange: モックの戻り値を設定
            mock_container.create_item.return_value = sample_tenant_user.model_dump(by_alias=True)
            
            # Act: TenantUserを作成
            result = await tenant_user_repository.create(sample_tenant_user)
            
            # Assert: 正しく作成される
            assert result.id == sample_tenant_user.id
            assert result.tenant_id == sample_tenant_user.tenant_id
            assert result.user_id == sample_tenant_user.user_id
            mock_container.create_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_get_tenant_user_by_id(self, tenant_user_repository, mock_container, sample_tenant_user):
            """IDでTenantUserを取得できる"""
            # Arrange: モックの戻り値を設定
            mock_container.read_item.return_value = sample_tenant_user.model_dump(by_alias=True)
            
            # Act: TenantUserを取得
            result = await tenant_user_repository.get(sample_tenant_user.id, sample_tenant_user.tenant_id)
            
            # Assert: 正しく取得される
            assert result is not None
            assert result.id == sample_tenant_user.id
            assert result.user_id == sample_tenant_user.user_id
            mock_container.read_item.assert_called_once_with(
                item=sample_tenant_user.id,
                partition_key=sample_tenant_user.tenant_id
            )

        @pytest.mark.asyncio
        async def test_should_return_none_when_tenant_user_not_found(self, tenant_user_repository, mock_container):
            """存在しないTenantUserの取得時にNoneを返す"""
            # Arrange: CosmosHttpResponseErrorをスロー
            mock_container.read_item.side_effect = CosmosHttpResponseError(status_code=404, message="Not found")
            
            # Act: TenantUserを取得
            result = await tenant_user_repository.get("nonexistent_id", "tenant_test")
            
            # Assert: Noneが返る
            assert result is None

        @pytest.mark.asyncio
        async def test_should_delete_tenant_user(self, tenant_user_repository, mock_container):
            """TenantUserを物理削除できる"""
            # Arrange: モックの戻り値を設定
            mock_container.delete_item.return_value = None
            tenant_user_id = "tenant_user_test_123"
            tenant_id = "tenant_test"
            
            # Act: TenantUserを削除
            await tenant_user_repository.delete(tenant_user_id, tenant_id)
            
            # Assert: 正しく削除される
            mock_container.delete_item.assert_called_once_with(
                item=tenant_user_id,
                partition_key=tenant_id
            )

        @pytest.mark.asyncio
        async def test_should_find_tenant_user_by_user_id(self, tenant_user_repository, mock_container, sample_tenant_user):
            """ユーザーIDでTenantUserを検索できる"""
            # Arrange: モックの戻り値を設定
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([sample_tenant_user.model_dump(by_alias=True)])
            
            # Act: TenantUserを検索
            result = await tenant_user_repository.find_by_user(sample_tenant_user.tenant_id, sample_tenant_user.user_id)
            
            # Assert: 正しく検索される
            assert result is not None
            assert result.user_id == sample_tenant_user.user_id
            assert result.tenant_id == sample_tenant_user.tenant_id

        @pytest.mark.asyncio
        async def test_should_return_none_when_no_duplicate_found(self, tenant_user_repository, mock_container):
            """重複がない場合にNoneを返す"""
            # Arrange: 空の結果を返すモック
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([])
            
            # Act: TenantUserを検索
            result = await tenant_user_repository.find_by_user("tenant_test", "nonexistent_user")
            
            # Assert: Noneが返る
            assert result is None

        @pytest.mark.asyncio
        async def test_should_list_tenant_users_by_tenant(self, tenant_user_repository, mock_container, sample_tenant_user):
            """テナント所属ユーザー一覧を取得できる"""
            # Arrange: モックの戻り値を設定
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([sample_tenant_user.model_dump(by_alias=True)])
            
            # Act: ユーザー一覧を取得
            results = await tenant_user_repository.list_by_tenant("tenant_test", skip=0, limit=20)
            
            # Assert: 正しく取得される
            assert len(results) == 1
            assert results[0].user_id == sample_tenant_user.user_id

        @pytest.mark.asyncio
        async def test_should_count_tenant_users(self, tenant_user_repository, mock_container):
            """テナント所属ユーザー数をカウントできる"""
            # Arrange: モックの戻り値を設定（3件）
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([3])
            
            # Act: ユーザー数をカウント
            count = await tenant_user_repository.count_by_tenant("tenant_test")
            
            # Assert: 3が返る
            assert count == 3

    class Test境界値:
        """境界値テスト"""

        @pytest.mark.asyncio
        async def test_should_paginate_tenant_users(self, tenant_user_repository, mock_container):
            """ページネーションが正しく機能する"""
            # Arrange: モックの戻り値を設定
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([])
            
            # Act: skip=10, limit=20で取得
            results = await tenant_user_repository.list_by_tenant("tenant_test", skip=10, limit=20)
            
            # Assert: クエリパラメータが正しい
            assert results == []
            # query_itemsが正しいパラメータで呼ばれたことを確認
            mock_container.query_items.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_return_empty_list_when_no_users(self, tenant_user_repository, mock_container):
            """ユーザーがいない場合に空配列を返す"""
            # Arrange: 空の結果を返すモック
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([])
            
            # Act: ユーザー一覧を取得
            results = await tenant_user_repository.list_by_tenant("tenant_test")
            
            # Assert: 空配列が返る
            assert results == []

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_handle_cosmos_error_on_create(self, tenant_user_repository, mock_container, sample_tenant_user):
            """作成時のCosmosエラーを適切に処理する"""
            # Arrange: CosmosHttpResponseErrorをスロー
            mock_container.create_item.side_effect = CosmosHttpResponseError(status_code=500, message="Internal error")
            
            # Act & Assert: 例外が発生
            with pytest.raises(CosmosHttpResponseError) as exc_info:
                await tenant_user_repository.create(sample_tenant_user)
            assert exc_info.value.status_code == 500

        @pytest.mark.asyncio
        async def test_should_handle_cosmos_error_on_delete(self, tenant_user_repository, mock_container):
            """削除時のCosmosエラーを適切に処理する"""
            # Arrange: CosmosHttpResponseErrorをスロー（404以外）
            mock_container.delete_item.side_effect = CosmosHttpResponseError(status_code=500, message="Internal error")
            
            # Act & Assert: 例外が発生
            with pytest.raises(CosmosHttpResponseError) as exc_info:
                await tenant_user_repository.delete("test_id", "tenant_test")
            assert exc_info.value.status_code == 500

