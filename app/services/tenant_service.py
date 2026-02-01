"""テナント管理サービス"""
from typing import List, Optional
from datetime import datetime
import logging
import re
from slugify import slugify

from app.models.tenant import Tenant, TenantCreate, TenantUpdate
from app.repositories.tenant_repository import TenantRepository

logger = logging.getLogger(__name__)


class TenantService:
    """テナント管理サービス"""

    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository
        self.logger = logger

    def validate_tenant_name(self, name: str) -> bool:
        """
        テナント名のバリデーション
        
        Requirements:
        - 3文字以上、100文字以内
        - 英数字とハイフン・アンダースコアのみ
        """
        if len(name) < 3 or len(name) > 100:
            return False
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return False
        return True

    def validate_display_name(self, display_name: str) -> bool:
        """
        表示名のバリデーション
        
        Requirements:
        - 1文字以上、200文字以内
        """
        return 1 <= len(display_name) <= 200

    def validate_plan(self, plan: str) -> bool:
        """プランのバリデーション"""
        return plan in ["free", "standard", "premium"]

    def validate_max_users(self, max_users: int) -> bool:
        """最大ユーザー数のバリデーション"""
        return 1 <= max_users <= 10000

    async def create_tenant(
        self, data: TenantCreate, created_by: str
    ) -> Tenant:
        """
        テナント作成（一意性チェック付き）
        
        Args:
            data: テナント作成データ
            created_by: 作成者ユーザーID
        
        Returns:
            Tenant: 作成されたテナント
        
        Raises:
            ValueError: バリデーションエラー、一意性違反
        """
        # 1. バリデーション
        if not self.validate_tenant_name(data.name):
            raise ValueError(
                "Invalid tenant name. Must be 3-100 characters, alphanumeric with hyphens and underscores only"
            )
        
        if not self.validate_display_name(data.display_name):
            raise ValueError(
                "Invalid display name. Must be 1-200 characters"
            )
        
        if data.plan and not self.validate_plan(data.plan):
            raise ValueError(
                "Invalid plan. Must be one of: free, standard, premium"
            )
        
        if data.max_users and not self.validate_max_users(data.max_users):
            raise ValueError(
                "Invalid max users. Must be between 1 and 10000"
            )

        # 2. テナント名の一意性チェック
        existing = await self.tenant_repository.find_by_name(data.name)
        if existing:
            raise ValueError(f"Tenant name '{data.name}' already exists")

        # 3. テナントID生成（name をslug化）
        tenant_id = f"tenant_{slugify(data.name, separator='_')}"

        # 4. Tenantオブジェクト作成
        tenant = Tenant(
            id=tenant_id,
            tenant_id=tenant_id,
            name=data.name,
            display_name=data.display_name,
            plan=data.plan or "standard",
            max_users=data.max_users or 100,
            user_count=0,
            status="active",
            is_privileged=False,
            metadata=data.metadata,
            created_by=created_by,
            updated_by=created_by,
        )

        # 5. データベースに保存
        created_tenant = await self.tenant_repository.create(tenant)

        self.logger.info(
            f"Tenant created: {created_tenant.id} by {created_by}",
            extra={"tenant_id": created_tenant.id, "created_by": created_by},
        )

        return created_tenant

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """テナント取得"""
        return await self.tenant_repository.get(tenant_id, tenant_id)

    async def list_tenants(
        self,
        current_tenant_id: str,
        is_privileged: bool,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Tenant]:
        """
        テナント一覧取得（ロールベース認可とテナント分離）
        
        Args:
            current_tenant_id: 現在のユーザーのテナントID
            is_privileged: 特権テナントかどうか
            status: ステータスフィルタ
            skip: スキップ件数
            limit: 取得件数
        
        Returns:
            List[Tenant]: テナント一覧
        """
        if is_privileged:
            # 特権テナントは全テナントを取得
            return await self.tenant_repository.list_all(status, skip, limit)
        else:
            # 一般テナントは自テナントのみ取得
            return await self.tenant_repository.list_by_tenant_id(
                current_tenant_id, status
            )

    async def update_tenant(
        self, tenant_id: str, data: TenantUpdate, updated_by: str
    ) -> Tenant:
        """
        テナント更新（特権テナント保護）
        
        Args:
            tenant_id: テナントID
            data: 更新データ
            updated_by: 更新者ユーザーID
        
        Returns:
            Tenant: 更新されたテナント
        
        Raises:
            ValueError: テナントが存在しない、特権テナント、バリデーションエラー
        """
        # 1. テナント取得
        tenant = await self.tenant_repository.get(tenant_id, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # 2. 特権テナントチェック
        if tenant.is_privileged:
            raise ValueError("Privileged tenant cannot be modified")

        # 3. バリデーション
        if data.display_name and not self.validate_display_name(data.display_name):
            raise ValueError("Invalid display name. Must be 1-200 characters")
        
        if data.plan and not self.validate_plan(data.plan):
            raise ValueError("Invalid plan. Must be one of: free, standard, premium")
        
        if data.max_users and not self.validate_max_users(data.max_users):
            raise ValueError("Invalid max users. Must be between 1 and 10000")

        # 4. 更新データ準備
        update_data = {}
        if data.display_name is not None:
            update_data["displayName"] = data.display_name
        if data.plan is not None:
            update_data["plan"] = data.plan
        if data.max_users is not None:
            update_data["maxUsers"] = data.max_users
        if data.metadata is not None:
            update_data["metadata"] = data.metadata
        
        update_data["updatedBy"] = updated_by

        # 5. 更新実行
        updated_tenant = await self.tenant_repository.update(
            tenant_id, tenant_id, update_data
        )

        self.logger.info(
            f"Tenant updated: {tenant_id} by {updated_by}",
            extra={"tenant_id": tenant_id, "updated_by": updated_by},
        )

        return updated_tenant

    async def delete_tenant(self, tenant_id: str, deleted_by: str) -> None:
        """
        テナント削除（特権テナント保護、ユーザー数チェック）
        
        Phase 1: 物理削除
        Phase 2: 論理削除 + カスケード削除
        
        Args:
            tenant_id: テナントID
            deleted_by: 削除者ユーザーID
        
        Raises:
            ValueError: テナントが存在しない、特権テナント、ユーザーが存在
        """
        # 1. テナント取得
        tenant = await self.tenant_repository.get(tenant_id, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # 2. 特権テナントチェック
        if tenant.is_privileged:
            raise ValueError("Privileged tenant cannot be deleted")

        # 3. ユーザー数チェック（Phase 1）
        if tenant.user_count > 0:
            raise ValueError(
                "Cannot delete tenant with existing users. Please remove all users first."
            )

        # 4. 物理削除（Phase 1）
        await self.tenant_repository.delete(tenant_id, tenant_id)

        # 5. 監査ログ記録
        self.logger.info(
            f"Tenant deleted: {tenant_id} by {deleted_by}",
            extra={"tenant_id": tenant_id, "deleted_by": deleted_by},
        )

    async def increment_user_count(self, tenant_id: str) -> None:
        """
        テナントのユーザー数をインクリメント（タスク06で使用予定）
        
        Args:
            tenant_id: テナントID
        """
        tenant = await self.tenant_repository.get(tenant_id, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        update_data = {
            "userCount": tenant.user_count + 1,
            "updatedAt": datetime.utcnow().isoformat() + "Z",
        }
        await self.tenant_repository.update(tenant_id, tenant_id, update_data)

        self.logger.info(
            f"Tenant user count incremented: {tenant_id}",
            extra={"tenant_id": tenant_id, "user_count": tenant.user_count + 1},
        )

    async def decrement_user_count(self, tenant_id: str) -> None:
        """
        テナントのユーザー数をデクリメント（タスク06で使用予定）
        
        Args:
            tenant_id: テナントID
        """
        tenant = await self.tenant_repository.get(tenant_id, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        new_count = max(0, tenant.user_count - 1)
        update_data = {
            "userCount": new_count,
            "updatedAt": datetime.utcnow().isoformat() + "Z",
        }
        await self.tenant_repository.update(tenant_id, tenant_id, update_data)

        self.logger.info(
            f"Tenant user count decremented: {tenant_id}",
            extra={"tenant_id": tenant_id, "user_count": new_count},
        )
