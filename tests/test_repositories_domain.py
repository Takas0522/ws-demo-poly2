"""ドメインリポジトリのテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.domain import Domain
from app.repositories.domain_repository import DomainRepository


@pytest.fixture
def mock_container():
    """モックCosmosコンテナ"""
    mock = MagicMock()
    # createメソッドのモック (async)
    mock.create_item = AsyncMock()
    # readメソッドのモック (async)
    mock.read_item = AsyncMock()
    # replaceメソッドのモック (async)
    mock.replace_item = AsyncMock()
    # upsertメソッドのモック (async)
    mock.upsert_item = AsyncMock()
    # deleteメソッドのモック (async)
    mock.delete_item = AsyncMock()
    # queryメソッドのモック
    mock.query_items = MagicMock()
    return mock


@pytest.fixture
def domain_repository(mock_container):
    """DomainRepositoryインスタンス"""
    return DomainRepository(mock_container)


class TestDomainRepository:
    """DomainRepositoryのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_create_domain(self, domain_repository, mock_container, sample_domain):
            """Domainを作成できる"""
            # Arrange: モックの戻り値を設定
            mock_container.create_item.return_value = sample_domain.model_dump(by_alias=True)
            
            # Act: Domainを作成
            result = await domain_repository.create(sample_domain)
            
            # Assert: 正しく作成される
            assert result.id == sample_domain.id
            assert result.domain == sample_domain.domain
            assert result.verified == sample_domain.verified
            mock_container.create_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_get_domain_by_id(self, domain_repository, mock_container, sample_domain):
            """IDでDomainを取得できる"""
            # Arrange: モックの戻り値を設定
            mock_container.read_item.return_value = sample_domain.model_dump(by_alias=True)
            
            # Act: Domainを取得
            result = await domain_repository.get(sample_domain.id, sample_domain.tenant_id)
            
            # Assert: 正しく取得される
            assert result is not None
            assert result.id == sample_domain.id
            assert result.domain == sample_domain.domain
            mock_container.read_item.assert_called_once_with(
                item=sample_domain.id,
                partition_key=sample_domain.tenant_id
            )

        @pytest.mark.asyncio
        async def test_should_return_none_when_domain_not_found(self, domain_repository, mock_container):
            """存在しないDomainの取得時にNoneを返す"""
            # Arrange: CosmosHttpResponseErrorをスロー
            mock_container.read_item.side_effect = CosmosHttpResponseError(status_code=404, message="Not found")
            
            # Act: Domainを取得
            result = await domain_repository.get("nonexistent_id", "tenant_test")
            
            # Assert: Noneが返る
            assert result is None

        @pytest.mark.asyncio
        async def test_should_update_domain(self, domain_repository, mock_container, verified_domain):
            """Domainを更新できる"""
            # Arrange: モックの戻り値を設定
            mock_container.read_item.return_value = verified_domain.model_dump(by_alias=True)
            mock_container.upsert_item.return_value = verified_domain.model_dump(by_alias=True)
            
            # Act: Domainを更新
            update_data = {"verified": True}
            result = await domain_repository.update(verified_domain.id, verified_domain.tenant_id, update_data)
            
            # Assert: 正しく更新される
            assert result.verified == True
            mock_container.upsert_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_delete_domain(self, domain_repository, mock_container):
            """Domainを物理削除できる"""
            # Arrange: モックの戻り値を設定
            mock_container.delete_item.return_value = None
            domain_id = "domain_test_example_com"
            tenant_id = "tenant_test"
            
            # Act: Domainを削除
            await domain_repository.delete(domain_id, tenant_id)
            
            # Assert: 正しく削除される
            mock_container.delete_item.assert_called_once_with(
                item=domain_id,
                partition_key=tenant_id
            )

        @pytest.mark.asyncio
        async def test_should_list_all_domains_by_tenant(self, domain_repository, mock_container, sample_domain):
            """テナントの全Domainを取得できる"""
            # Arrange: モックの戻り値を設定
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([sample_domain.model_dump(by_alias=True)])
            
            # Act: Domain一覧を取得
            results = await domain_repository.list_by_tenant("tenant_test")
            
            # Assert: 正しく取得される
            assert len(results) == 1
            assert results[0].domain == sample_domain.domain

        @pytest.mark.asyncio
        async def test_should_list_verified_domains_only(self, domain_repository, mock_container, verified_domain):
            """検証済みDomainのみを取得できる"""
            # Arrange: モックの戻り値を設定
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([verified_domain.model_dump(by_alias=True)])
            
            # Act: 検証済みDomainを取得
            results = await domain_repository.list_by_tenant("tenant_test", verified=True)
            
            # Assert: verified=Trueのみが返る
            assert len(results) == 1
            assert results[0].verified == True

        @pytest.mark.asyncio
        async def test_should_list_unverified_domains_only(self, domain_repository, mock_container, sample_domain):
            """未検証Domainのみを取得できる"""
            # Arrange: モックの戻り値を設定
            from tests.conftest import create_mock_query_result
            mock_container.query_items.return_value = create_mock_query_result([sample_domain.model_dump(by_alias=True)])
            
            # Act: 未検証Domainを取得
            results = await domain_repository.list_by_tenant("tenant_test", verified=False)
            
            # Assert: verified=Falseのみが返る
            assert len(results) == 1
            assert results[0].verified == False

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_handle_cosmos_error_on_create(self, domain_repository, mock_container, sample_domain):
            """作成時のCosmosエラーを適切に処理する"""
            # Arrange: CosmosHttpResponseErrorをスロー
            mock_container.create_item.side_effect = CosmosHttpResponseError(status_code=500, message="Internal error")
            
            # Act & Assert: 例外が発生
            with pytest.raises(CosmosHttpResponseError) as exc_info:
                await domain_repository.create(sample_domain)
            assert exc_info.value.status_code == 500

        @pytest.mark.asyncio
        async def test_should_handle_cosmos_error_on_update(self, domain_repository, mock_container, verified_domain):
            """更新時のCosmosエラーを適切に処理すろ"""
            # Arrange: CosmosHttpResponseErrorをスロー
            mock_container.read_item.return_value = verified_domain.model_dump(by_alias=True)
            mock_container.upsert_item.side_effect = CosmosHttpResponseError(status_code=500, message="Internal error")
            
            # Act & Assert: 例外が発生
            with pytest.raises(CosmosHttpResponseError) as exc_info:
                await domain_repository.update(verified_domain.id, verified_domain.tenant_id, {"verified": True})
            assert exc_info.value.status_code == 500

        @pytest.mark.asyncio
        async def test_should_handle_cosmos_error_on_delete(self, domain_repository, mock_container):
            """削除時のCosmosエラーを適切に処理する"""
            # Arrange: CosmosHttpResponseErrorをスロー（404以外）
            mock_container.delete_item.side_effect = CosmosHttpResponseError(status_code=500, message="Internal error")
            
            # Act & Assert: 例外が発生
            with pytest.raises(CosmosHttpResponseError) as exc_info:
                await domain_repository.delete("test_id", "tenant_test")
            assert exc_info.value.status_code == 500

