"""ドメイン管理サービス"""
from typing import List, Optional, Dict
from datetime import datetime
import logging
import secrets
import dns.resolver
from slugify import slugify
from tenacity import retry, stop_after_attempt, wait_fixed

from app.models.domain import Domain
from app.repositories.domain_repository import DomainRepository
from app.repositories.tenant_repository import TenantRepository

logger = logging.getLogger(__name__)


class DomainService:
    """ドメイン管理サービス"""

    def __init__(
        self,
        domain_repository: DomainRepository,
        tenant_repository: TenantRepository
    ):
        self.domain_repository = domain_repository
        self.tenant_repository = tenant_repository
        self.logger = logger

    def _generate_verification_token(self) -> str:
        """検証トークン生成（32桁のランダム文字列）"""
        random_str = secrets.token_hex(16)  # 32文字
        return f"txt-verification-{random_str}"

    def _generate_verification_instructions(
        self, domain: str, token: str
    ) -> Dict[str, str]:
        """DNS設定手順の生成"""
        return {
            "step1": "DNSプロバイダーにログイン",
            "step2": "以下のTXTレコードを追加:",
            "record_name": f"_tenant_verification.{domain}",
            "record_type": "TXT",
            "record_value": token
        }

    async def add_domain(
        self, tenant_id: str, domain: str, created_by: str
    ) -> Domain:
        """
        独自ドメインを追加
        
        Args:
            tenant_id: テナントID
            domain: ドメイン名（例: "example.com"）
            created_by: 作成者ユーザーID
        
        Returns:
            Domain: 作成されたドメイン
        
        Raises:
            ValueError: テナント不存在
        """
        # 1. テナント存在確認
        tenant = await self.tenant_repository.get(tenant_id, tenant_id)
        if not tenant:
            self.logger.warning(
                "Failed to add domain: Tenant not found",
                extra={"tenant_id": tenant_id, "domain": domain, "created_by": created_by}
            )
            raise ValueError(f"Tenant {tenant_id} not found")

        # 2. 検証トークン生成
        verification_token = self._generate_verification_token()

        # 3. ドメインID生成
        # domain_{tenant_id}_{slug化したdomain}
        slugified_domain = slugify(domain, separator='_')
        domain_id = f"domain_{tenant_id}_{slugified_domain}"

        # 4. Domainオブジェクト作成
        domain_obj = Domain(
            id=domain_id,
            tenant_id=tenant_id,
            domain=domain.lower(),
            verified=False,
            verification_token=verification_token,
            created_at=datetime.utcnow(),
            created_by=created_by
        )

        # 5. Cosmos DBに保存
        created_domain = await self.domain_repository.create(domain_obj)

        # 6. 監査ログ記録
        self.logger.info(
            f"Domain added: domain={domain}, tenant={tenant_id}, by={created_by}",
            extra={"domain": domain, "tenant_id": tenant_id, "created_by": created_by}
        )

        return created_domain

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        reraise=True
    )
    async def _verify_domain_ownership(
        self, domain: str, expected_token: str
    ) -> bool:
        """
        DNS TXTレコードでドメイン所有権を検証
        
        Args:
            domain: 検証するドメイン（例: "example.com"）
            expected_token: 期待する検証トークン
        
        Returns:
            bool: 検証成功時True、失敗時False
        
        Raises:
            dns.exception.Timeout: DNS問い合わせタイムアウト（5秒超過）
        
        Retry Policy:
            - 最大3回リトライ
            - 固定間隔1秒
            - DNS伝播の遅延に対応
        """
        record_name = f"_tenant_verification.{domain}"

        try:
            # DNS Resolverの設定
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5.0  # タイムアウト5秒
            resolver.lifetime = 5.0  # 全体のタイムアウト5秒

            # DNS TXTレコードクエリ
            answers = resolver.resolve(record_name, 'TXT')

            # 各TXTレコードをチェック
            for rdata in answers:
                for txt_string in rdata.strings:
                    txt_value = txt_string.decode('utf-8')
                    self.logger.info(f"Found TXT record: {txt_value}")
                    if txt_value == expected_token:
                        return True

            self.logger.warning(f"TXT record found but token mismatch for {domain}")
            return False

        except dns.resolver.NXDOMAIN:
            # ドメインが存在しない
            self.logger.warning(f"Domain does not exist: {domain}")
            return False
        except dns.resolver.NoAnswer:
            # TXTレコードが存在しない
            self.logger.warning(f"No TXT record found for {record_name}")
            return False
        except dns.exception.Timeout:
            # タイムアウト（リトライ対象）
            self.logger.warning(f"DNS query timeout for {record_name}")
            raise
        except Exception as e:
            # その他のDNSエラー
            self.logger.error(f"DNS verification error for {domain}: {e}")
            return False

    async def verify_domain(
        self, tenant_id: str, domain_id: str, verified_by: str
    ) -> Domain:
        """
        ドメイン所有権の検証
        
        Args:
            tenant_id: テナントID
            domain_id: ドメインID
            verified_by: 検証者ユーザーID
        
        Returns:
            Domain: 検証済みドメイン
        
        Raises:
            ValueError: ドメイン不存在、既に検証済み、検証失敗
        """
        # 1. Domain取得
        domain = await self.domain_repository.get(domain_id, tenant_id)
        if not domain:
            self.logger.warning(
                "Failed to verify domain: Domain not found",
                extra={"tenant_id": tenant_id, "domain_id": domain_id, "verified_by": verified_by}
            )
            raise ValueError(f"Domain {domain_id} not found")

        # 2. 既に検証済みの場合はスキップ
        if domain.verified:
            self.logger.info(f"Domain {domain.domain} is already verified")
            return domain

        # 3. DNS TXTレコードクエリ
        is_verified = await self._verify_domain_ownership(
            domain.domain, domain.verification_token
        )

        if not is_verified:
            self.logger.warning(
                "Failed to verify domain: TXT record not found or mismatch",
                extra={
                    "tenant_id": tenant_id,
                    "domain_id": domain_id,
                    "domain": domain.domain,
                    "verified_by": verified_by
                }
            )
            raise ValueError(
                "Verification failed: TXT record not found or mismatch"
            )

        # 4. 検証成功: ドメイン更新
        update_data = {
            "verified": True,
            "verifiedAt": datetime.utcnow().isoformat() + "Z",
            "verifiedBy": verified_by
        }
        updated_domain = await self.domain_repository.update(
            domain_id, tenant_id, update_data
        )

        # 5. 監査ログ記録
        self.logger.info(
            f"Domain verified: domain={domain.domain}, tenant={tenant_id}, by={verified_by}",
            extra={"domain": domain.domain, "tenant_id": tenant_id, "verified_by": verified_by}
        )

        return updated_domain

    async def list_domains(
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
        return await self.domain_repository.list_by_tenant(tenant_id, verified)

    async def delete_domain(
        self, tenant_id: str, domain_id: str, deleted_by: str
    ) -> None:
        """
        ドメイン削除
        
        Args:
            tenant_id: テナントID
            domain_id: ドメインID
            deleted_by: 削除者ユーザーID
        
        Raises:
            ValueError: ドメイン不存在
        """
        # 1. Domain取得
        domain = await self.domain_repository.get(domain_id, tenant_id)
        if not domain:
            self.logger.warning(
                "Failed to delete domain: Domain not found",
                extra={"tenant_id": tenant_id, "domain_id": domain_id, "deleted_by": deleted_by}
            )
            raise ValueError(f"Domain {domain_id} not found")

        # 2. Cosmos DBから物理削除
        await self.domain_repository.delete(domain_id, tenant_id)

        # 3. 監査ログ記録
        self.logger.info(
            f"Domain deleted: domain={domain.domain}, tenant={tenant_id}, by={deleted_by}",
            extra={"domain": domain.domain, "tenant_id": tenant_id, "deleted_by": deleted_by}
        )
