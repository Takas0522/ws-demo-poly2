"""テナントユーザー管理API"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response

from app.schemas.tenant_user import (
    TenantUserCreateRequest,
    TenantUserResponse,
    TenantUserListResponse
)
from app.services.tenant_user_service import TenantUserService
from app.repositories.tenant_user_repository import TenantUserRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.tenant_service import TenantService
from app.services.auth_service_client import AuthServiceClient

router = APIRouter()


def get_tenant_user_service(request: Request) -> TenantUserService:
    """TenantUserService依存注入"""
    container = request.app.state.cosmos_container
    tenant_user_repository = TenantUserRepository(container)
    tenant_repository = TenantRepository(container)
    tenant_service = TenantService(tenant_repository)
    auth_service_client = AuthServiceClient()
    return TenantUserService(
        tenant_user_repository,
        tenant_repository,
        tenant_service,
        auth_service_client
    )


@router.post(
    "/{tenant_id}/users",
    response_model=TenantUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー招待",
    description="既存のユーザーをテナントに招待します。管理者ロールが必要です。"
)
async def invite_user(
    tenant_id: str,
    request_data: TenantUserCreateRequest,
    service: TenantUserService = Depends(get_tenant_user_service)
):
    """
    テナントへのユーザー招待
    
    Phase 1: 認証・認可は未実装（開発環境）
    Phase 2: JWT検証、ロールベース認可を実装
    
    Args:
        tenant_id: テナントID
        request_data: ユーザー招待リクエスト
        service: TenantUserService
    
    Returns:
        TenantUserResponse: 作成されたTenantUser情報
    
    Raises:
        HTTPException 404: テナントまたはユーザーが存在しない
        HTTPException 409: ユーザーは既にテナントに所属
        HTTPException 400: 最大ユーザー数を超過
        HTTPException 503: 認証認可サービスが利用不可
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["管理者", "全体管理者"])
    assigned_by = "system"  # Phase 1では固定値

    try:
        tenant_user = await service.invite_user(
            tenant_id, request_data.user_id, assigned_by
        )

        # ユーザー詳細情報を取得
        auth_client = AuthServiceClient()
        user_details = await auth_client.get_user_details(request_data.user_id)

        return TenantUserResponse(
            id=tenant_user.id,
            tenant_id=tenant_user.tenant_id,
            user_id=tenant_user.user_id,
            user_details=user_details,
            assigned_at=tenant_user.assigned_at,
            assigned_by=tenant_user.assigned_by
        )
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=404, detail=error_message)
        elif "already a member" in error_message.lower():
            raise HTTPException(status_code=409, detail=error_message)
        elif "maximum user limit" in error_message.lower():
            raise HTTPException(status_code=400, detail=error_message)
        else:
            raise HTTPException(status_code=400, detail=error_message)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error inviting user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{tenant_id}/users",
    response_model=TenantUserListResponse,
    summary="テナント所属ユーザー一覧",
    description="テナントに所属するユーザーの一覧を取得します。閲覧者以上のロールが必要です。"
)
async def list_tenant_users(
    tenant_id: str,
    skip: int = 0,
    limit: int = 20,
    include_total: bool = False,
    service: TenantUserService = Depends(get_tenant_user_service)
):
    """
    テナント所属ユーザー一覧取得
    
    Args:
        tenant_id: テナントID
        skip: スキップ件数（デフォルト: 0）
        limit: 取得件数（デフォルト: 20、最大: 100）
        include_total: totalカウントを含めるか（デフォルト: False）
        service: TenantUserService
    
    Returns:
        TenantUserListResponse: ユーザー一覧とページネーション情報
    
    Raises:
        HTTPException 400: limitが不正
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["閲覧者", "管理者", "全体管理者"])

    # skipの負数チェック
    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="Skip must be non-negative"
        )

    # limitのバリデーション
    if limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 100"
        )

    try:
        result = await service.list_tenant_users(tenant_id, skip, limit, include_total)
        
        # TenantUserResponseに変換
        user_responses = [
            TenantUserResponse(
                id=user["id"],
                tenant_id=user["tenant_id"],
                user_id=user["user_id"],
                user_details=user.get("user_details"),
                assigned_at=user["assigned_at"],
                assigned_by=user["assigned_by"]
            )
            for user in result["data"]
        ]

        return TenantUserListResponse(
            data=user_responses,
            pagination=result["pagination"]
        )
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error listing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{tenant_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ユーザー削除",
    description="テナントからユーザーを削除します（ユーザー本体は削除されません）。管理者ロールが必要です。"
)
async def remove_user(
    tenant_id: str,
    user_id: str,
    service: TenantUserService = Depends(get_tenant_user_service)
):
    """
    テナントからのユーザー削除
    
    Args:
        tenant_id: テナントID
        user_id: 削除するユーザーのID
        service: TenantUserService
    
    Returns:
        Response: 204 No Content
    
    Raises:
        HTTPException 404: TenantUserが存在しない
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["管理者", "全体管理者"])
    deleted_by = "system"  # Phase 1では固定値

    try:
        await service.remove_user(tenant_id, user_id, deleted_by)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error removing user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
