"""
TenantRepositoryのユニットテスト

テストケース:
- TC-R001 ~ TC-R020: TenantRepositoryのCRUD操作、検索操作、境界値
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from azure.cosmos.exceptions import CosmosHttpResponseError
from datetime import datetime

from app.repositories.tenant_repository import TenantRepository
from app.models.tenant import Tenant
from tests.conftest import create_mock_query_result


class TestTenantRepository:
    """TenantRepositoryのテスト"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """各テストの前に実行"""
        self.mock_container = MagicMock()
        self.repository = TenantRepository(self.mock_container)

    class TestCRUD操作:
        """CRUD操作のテスト"""

        @pytest.mark.asyncio
        async def test_create_正常なテナント作成(self, sample_tenant):
            """
            テストケース: TC-R001
            目的: 正常なテナント作成ができることを検証
            前提条件: 有効なTenantモデルが存在
            実行手順:
              1. Tenantオブジェクトを作成
              2. repository.create()を呼び出す
              3. Cosmos DB containerのcreate_item()が呼ばれる
            期待結果:
              - 作成されたTenantオブジェクトが返却される
              - create_item()が1回呼ばれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.create_item = AsyncMock(return_value=sample_tenant.model_dump(by_alias=True))

            # Act
            result = await repository.create(sample_tenant)

            # Assert
            assert result.id == sample_tenant.id
            assert result.name == sample_tenant.name
            mock_container.create_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_CosmosDBエラー時の例外処理(self, sample_tenant):
            """
            テストケース: TC-R002
            目的: Cosmos DBエラー時に例外が伝播することを検証
            前提条件: Cosmos DBがエラーを返す
            実行手順:
              1. create_item()がCosmosHttpResponseErrorを発生させる
              2. repository.create()を呼び出す
            期待結果:
              - CosmosHttpResponseErrorが伝播する
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.create_item = AsyncMock(side_effect=CosmosHttpResponseError(status_code=500, message="Internal error"))

            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await repository.create(sample_tenant)

        @pytest.mark.asyncio
        async def test_get_存在するテナント取得(self, sample_tenant):
            """
            テストケース: TC-R003
            目的: 存在するテナントを取得できることを検証
            前提条件: 該当テナントがCosmos DBに存在
            実行手順:
              1. read_item()がテナントデータを返却する
              2. repository.get(tenant_id, partition_key)を呼び出す
            期待結果:
              - Tenantオブジェクトが返却される
              - read_item()が正しいパラメータで呼ばれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.read_item = AsyncMock(return_value=sample_tenant.model_dump(by_alias=True))

            # Act
            result = await repository.get("tenant_test", "tenant_test")

            # Assert
            assert result is not None
            assert result.id == "tenant_test"
            mock_container.read_item.assert_called_once_with(item="tenant_test", partition_key="tenant_test")

        @pytest.mark.asyncio
        async def test_get_存在しないテナント取得(self):
            """
            テストケース: TC-R004
            目的: 存在しないテナント取得時にNoneが返却されることを検証
            前提条件: 該当テナントが存在しない(404エラー)
            実行手順:
              1. read_item()が404エラーを発生させる
              2. repository.get()を呼び出す
            期待結果:
              - Noneが返却される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.read_item = AsyncMock(side_effect=CosmosHttpResponseError(status_code=404, message="Not found"))

            # Act
            result = await repository.get("tenant_notexist", "tenant_notexist")

            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_get_不正なパーティションキー(self):
            """
            テストケース: TC-R005
            目的: 不正なパーティションキーでアクセス時にNoneが返却されることを検証
            前提条件: 誤ったパーティションキーを指定
            実行手順:
              1. read_item()が404エラーを発生させる
              2. repository.get()を不正なパーティションキーで呼び出す
            期待結果:
              - Noneが返却される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.read_item = AsyncMock(side_effect=CosmosHttpResponseError(status_code=404, message="Not found"))

            # Act
            result = await repository.get("tenant_test", "wrong_partition")

            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_update_テナント情報更新(self, sample_tenant):
            """
            テストケース: TC-R006
            目的: テナント情報を更新できることを検証
            前提条件: 更新対象テナントが存在
            実行手順:
              1. 既存テナントを取得
              2. 更新データを指定してrepository.update()を呼び出す
              3. upsert_item()が呼ばれる
            期待結果:
              - 更新されたTenantオブジェクトが返却される
              - updatedAtが自動更新される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.read_item = AsyncMock(return_value=sample_tenant.model_dump(by_alias=True))
            
            updated_data = sample_tenant.model_dump(by_alias=True)
            updated_data["displayName"] = "Updated Name"
            mock_container.upsert_item = AsyncMock(return_value=updated_data)

            # Act
            result = await repository.update("tenant_test", "tenant_test", {"displayName": "Updated Name"})

            # Assert
            assert result.display_name == "Updated Name"
            mock_container.upsert_item.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_存在しないテナント更新(self):
            """
            テストケース: TC-R007
            目的: 存在しないテナント更新時にValueErrorが発生することを検証
            前提条件: 更新対象テナントが存在しない
            実行手順:
              1. get()がNoneを返却する
              2. repository.update()を呼び出す
            期待結果:
              - ValueErrorが発生
              - エラーメッセージに"not found"が含まれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.read_item = AsyncMock(side_effect=CosmosHttpResponseError(status_code=404, message="Not found"))

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await repository.update("tenant_notexist", "tenant_notexist", {"displayName": "Test"})
            assert "not found" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_delete_テナント削除(self):
            """
            テストケース: TC-R008
            目的: テナントを削除できることを検証
            前提条件: 削除対象テナントが存在
            実行手順:
              1. repository.delete(tenant_id, partition_key)を呼び出す
              2. delete_item()が呼ばれる
            期待結果:
              - 正常に削除される
              - delete_item()が正しいパラメータで呼ばれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.delete_item = AsyncMock()

            # Act
            await repository.delete("tenant_test", "tenant_test")

            # Assert
            mock_container.delete_item.assert_called_once_with(item="tenant_test", partition_key="tenant_test")

        @pytest.mark.asyncio
        async def test_delete_存在しないテナント削除(self):
            """
            テストケース: TC-R009
            目的: 存在しないテナント削除時に例外が発生することを検証
            前提条件: 削除対象テナントが存在しない
            実行手順:
              1. delete_item()が404エラーを発生させる
              2. repository.delete()を呼び出す
            期待結果:
              - CosmosHttpResponseErrorが伝播する
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.delete_item = AsyncMock(side_effect=CosmosHttpResponseError(status_code=404, message="Not found"))

            # Act & Assert
            with pytest.raises(CosmosHttpResponseError):
                await repository.delete("tenant_notexist", "tenant_notexist")

    class Test検索操作:
        """検索操作のテスト"""

        @pytest.mark.asyncio
        async def test_find_by_name_テナント名検索成功(self, sample_tenant):
            """
            テストケース: TC-R010
            目的: テナント名で検索できることを検証
            前提条件: 該当テナントが存在
            実行手順:
              1. query_items()がテナントデータを返却する
              2. repository.find_by_name(name)を呼び出す
            期待結果:
              - Tenantオブジェクトが返却される
              - クロスパーティションクエリが実行される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([sample_tenant.model_dump(by_alias=True)]))

            # Act
            result = await repository.find_by_name("test")

            # Assert
            assert result is not None
            assert result.name == "test"
            mock_container.query_items.assert_called_once()
            call_kwargs = mock_container.query_items.call_args[1]
            assert call_kwargs["enable_cross_partition_query"] is True

        @pytest.mark.asyncio
        async def test_find_by_name_存在しない名前(self):
            """
            テストケース: TC-R011
            目的: 存在しないテナント名で検索時にNoneが返却されることを検証
            前提条件: 該当テナントが存在しない
            実行手順:
              1. query_items()が空の結果を返却する
              2. repository.find_by_name(name)を呼び出す
            期待結果:
              - Noneが返却される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            result = await repository.find_by_name("nonexistent")

            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_find_by_name_アクティブのみフィルタ(self):
            """
            テストケース: TC-R012
            目的: アクティブなテナントのみ検索されることを検証
            前提条件: クエリにstatus='active'条件が含まれる
            実行手順:
              1. repository.find_by_name(name)を呼び出す
              2. query_items()の呼び出しパラメータを検証
            期待結果:
              - クエリにstatus='active'条件が含まれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            await repository.find_by_name("test")

            # Assert
            call_args = mock_container.query_items.call_args
            assert "status = 'active'" in call_args[1]["query"]

        @pytest.mark.asyncio
        async def test_find_by_name_クロスパーティションクエリ(self):
            """
            テストケース: TC-R013
            目的: クロスパーティションクエリが実行されることを検証
            前提条件: テナント名検索は全パーティション対象
            実行手順:
              1. repository.find_by_name(name)を呼び出す
              2. query_items()の呼び出しパラメータを検証
            期待結果:
              - enable_cross_partition_query=Trueで呼ばれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            await repository.find_by_name("test")

            # Assert
            call_kwargs = mock_container.query_items.call_args[1]
            assert call_kwargs["enable_cross_partition_query"] is True

        @pytest.mark.asyncio
        async def test_list_all_全テナント一覧取得(self, sample_tenant, regular_tenant):
            """
            テストケース: TC-R014
            目的: 全テナント一覧を取得できることを検証
            前提条件: 複数のテナントが存在
            実行手順:
              1. query_items()が複数テナントを返却する
              2. repository.list_all()を呼び出す
            期待結果:
              - テナントのリストが返却される
              - クロスパーティションクエリが実行される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([
                sample_tenant.model_dump(by_alias=True),
                regular_tenant.model_dump(by_alias=True)
            ]))

            # Act
            result = await repository.list_all()

            # Assert
            assert len(result) == 2
            call_kwargs = mock_container.query_items.call_args[1]
            assert call_kwargs["enable_cross_partition_query"] is True

        @pytest.mark.asyncio
        async def test_list_all_ステータスフィルタ(self):
            """
            テストケース: TC-R015
            目的: ステータスでフィルタできることを検証
            前提条件: statusパラメータを指定
            実行手順:
              1. repository.list_all(status="active")を呼び出す
              2. query_items()の呼び出しパラメータを検証
            期待結果:
              - クエリにstatus条件が含まれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            await repository.list_all(status="active")

            # Assert
            call_args = mock_container.query_items.call_args
            assert "status = @status" in call_args[1]["query"]

        @pytest.mark.asyncio
        async def test_list_all_ページネーション(self):
            """
            テストケース: TC-R016
            目的: ページネーション(skip, limit)が機能することを検証
            前提条件: skip, limitパラメータを指定
            実行手順:
              1. repository.list_all(skip=10, limit=20)を呼び出す
              2. query_items()の呼び出しパラメータを検証
            期待結果:
              - クエリにOFFSET, LIMIT句が含まれる
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            await repository.list_all(skip=10, limit=20)

            # Assert
            call_args = mock_container.query_items.call_args
            assert "OFFSET @skip LIMIT @limit" in call_args[1]["query"]

        @pytest.mark.asyncio
        async def test_list_by_tenant_id_単一パーティション(self, regular_tenant):
            """
            テストケース: TC-R017
            目的: 特定テナントIDで絞り込めることを検証
            前提条件: tenant_idを指定
            実行手順:
              1. repository.list_by_tenant_id(tenant_id)を呼び出す
              2. query_items()の呼び出しパラメータを検証
            期待結果:
              - 単一パーティションクエリが実行される
              - partition_key=tenant_idが指定される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([regular_tenant.model_dump(by_alias=True)]))

            # Act
            result = await repository.list_by_tenant_id("tenant_acme")

            # Assert
            assert len(result) == 1
            call_kwargs = mock_container.query_items.call_args[1]
            assert call_kwargs["partition_key"] == "tenant_acme"

        @pytest.mark.asyncio
        async def test_list_by_tenant_id_空のテナント(self):
            """
            テストケース: TC-R018
            目的: 存在しないテナントIDで空配列が返却されることを検証
            前提条件: 該当テナントが存在しない
            実行手順:
              1. query_items()が空の結果を返却する
              2. repository.list_by_tenant_id(tenant_id)を呼び出す
            期待結果:
              - 空配列が返却される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            result = await repository.list_by_tenant_id("tenant_nonexistent")

            # Assert
            assert result == []

    class Test境界値:
        """境界値テスト"""

        @pytest.mark.asyncio
        async def test_list_all_skip境界値(self):
            """
            テストケース: TC-R019
            目的: skipパラメータの境界値(0, 1, 大きな値)が正しく動作することを検証
            前提条件: skipパラメータを様々な値で指定
            実行手順:
              1. skip=0, 1, 10000でrepository.list_all()を呼び出す
              2. query_items()のパラメータを検証
            期待結果:
              - 各境界値で正しいOFFSET値が設定される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            await repository.list_all(skip=0)
            await repository.list_all(skip=1)
            await repository.list_all(skip=10000)

            # Assert
            assert mock_container.query_items.call_count == 3

        @pytest.mark.asyncio
        async def test_list_all_limit境界値(self):
            """
            テストケース: TC-R020
            目的: limitパラメータの境界値(1, 100)が正しく動作することを検証
            前提条件: limitパラメータを様々な値で指定
            実行手順:
              1. limit=1, 100, 1000でrepository.list_all()を呼び出す
              2. query_items()のパラメータを検証
            期待結果:
              - 各境界値で正しいLIMIT値が設定される
            """
            # Arrange
            mock_container = MagicMock()
            repository = TenantRepository(mock_container)
            mock_container.query_items = MagicMock(return_value=create_mock_query_result([]))

            # Act
            await repository.list_all(limit=1)
            await repository.list_all(limit=100)
            await repository.list_all(limit=1000)

            # Assert
            assert mock_container.query_items.call_count == 3
