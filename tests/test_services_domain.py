"""ドメインサービスのテスト"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import dns.resolver
from app.services.domain_service import DomainService
from app.models.domain import Domain
from app.models.tenant import Tenant


@pytest.fixture
def mock_domain_repository():
    """モックDomainRepository"""
    mock = MagicMock()
    mock.create = AsyncMock()
    mock.get = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.list_by_tenant = AsyncMock()
    return mock


@pytest.fixture
def mock_tenant_repository():
    """モックTenantRepository"""
    mock = MagicMock()
    mock.get = AsyncMock()
    return mock


@pytest.fixture
def domain_service(mock_domain_repository, mock_tenant_repository):
    """DomainServiceインスタンス"""
    return DomainService(
        domain_repository=mock_domain_repository,
        tenant_repository=mock_tenant_repository
    )


class TestDomainServiceAddDomain:
    """add_domainメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_add_domain_successfully(self, domain_service, mock_tenant_repository, mock_domain_repository, sample_tenant):
            """ドメイン追加が成功する"""
            # Arrange: モックの戻り値を設定
            mock_tenant_repository.get.return_value = sample_tenant
            expected_domain = Domain(
                id="domain_tenant_test_example_com",
                tenant_id="tenant_test",
                domain="example.com",
                verified=False,
                verification_token="txt-verification-abc123",
                created_at=datetime.utcnow(),
                created_by="user_admin_001"
            )
            mock_domain_repository.create.return_value = expected_domain
            
            # Act: ドメイン追加を実行
            result = await domain_service.add_domain("tenant_test", "example.com", "user_admin_001")
            
            # Assert: ドメインが作成される
            assert result.domain == "example.com"
            assert result.verified == False
            assert result.verification_token.startswith("txt-verification-")
            mock_domain_repository.create.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_generate_verification_token(self, domain_service, mock_tenant_repository, mock_domain_repository, sample_tenant):
            """検証トークンが生成される（txt-verification-*形式）"""
            # Arrange: ドメイン追加準備
            mock_tenant_repository.get.return_value = sample_tenant
            expected_domain = Domain(
                id="domain_tenant_test_example_com",
                tenant_id="tenant_test",
                domain="example.com",
                verified=False,
                verification_token="txt-verification-abc123def456",
                created_at=datetime.utcnow(),
                created_by="user_admin_001"
            )
            mock_domain_repository.create.return_value = expected_domain
            
            # Act: ドメイン追加を実行
            result = await domain_service.add_domain("tenant_test", "example.com", "user_admin_001")
            
            # Assert: verification_tokenが"txt-verification-"で始まる
            assert result.verification_token.startswith("txt-verification-")
            assert len(result.verification_token) > 20  # 十分な長さがある

        @pytest.mark.asyncio
        async def test_should_generate_slugified_domain_id(self, domain_service, mock_tenant_repository, mock_domain_repository, sample_tenant):
            """slug化されたドメインIDが生成される"""
            # Arrange: ドメイン追加準備
            mock_tenant_repository.get.return_value = sample_tenant
            
            def check_domain_id(domain_obj):
                # IDが"domain_{tenant_id}_{slug}"形式であることを確認
                assert domain_obj.id == "domain_tenant_test_example_com"
                return domain_obj
            
            mock_domain_repository.create.side_effect = check_domain_id
            
            # Act: ドメイン追加を実行
            await domain_service.add_domain("tenant_test", "example.com", "user_admin_001")
            
            # Assert: createが呼ばれたことを確認
            mock_domain_repository.create.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_convert_domain_to_lowercase(self, domain_service, mock_tenant_repository, mock_domain_repository, sample_tenant):
            """ドメインが小文字に変換される"""
            # Arrange: 大文字を含むドメインを準備
            mock_tenant_repository.get.return_value = sample_tenant
            
            def check_domain_lowercase(domain_obj):
                # domainが小文字であることを確認
                assert domain_obj.domain == "example.com"
                assert domain_obj.domain.islower()
                return domain_obj
            
            mock_domain_repository.create.side_effect = check_domain_lowercase
            
            # Act: ドメイン追加を実行（大文字を含む）
            await domain_service.add_domain("tenant_test", "EXAMPLE.COM", "user_admin_001")
            
            # Assert: 小文字に変換される
            mock_domain_repository.create.assert_called_once()

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_raise_error_when_tenant_not_found(self, domain_service, mock_tenant_repository):
            """テナントが存在しない場合にエラー"""
            # Arrange
            mock_tenant_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="not found"):
                await domain_service.add_domain("tenant_notfound", "example.com", "user_admin_001")


class TestDomainServiceVerifyDomain:
    """verify_domainメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_verify_domain_successfully(self, domain_service, mock_domain_repository, sample_domain):
            """ドメイン検証が成功する"""
            # Arrange
            mock_domain_repository.get.return_value = sample_domain
            
            # DNS検証をモック
            with patch.object(domain_service, '_verify_domain_ownership', new_callable=AsyncMock) as mock_verify:
                mock_verify.return_value = True
                updated_domain = Domain(
                    id=sample_domain.id,
                    tenant_id=sample_domain.tenant_id,
                    domain=sample_domain.domain,
                    verified=True,
                    verification_token=sample_domain.verification_token,
                    verified_at=datetime.utcnow(),
                    verified_by="user_admin_001",
                    created_at=sample_domain.created_at,
                    created_by=sample_domain.created_by
                )
                mock_domain_repository.update.return_value = updated_domain
                
                # Act
                result = await domain_service.verify_domain("tenant_test", sample_domain.id, "user_admin_001")
                
                # Assert
                assert result.verified == True
                mock_verify.assert_called_once()
                mock_domain_repository.update.assert_called_once()

        @pytest.mark.asyncio
        async def test_should_skip_verification_if_already_verified(self, domain_service, mock_domain_repository, verified_domain):
            """既に検証済みの場合はスキップする"""
            # Arrange
            mock_domain_repository.get.return_value = verified_domain
            
            # Act
            result = await domain_service.verify_domain("tenant_test", verified_domain.id, "user_admin_001")
            
            # Assert
            assert result.verified == True
            # updateは呼ばれない（既に検証済みのため）
            mock_domain_repository.update.assert_not_called()

        @pytest.mark.asyncio
        async def test_should_update_domain_with_verification_info(self, domain_service, mock_domain_repository, sample_domain):
            """検証成功時にドメイン情報を更新する"""
            # Arrange
            mock_domain_repository.get.return_value = sample_domain
            
            with patch.object(domain_service, '_verify_domain_ownership', new_callable=AsyncMock) as mock_verify:
                mock_verify.return_value = True
                updated_domain = Domain(
                    id=sample_domain.id,
                    tenant_id=sample_domain.tenant_id,
                    domain=sample_domain.domain,
                    verified=True,
                    verification_token=sample_domain.verification_token,
                    verified_at=datetime.utcnow(),
                    verified_by="user_admin_001",
                    created_at=sample_domain.created_at,
                    created_by=sample_domain.created_by
                )
                mock_domain_repository.update.return_value = updated_domain
                
                # Act
                result = await domain_service.verify_domain("tenant_test", sample_domain.id, "user_admin_001")
                
                # Assert: updateが呼ばれ、verified/verifiedAt/verifiedByが設定される
                assert result.verified == True
                assert result.verified_at is not None
                assert result.verified_by == "user_admin_001"
                mock_domain_repository.update.assert_called_once()

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_raise_error_when_domain_not_found(self, domain_service, mock_domain_repository):
            """ドメインが存在しない場合にエラー"""
            # Arrange
            mock_domain_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="not found"):
                await domain_service.verify_domain("tenant_test", "domain_notfound", "user_admin_001")

        @pytest.mark.asyncio
        async def test_should_raise_error_when_txt_record_not_found(self, domain_service, mock_domain_repository, sample_domain):
            """TXTレコードが見つからない場合にエラー"""
            # Arrange
            mock_domain_repository.get.return_value = sample_domain
            
            with patch.object(domain_service, '_verify_domain_ownership', new_callable=AsyncMock) as mock_verify:
                mock_verify.return_value = False
                
                # Act & Assert
                with pytest.raises(ValueError, match="Verification failed"):
                    await domain_service.verify_domain("tenant_test", sample_domain.id, "user_admin_001")

        @pytest.mark.asyncio
        async def test_should_raise_error_when_txt_record_mismatch(self, domain_service, mock_domain_repository, sample_domain):
            """TXTレコードが一致しない場合にエラー"""
            # Arrange
            mock_domain_repository.get.return_value = sample_domain
            
            with patch.object(domain_service, '_verify_domain_ownership', new_callable=AsyncMock) as mock_verify:
                mock_verify.return_value = False
                
                # Act & Assert
                with pytest.raises(ValueError, match="Verification failed"):
                    await domain_service.verify_domain("tenant_test", sample_domain.id, "user_admin_001")

        @pytest.mark.asyncio
        async def test_should_retry_on_dns_timeout(self, domain_service, mock_domain_repository, sample_domain):
            """DNSタイムアウト時に最大3回リトライする"""
            # Arrange
            mock_domain_repository.get.return_value = sample_domain
            
            # _verify_domain_ownershipは@retryデコレータ付きなので、実際のメソッドをテスト
            with patch('dns.resolver.Resolver') as mock_resolver_class:
                mock_resolver = Mock()
                mock_resolver.resolve.side_effect = dns.exception.Timeout()
                mock_resolver_class.return_value = mock_resolver
                
                # Act & Assert: リトライ後にエラー
                with pytest.raises(dns.exception.Timeout):
                    await domain_service._verify_domain_ownership(sample_domain.domain, sample_domain.verification_token)
                
                # 最大3回試行される
                assert mock_resolver.resolve.call_count == 3

        @pytest.mark.asyncio
        async def test_should_handle_nxdomain_error(self, domain_service):
            """NXDOMAINエラーを適切に処理する"""
            # Arrange
            with patch('dns.resolver.Resolver') as mock_resolver_class:
                mock_resolver = Mock()
                mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()
                mock_resolver_class.return_value = mock_resolver
                
                # Act
                result = await domain_service._verify_domain_ownership("nonexistent.domain", "txt-verification-abc")
                
                # Assert: Falseを返す（エラーは発生しない）
                assert result == False

        @pytest.mark.asyncio
        async def test_should_handle_no_answer_error(self, domain_service):
            """NoAnswerエラーを適切に処理する"""
            # Arrange
            with patch('dns.resolver.Resolver') as mock_resolver_class:
                mock_resolver = Mock()
                mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()
                mock_resolver_class.return_value = mock_resolver
                
                # Act
                result = await domain_service._verify_domain_ownership("example.com", "txt-verification-abc")
                
                # Assert: Falseを返す（エラーは発生しない）
                assert result == False


class TestDomainServiceListDomains:
    """list_domainsメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_list_all_domains(self, domain_service, mock_domain_repository, sample_domain, verified_domain):
            """全ドメインを取得できる"""
            # Arrange
            mock_domain_repository.list_by_tenant.return_value = [sample_domain, verified_domain]
            
            # Act
            result = await domain_service.list_domains("tenant_test")
            
            # Assert
            assert len(result) == 2
            mock_domain_repository.list_by_tenant.assert_called_once_with("tenant_test", None)

        @pytest.mark.asyncio
        async def test_should_filter_verified_domains(self, domain_service, mock_domain_repository, verified_domain):
            """検証済みドメインのみをフィルタできる"""
            # Arrange
            mock_domain_repository.list_by_tenant.return_value = [verified_domain]
            
            # Act
            result = await domain_service.list_domains("tenant_test", verified=True)
            
            # Assert
            assert len(result) == 1
            assert result[0].verified == True
            mock_domain_repository.list_by_tenant.assert_called_once_with("tenant_test", True)

        @pytest.mark.asyncio
        async def test_should_filter_unverified_domains(self, domain_service, mock_domain_repository, sample_domain):
            """未検証ドメインのみをフィルタできる"""
            # Arrange
            mock_domain_repository.list_by_tenant.return_value = [sample_domain]
            
            # Act
            result = await domain_service.list_domains("tenant_test", verified=False)
            
            # Assert
            assert len(result) == 1
            assert result[0].verified == False
            mock_domain_repository.list_by_tenant.assert_called_once_with("tenant_test", False)


class TestDomainServiceDeleteDomain:
    """delete_domainメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.asyncio
        async def test_should_delete_domain_successfully(self, domain_service, mock_domain_repository, sample_domain):
            """ドメイン削除が成功する"""
            # Arrange
            mock_domain_repository.get.return_value = sample_domain
            mock_domain_repository.delete.return_value = None
            
            # Act
            await domain_service.delete_domain("tenant_test", sample_domain.id, "user_admin_001")
            
            # Assert
            mock_domain_repository.delete.assert_called_once_with(sample_domain.id, "tenant_test")

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.asyncio
        async def test_should_raise_error_when_domain_not_found(self, domain_service, mock_domain_repository):
            """ドメインが存在しない場合にエラー"""
            # Arrange
            mock_domain_repository.get.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="not found"):
                await domain_service.delete_domain("tenant_test", "domain_notfound", "user_admin_001")


class TestDomainServiceHelperMethods:
    """ヘルパーメソッドのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_generate_verification_token_with_correct_format(self, domain_service):
            """正しい形式の検証トークンを生成する"""
            # Act
            token = domain_service._generate_verification_token()
            
            # Assert
            assert token.startswith("txt-verification-")
            # "txt-verification-" (17文字) + 32文字のhex = 49文字
            assert len(token) == 49

        def test_should_generate_verification_instructions(self, domain_service):
            """DNS設定手順を生成する"""
            # Act
            instructions = domain_service._generate_verification_instructions("example.com", "txt-verification-abc123")
            
            # Assert
            assert "step1" in instructions
            assert "step2" in instructions
            assert "record_name" in instructions
            assert instructions["record_name"] == "_tenant_verification.example.com"
            assert instructions["record_type"] == "TXT"
            assert instructions["record_value"] == "txt-verification-abc123"

        def test_should_generate_unique_verification_tokens(self, domain_service):
            """一意の検証トークンを生成する"""
            # Act: 複数回トークンを生成
            tokens = [domain_service._generate_verification_token() for _ in range(10)]
            
            # Assert: すべてユニーク
            assert len(tokens) == len(set(tokens))

