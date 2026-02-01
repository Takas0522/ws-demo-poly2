"""ドメイン管理API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response

from app.schemas.domain import (
    DomainCreateRequest,
    DomainResponse,
    DomainVerificationResponse,
    DomainListResponse
)
from app.services.domain_service import DomainService
from app.repositories.domain_repository import DomainRepository
from app.repositories.tenant_repository import TenantRepository

router = APIRouter()


def get_domain_service(request: Request) -> DomainService:
    """DomainService依存注入"""
    container = request.app.state.cosmos_container
    domain_repository = DomainRepository(container)
    tenant_repository = TenantRepository(container)
    return DomainService(domain_repository, tenant_repository)


@router.post(
    "/{tenant_id}/domains",
    response_model=DomainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ドメイン追加",
    description="テナントに独自ドメインを追加します。管理者ロールが必要です。"
)
async def add_domain(
    tenant_id: str,
    request_data: DomainCreateRequest,
    service: DomainService = Depends(get_domain_service)
):
    """
    独自ドメインの追加
    
    Phase 1: 認証・認可は未実装（開発環境）
    Phase 2: JWT検証、ロールベース認可を実装
    
    Args:
        tenant_id: テナントID
        request_data: ドメイン作成リクエスト
        service: DomainService
    
    Returns:
        DomainResponse: 作成されたDomain情報とDNS設定手順
    
    Raises:
        HTTPException 404: テナントが存在しない
        HTTPException 422: ドメイン形式不正
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["管理者", "全体管理者"])
    created_by = "system"  # Phase 1では固定値

    try:
        domain = await service.add_domain(
            tenant_id, request_data.domain, created_by
        )

        # DNS設定手順を生成
        verification_instructions = service._generate_verification_instructions(
            domain.domain, domain.verification_token
        )

        return DomainResponse(
            id=domain.id,
            tenant_id=domain.tenant_id,
            domain=domain.domain,
            verified=domain.verified,
            verification_token=domain.verification_token,
            verification_instructions=verification_instructions,
            verified_at=domain.verified_at,
            verified_by=domain.verified_by,
            created_at=domain.created_at,
            created_by=domain.created_by
        )
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=404, detail=error_message)
        else:
            raise HTTPException(status_code=422, detail=error_message)
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error adding domain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{tenant_id}/domains/{domain_id}/verify",
    response_model=DomainVerificationResponse,
    summary="ドメイン検証",
    description="DNS TXTレコードを使用してドメインの所有権を検証します。管理者ロールが必要です。"
)
async def verify_domain(
    tenant_id: str,
    domain_id: str,
    service: DomainService = Depends(get_domain_service)
):
    """
    ドメイン所有権の検証
    
    Args:
        tenant_id: テナントID
        domain_id: ドメインID
        service: DomainService
    
    Returns:
        DomainVerificationResponse: 検証結果
    
    Raises:
        HTTPException 404: Domainが存在しない
        HTTPException 422: 検証失敗（TXTレコード不一致）
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["管理者", "全体管理者"])
    verified_by = "system"  # Phase 1では固定値

    try:
        domain = await service.verify_domain(tenant_id, domain_id, verified_by)

        return DomainVerificationResponse(
            id=domain.id,
            domain=domain.domain,
            verified=domain.verified,
            verified_at=domain.verified_at,
            verified_by=domain.verified_by
        )
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=404, detail=error_message)
        elif "verification failed" in error_message.lower():
            raise HTTPException(status_code=422, detail=error_message)
        else:
            raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error verifying domain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{tenant_id}/domains",
    response_model=DomainListResponse,
    summary="ドメイン一覧",
    description="テナントに登録されているドメインの一覧を取得します。閲覧者以上のロールが必要です。"
)
async def list_domains(
    tenant_id: str,
    verified: Optional[bool] = None,
    service: DomainService = Depends(get_domain_service)
):
    """
    ドメイン一覧取得
    
    Args:
        tenant_id: テナントID
        verified: 検証済みフィルタ（オプション）
        service: DomainService
    
    Returns:
        DomainListResponse: ドメイン一覧
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["閲覧者", "管理者", "全体管理者"])

    try:
        domains = await service.list_domains(tenant_id, verified)

        domain_responses = [
            DomainResponse(
                id=domain.id,
                tenant_id=domain.tenant_id,
                domain=domain.domain,
                verified=domain.verified,
                verification_token=None,  # 一覧では非表示
                verification_instructions=None,
                verified_at=domain.verified_at,
                verified_by=domain.verified_by,
                created_at=domain.created_at,
                created_by=domain.created_by
            )
            for domain in domains
        ]

        return DomainListResponse(data=domain_responses)
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error listing domains: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{tenant_id}/domains/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ドメイン削除",
    description="登録済みドメインを削除します。管理者ロールが必要です。"
)
async def delete_domain(
    tenant_id: str,
    domain_id: str,
    service: DomainService = Depends(get_domain_service)
):
    """
    ドメイン削除
    
    Args:
        tenant_id: テナントID
        domain_id: ドメインID
        service: DomainService
    
    Returns:
        Response: 204 No Content
    
    Raises:
        HTTPException 404: Domainが存在しない
    """
    # TODO: Phase 2でJWT検証とロールチェックを実装
    # current_user = get_current_user(request)
    # require_role("tenant-management", ["管理者", "全体管理者"])
    deleted_by = "system"  # Phase 1では固定値

    try:
        await service.delete_domain(tenant_id, domain_id, deleted_by)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 情報漏洩防止: 詳細はログのみ
        import logging
        logging.getLogger(__name__).error(f"Unexpected error deleting domain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
