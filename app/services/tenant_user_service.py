"""テナントユーザー管理サービス"""
from typing import List, Dict, Any
from datetime import datetime
import logging
import asyncio

from app.models.tenant_user import TenantUser
from app.repositories.tenant_user_repository import TenantUserRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.tenant_service import TenantService
from app.services.auth_service_client import AuthServiceClient

logger = logging.getLogger(__name__)


class TenantUserService:
    """テナントユーザー管理サービス"""

    def __init__(
        self,
        tenant_user_repository: TenantUserRepository,
        tenant_repository: TenantRepository,
        tenant_service: TenantService,
        auth_service_client: AuthServiceClient
    ):
        self.tenant_user_repository = tenant_user_repository
        self.tenant_repository = tenant_repository
        self.tenant_service = tenant_service
        self.auth_service_client = auth_service_client
        self.logger = logger

    async def invite_user(
        self, tenant_id: str, user_id: str, assigned_by: str
    ) -> TenantUser:
        """
        ユーザー招待（重複チェック + 最大ユーザー数チェック + ユーザー存在確認）
        
        Args:
            tenant_id: テナントID
            user_id: 招待するユーザーのID
            assigned_by: 招待者のユーザーID
        
        Returns:
            TenantUser: 作成されたテナントユーザー
        
        Raises:
            ValueError: テナント不存在、重複、最大ユーザー数超過、ユーザー不存在
            RuntimeError: 認証認可サービス接続エラー
        """
        # 1. テナント存在確認
        tenant = await self.tenant_repository.get(tenant_id, tenant_id)
        if not tenant:
            self.logger.warning(
                "Failed to invite user: Tenant not found",
                extra={"tenant_id": tenant_id, "user_id": user_id, "assigned_by": assigned_by}
            )
            raise ValueError(f"Tenant {tenant_id} not found")

        # 2. ユーザー存在確認（認証認可サービスに問い合わせ）
        try:
            await self.auth_service_client.verify_user_exists(user_id)
        except ValueError as e:
            # ユーザーが存在しない
            self.logger.warning(
                "Failed to invite user: User not found",
                extra={"tenant_id": tenant_id, "user_id": user_id, "assigned_by": assigned_by, "error": str(e)}
            )
            raise ValueError(str(e))
        except RuntimeError as e:
            # 認証認可サービスが利用不可
            self.logger.error(
                "Failed to invite user: Auth service unavailable",
                extra={"tenant_id": tenant_id, "user_id": user_id, "assigned_by": assigned_by, "error": str(e)}
            )
            raise RuntimeError(str(e))
        except Exception as e:
            # サービス間認証失敗など
            self.logger.error(
                "Failed to invite user: Unexpected error from auth service",
                extra={"tenant_id": tenant_id, "user_id": user_id, "assigned_by": assigned_by, "error": str(e)}
            )
            raise Exception(str(e))

        # 3. 重複チェック
        existing = await self.tenant_user_repository.find_by_user(tenant_id, user_id)
        if existing:
            self.logger.warning(
                "Failed to invite user: User already member",
                extra={"tenant_id": tenant_id, "user_id": user_id, "assigned_by": assigned_by}
            )
            raise ValueError("User is already a member of this tenant")

        # 4. 最大ユーザー数チェック
        if tenant.user_count >= tenant.max_users:
            self.logger.warning(
                "Failed to invite user: Maximum user limit reached",
                extra={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "assigned_by": assigned_by,
                    "current_count": tenant.user_count,
                    "max_users": tenant.max_users
                }
            )
            raise ValueError(
                f"Tenant has reached maximum user limit ({tenant.max_users})"
            )

        # 5. TenantUserオブジェクト作成
        # IDは決定的ID: tenant_user_{tenant_id}_{user_id}
        # user_idからハイフンを除去してIDを生成
        clean_user_id = user_id.replace("-", "")
        clean_tenant_id = tenant_id.replace("-", "")
        tenant_user_id = f"tenant_user_{clean_tenant_id}_{clean_user_id}"

        tenant_user = TenantUser(
            id=tenant_user_id,
            tenant_id=tenant_id,
            user_id=user_id,
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by
        )

        # 6. Cosmos DBに保存
        created_tenant_user = await self.tenant_user_repository.create(tenant_user)

        # 7. user_countをインクリメント
        try:
            await self.tenant_service.increment_user_count(tenant_id)
        except Exception as e:
            # user_count更新失敗時はロールバック
            self.logger.error(f"Failed to increment user_count, rolling back: {e}")
            await self.tenant_user_repository.delete(tenant_user_id, tenant_id)
            raise

        # 8. 監査ログ記録
        self.logger.info(
            f"User invited to tenant: user={user_id}, tenant={tenant_id}, by={assigned_by}",
            extra={"user_id": user_id, "tenant_id": tenant_id, "assigned_by": assigned_by}
        )

        return created_tenant_user

    async def list_tenant_users(
        self, tenant_id: str, skip: int = 0, limit: int = 20, include_total: bool = False
    ) -> Dict[str, Any]:
        """
        テナント所属ユーザー一覧取得（ユーザー詳細情報を並列取得）
        
        Args:
            tenant_id: テナントID
            skip: スキップ件数
            limit: 取得件数
            include_total: totalカウントを含めるか
        
        Returns:
            Dict[str, Any]: {
                "data": [...],
                "pagination": {"skip": 0, "limit": 20, "total": 100}
            }
        """
        # 1. TenantUser一覧を取得
        tenant_users = await self.tenant_user_repository.list_by_tenant(
            tenant_id, skip, limit
        )

        # 2. totalカウント取得（オプション）
        total = None
        if include_total:
            total = await self.tenant_user_repository.count_by_tenant(tenant_id)

        # 3. ユーザー詳細情報を並列取得
        users_with_details = await self._get_tenant_users_with_details(tenant_users)

        # 4. レスポンス構築
        response = {
            "data": users_with_details,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }

        if total is not None:
            response["pagination"]["total"] = total

        return response

    async def _get_tenant_users_with_details(
        self, tenant_users: List[TenantUser]
    ) -> List[Dict[str, Any]]:
        """
        複数ユーザーの詳細情報を並列取得
        
        Parallelism: 最大10件同時
        """
        # 並列取得（最大10件同時）
        tasks = [
            self.auth_service_client.get_user_details(tu.user_id)
            for tu in tenant_users
        ]
        user_details_list = await asyncio.gather(*tasks, return_exceptions=False)

        # 結果をマージ（取得失敗したユーザーは基本情報のみ）
        results = []
        for tenant_user, user_details in zip(tenant_users, user_details_list):
            result = {
                "id": tenant_user.id,
                "tenant_id": tenant_user.tenant_id,
                "user_id": tenant_user.user_id,
                "assigned_at": tenant_user.assigned_at,
                "assigned_by": tenant_user.assigned_by
            }

            if user_details:
                result["user_details"] = user_details
            else:
                # フォールバック: 基本情報のみ
                result["user_details"] = {
                    "user_id": tenant_user.user_id,
                    "error": "Details unavailable"
                }

            results.append(result)

        return results

    async def remove_user(
        self, tenant_id: str, user_id: str, deleted_by: str
    ) -> None:
        """
        テナントからユーザーを削除（ユーザー本体は削除されない）
        
        Args:
            tenant_id: テナントID
            user_id: 削除するユーザーのID
            deleted_by: 削除者のユーザーID
        
        Raises:
            ValueError: TenantUserが存在しない
        """
        # 1. TenantUser存在確認
        clean_user_id = user_id.replace("-", "")
        clean_tenant_id = tenant_id.replace("-", "")
        tenant_user_id = f"tenant_user_{clean_tenant_id}_{clean_user_id}"

        existing = await self.tenant_user_repository.get(tenant_user_id, tenant_id)
        if not existing:
            self.logger.warning(
                "Failed to remove user: TenantUser not found",
                extra={"tenant_id": tenant_id, "user_id": user_id, "deleted_by": deleted_by}
            )
            raise ValueError(f"TenantUser not found: user={user_id}, tenant={tenant_id}")

        # 2. Cosmos DBから物理削除
        await self.tenant_user_repository.delete(tenant_user_id, tenant_id)

        # 3. user_countをデクリメント
        try:
            await self.tenant_service.decrement_user_count(tenant_id)
        except Exception as e:
            # user_count更新失敗をログに記録（ロールバックしない）
            self.logger.error(f"Failed to decrement user_count: {e}")

        # 4. 監査ログ記録
        self.logger.info(
            f"User removed from tenant: user={user_id}, tenant={tenant_id}, by={deleted_by}",
            extra={"user_id": user_id, "tenant_id": tenant_id, "deleted_by": deleted_by}
        )
