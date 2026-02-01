"""テナントリポジトリ"""
from typing import Optional, List
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.tenant import Tenant
import logging

logger = logging.getLogger(__name__)


class TenantRepository:
    """テナントデータアクセス層"""

    def __init__(self, container):
        self.container = container
        self.logger = logger

    async def create(self, tenant: Tenant) -> Tenant:
        """テナント作成"""
        try:
            tenant_dict = tenant.model_dump(by_alias=True)
            created = await self.container.create_item(body=tenant_dict)
            return Tenant(**created)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create tenant: {e}")
            raise

    async def get(self, tenant_id: str, partition_key: str) -> Optional[Tenant]:
        """テナント取得"""
        try:
            item = await self.container.read_item(item=tenant_id, partition_key=partition_key)
            return Tenant(**item)
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                return None
            self.logger.error(f"Failed to get tenant: {e}")
            raise

    async def update(self, tenant_id: str, partition_key: str, data: dict) -> Tenant:
        """テナント更新"""
        try:
            # 既存テナント取得
            existing = await self.get(tenant_id, partition_key)
            if not existing:
                raise ValueError(f"Tenant {tenant_id} not found")

            # データマージ
            updated_data = existing.model_dump(by_alias=True)
            for key, value in data.items():
                if value is not None:
                    updated_data[key] = value

            # 更新日時を設定
            from datetime import datetime
            updated_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

            # 保存
            updated = await self.container.upsert_item(body=updated_data)
            return Tenant(**updated)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to update tenant: {e}")
            raise

    async def delete(self, tenant_id: str, partition_key: str) -> None:
        """テナント削除（物理削除 - Phase 1）"""
        try:
            await self.container.delete_item(item=tenant_id, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to delete tenant: {e}")
            raise

    async def find_by_name(self, name: str) -> Optional[Tenant]:
        """
        テナント名でテナントを検索（アクティブなテナントのみ）
        
        Note: 一意性チェック用にクロスパーティションクエリを使用
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.type = 'tenant' 
                  AND c.name = @name 
                  AND c.status = 'active'
            """
            parameters = [{"name": "@name", "value": name}]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )

            async for item in items:
                return Tenant(**item)

            return None
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to find tenant by name: {e}")
            raise

    async def list_all(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[Tenant]:
        """
        全テナント一覧取得（特権テナント用、クロスパーティションクエリ）
        
        Args:
            status: ステータスフィルタ（active/suspended/deleted）
            skip: スキップ件数
            limit: 取得件数
        
        Returns:
            テナント一覧
        """
        try:
            if status:
                query = """
                    SELECT * FROM c 
                    WHERE c.type = 'tenant' 
                      AND c.status = @status
                    ORDER BY c.createdAt DESC
                    OFFSET @skip LIMIT @limit
                """
                parameters = [
                    {"name": "@status", "value": status},
                    {"name": "@skip", "value": skip},
                    {"name": "@limit", "value": limit},
                ]
            else:
                query = """
                    SELECT * FROM c 
                    WHERE c.type = 'tenant'
                    ORDER BY c.createdAt DESC
                    OFFSET @skip LIMIT @limit
                """
                parameters = [
                    {"name": "@skip", "value": skip},
                    {"name": "@limit", "value": limit},
                ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )

            tenants = []
            async for item in items:
                tenants.append(Tenant(**item))

            return tenants
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list tenants: {e}")
            raise

    async def list_by_tenant_id(
        self, tenant_id: str, status: Optional[str] = None
    ) -> List[Tenant]:
        """
        テナントID指定で一覧取得（一般テナント用、単一パーティションクエリ）
        
        Args:
            tenant_id: テナントID
            status: ステータスフィルタ
        
        Returns:
            テナント一覧（通常は1件のみ）
        """
        try:
            if status:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenantId = @tenant_id 
                      AND c.type = 'tenant'
                      AND c.status = @status
                """
                parameters = [
                    {"name": "@tenant_id", "value": tenant_id},
                    {"name": "@status", "value": status},
                ]
            else:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenantId = @tenant_id 
                      AND c.type = 'tenant'
                """
                parameters = [
                    {"name": "@tenant_id", "value": tenant_id},
                ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id,
            )

            tenants = []
            async for item in items:
                tenants.append(Tenant(**item))

            return tenants
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list tenants by tenant_id: {e}")
            raise
