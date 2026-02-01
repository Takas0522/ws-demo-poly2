"""ドメインリポジトリ"""
from typing import Optional, List
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.domain import Domain
import logging

logger = logging.getLogger(__name__)


class DomainRepository:
    """ドメインデータアクセス層"""

    def __init__(self, container):
        self.container = container
        self.logger = logger

    async def create(self, domain: Domain) -> Domain:
        """ドメイン作成"""
        try:
            domain_dict = domain.model_dump(by_alias=True)
            created = await self.container.create_item(body=domain_dict)
            return Domain(**created)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create domain: {e}")
            raise

    async def get(self, domain_id: str, partition_key: str) -> Optional[Domain]:
        """ドメイン取得"""
        try:
            item = await self.container.read_item(item=domain_id, partition_key=partition_key)
            return Domain(**item)
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                return None
            self.logger.error(f"Failed to get domain: {e}")
            raise

    async def update(self, domain_id: str, partition_key: str, data: dict) -> Domain:
        """ドメイン更新"""
        try:
            # 既存ドメイン取得
            existing = await self.get(domain_id, partition_key)
            if not existing:
                raise ValueError(f"Domain {domain_id} not found")

            # データマージ
            updated_data = existing.model_dump(by_alias=True)
            for key, value in data.items():
                if value is not None:
                    updated_data[key] = value

            # 保存
            updated = await self.container.upsert_item(body=updated_data)
            return Domain(**updated)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to update domain: {e}")
            raise

    async def delete(self, domain_id: str, partition_key: str) -> None:
        """ドメイン削除（物理削除）"""
        try:
            await self.container.delete_item(item=domain_id, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to delete domain: {e}")
            raise

    async def list_by_tenant(
        self, tenant_id: str, verified: Optional[bool] = None
    ) -> List[Domain]:
        """
        テナントのドメイン一覧取得
        
        Args:
            tenant_id: テナントID
            verified: 検証済みフィルタ（Noneの場合は全て）
        
        Returns:
            List[Domain]: ドメイン一覧
        """
        try:
            if verified is not None:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenantId = @tenant_id 
                      AND c.type = 'domain'
                      AND c.verified = @verified
                    ORDER BY c.createdAt DESC
                """
                parameters = [
                    {"name": "@tenant_id", "value": tenant_id},
                    {"name": "@verified", "value": verified}
                ]
            else:
                query = """
                    SELECT * FROM c 
                    WHERE c.tenantId = @tenant_id 
                      AND c.type = 'domain'
                    ORDER BY c.createdAt DESC
                """
                parameters = [
                    {"name": "@tenant_id", "value": tenant_id}
                ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id,
            )

            domains = []
            async for item in items:
                domains.append(Domain(**item))

            return domains
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list domains: {e}")
            raise
