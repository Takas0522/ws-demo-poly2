"""テナントユーザーリポジトリ"""
from typing import Optional, List
from azure.cosmos.exceptions import CosmosHttpResponseError
from app.models.tenant_user import TenantUser
import logging

logger = logging.getLogger(__name__)


class TenantUserRepository:
    """テナントユーザーデータアクセス層"""

    def __init__(self, container):
        self.container = container
        self.logger = logger

    async def create(self, tenant_user: TenantUser) -> TenantUser:
        """テナントユーザー作成"""
        try:
            tenant_user_dict = tenant_user.model_dump(by_alias=True)
            created = await self.container.create_item(body=tenant_user_dict)
            return TenantUser(**created)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to create tenant user: {e}")
            raise

    async def get(self, tenant_user_id: str, partition_key: str) -> Optional[TenantUser]:
        """テナントユーザー取得"""
        try:
            item = await self.container.read_item(item=tenant_user_id, partition_key=partition_key)
            return TenantUser(**item)
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                return None
            self.logger.error(f"Failed to get tenant user: {e}")
            raise

    async def delete(self, tenant_user_id: str, partition_key: str) -> None:
        """テナントユーザー削除（物理削除）"""
        try:
            await self.container.delete_item(item=tenant_user_id, partition_key=partition_key)
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to delete tenant user: {e}")
            raise

    async def find_by_user(self, tenant_id: str, user_id: str) -> Optional[TenantUser]:
        """
        ユーザーIDでテナントユーザーを検索（重複チェック用）
        
        Args:
            tenant_id: テナントID
            user_id: ユーザーID
        
        Returns:
            Optional[TenantUser]: 見つかった場合はTenantUser、見つからない場合はNone
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'tenant_user' 
                  AND c.userId = @user_id
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@user_id", "value": user_id}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id,
            )

            async for item in items:
                return TenantUser(**item)

            return None
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to find tenant user by user_id: {e}")
            raise

    async def list_by_tenant(
        self, tenant_id: str, skip: int = 0, limit: int = 20
    ) -> List[TenantUser]:
        """
        テナント所属ユーザー一覧取得
        
        Args:
            tenant_id: テナントID
            skip: スキップ件数
            limit: 取得件数
        
        Returns:
            List[TenantUser]: テナントユーザー一覧
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'tenant_user'
                ORDER BY c.assignedAt DESC
                OFFSET @skip LIMIT @limit
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@skip", "value": skip},
                {"name": "@limit", "value": limit}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id,
            )

            tenant_users = []
            async for item in items:
                tenant_users.append(TenantUser(**item))

            return tenant_users
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to list tenant users: {e}")
            raise

    async def count_by_tenant(self, tenant_id: str) -> int:
        """
        テナント所属ユーザー数を取得
        
        Args:
            tenant_id: テナントID
        
        Returns:
            int: ユーザー数
        """
        try:
            query = """
                SELECT VALUE COUNT(1) FROM c 
                WHERE c.tenantId = @tenant_id 
                  AND c.type = 'tenant_user'
            """
            parameters = [
                {"name": "@tenant_id", "value": tenant_id}
            ]

            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=tenant_id,
            )

            async for item in items:
                return item

            return 0
        except CosmosHttpResponseError as e:
            self.logger.error(f"Failed to count tenant users: {e}")
            raise
