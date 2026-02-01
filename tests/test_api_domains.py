"""ドメイン管理APIのテスト"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
from app.main import app
from app.models.domain import Domain
from app.api.domains import get_domain_service


@pytest.fixture
def client():
    """FastAPIテストクライアント"""
    # Cosmos DB初期化を無効化
    app.state.cosmos_client = Mock()
    app.state.cosmos_container = Mock()
    return TestClient(app)


@pytest.fixture
def mock_domain_service():
    """モックDomainService"""
    mock = MagicMock()
    mock.add_domain = AsyncMock()
    mock.verify_domain = AsyncMock()
    mock.list_domains = AsyncMock()
    mock.delete_domain = AsyncMock()
    mock._generate_verification_instructions = MagicMock()
    return mock


class TestAddDomainAPI:
    """POST /tenants/{tenant_id}/domains のテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_add_domain_successfully(self, client, mock_domain_service, sample_domain):
            """ドメイン追加が成功する（201 Created）"""
            # Arrange: リクエストデータを準備
            request_data = {"domain": "newdomain.com"}
            mock_domain_service.add_domain.return_value = sample_domain
            mock_domain_service._generate_verification_instructions.return_value = {
                "step1": "DNSプロバイダーにログイン",
                "step2": "以下のTXTレコードを追加:",
                "record_name": "_tenant_verification.example.com",
                "record_type": "TXT",
                "record_value": "txt-verification-abc123def456"
            }
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act: APIを呼び出し
            response = client.post("/api/v1/tenants/tenant_test/domains", json=request_data)
            
            # Assert: 201が返る
            assert response.status_code == 201
            app.dependency_overrides.clear()

        def test_should_return_domain_with_verification_instructions(self, client, mock_domain_service, sample_domain):
            """DNS設定手順を含むDomainを返す"""
            # Arrange: リクエストデータを準備
            request_data = {"domain": "newdomain.com"}
            mock_domain_service.add_domain.return_value = sample_domain
            expected_instructions = {
                "step1": "DNSプロバイダーにログイン",
                "step2": "以下のTXTレコードを追加:",
                "record_name": "_tenant_verification.example.com",
                "record_type": "TXT",
                "record_value": "txt-verification-abc123def456"
            }
            mock_domain_service._generate_verification_instructions.return_value = expected_instructions
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act: APIを呼び出し
            response = client.post("/api/v1/tenants/tenant_test/domains", json=request_data)
            
            # Assert: verificationInstructionsが含まれる
            assert response.status_code == 201
            data = response.json()
            assert "verificationInstructions" in data
            assert data["verificationInstructions"] == expected_instructions
            app.dependency_overrides.clear()

        def test_should_return_verification_token(self, client, mock_domain_service, sample_domain):
            """検証トークンを含む"""
            # Arrange: リクエストデータを準備
            request_data = {"domain": "newdomain.com"}
            mock_domain_service.add_domain.return_value = sample_domain
            mock_domain_service._generate_verification_instructions.return_value = {}
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act: APIを呼び出し
            response = client.post("/api/v1/tenants/tenant_test/domains", json=request_data)
            
            # Assert: verificationTokenが含まれる
            assert response.status_code == 201
            data = response.json()
            assert "verificationToken" in data
            assert data["verificationToken"] == "txt-verification-abc123def456"
            app.dependency_overrides.clear()

    class Test異常系:
        """異常系テスト"""

        def test_should_return_404_when_tenant_not_found(self, client, mock_domain_service):
            """テナントが存在しない場合に404を返す"""
            # Arrange
            request_data = {"domain": "newdomain.com"}
            mock_domain_service.add_domain.side_effect = ValueError("Tenant tenant_notfound not found")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_notfound/domains", json=request_data)
            
            # Assert
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
            app.dependency_overrides.clear()

        def test_should_return_422_when_invalid_domain_format(self, client):
            """不正なドメイン形式の場合に422を返す"""
            # Arrange
            request_data = {"domain": "invalid..domain"}
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains", json=request_data)
            
            # Assert
            assert response.status_code == 422

        def test_should_return_422_when_forbidden_domain(self, client):
            """禁止ドメインの場合に422を返す"""
            # Arrange
            request_data = {"domain": "localhost"}
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains", json=request_data)
            
            # Assert
            assert response.status_code == 422

        def test_should_return_500_on_unexpected_error(self, client, mock_domain_service):
            """予期しないエラー時に500を返す"""
            # Arrange
            request_data = {"domain": "newdomain.com"}
            mock_domain_service.add_domain.side_effect = Exception("Unexpected error")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains", json=request_data)
            
            # Assert
            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
            app.dependency_overrides.clear()


class TestVerifyDomainAPI:
    """POST /tenants/{tenant_id}/domains/{domain_id}/verify のテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_verify_domain_successfully(self, client, mock_domain_service, verified_domain):
            """ドメイン検証が成功する（200 OK）"""
            # Arrange
            mock_domain_service.verify_domain.return_value = verified_domain
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains/domain_test_example_com/verify")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["verified"] == True
            app.dependency_overrides.clear()

        def test_should_return_verification_result(self, client, mock_domain_service, verified_domain):
            """検証結果を含む"""
            # Arrange
            mock_domain_service.verify_domain.return_value = verified_domain
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains/domain_test_example_com/verify")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "verified" in data
            assert "verifiedAt" in data
            assert "verifiedBy" in data
            app.dependency_overrides.clear()

    class Test異常系:
        """異常系テスト"""

        def test_should_return_404_when_domain_not_found(self, client, mock_domain_service):
            """ドメインが存在しない場合に404を返す"""
            # Arrange
            mock_domain_service.verify_domain.side_effect = ValueError("Domain domain_notfound not found")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains/domain_notfound/verify")
            
            # Assert
            assert response.status_code == 404
            app.dependency_overrides.clear()

        def test_should_return_422_when_verification_failed(self, client, mock_domain_service):
            """検証失敗時に422を返す"""
            # Arrange
            mock_domain_service.verify_domain.side_effect = ValueError("Verification failed: TXT record not found")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains/domain_test_example_com/verify")
            
            # Assert
            assert response.status_code == 422
            app.dependency_overrides.clear()

        def test_should_return_500_on_unexpected_error(self, client, mock_domain_service):
            """予期しないエラー時に500を返す"""
            # Arrange
            mock_domain_service.verify_domain.side_effect = Exception("Unexpected error")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.post("/api/v1/tenants/tenant_test/domains/domain_test_example_com/verify")
            
            # Assert
            assert response.status_code == 500
            app.dependency_overrides.clear()


class TestListDomainsAPI:
    """GET /tenants/{tenant_id}/domains のテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_list_domains_successfully(self, client, mock_domain_service, sample_domain):
            """ドメイン一覧を取得できる（200 OK）"""
            # Arrange
            mock_domain_service.list_domains.return_value = [sample_domain]
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.get("/api/v1/tenants/tenant_test/domains")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) == 1
            app.dependency_overrides.clear()

        def test_should_filter_by_verified_status(self, client, mock_domain_service, verified_domain):
            """verifiedパラメータでフィルタできる"""
            # Arrange
            mock_domain_service.list_domains.return_value = [verified_domain]
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.get("/api/v1/tenants/tenant_test/domains?verified=true")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 1
            assert data["data"][0]["verified"] == True
            app.dependency_overrides.clear()

        def test_should_not_include_verification_token_in_list(self, client, mock_domain_service, sample_domain):
            """一覧では検証トークンを含まない"""
            # Arrange
            mock_domain_service.list_domains.return_value = [sample_domain]
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.get("/api/v1/tenants/tenant_test/domains")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["data"][0]["verificationToken"] is None
            app.dependency_overrides.clear()

    class Test異常系:
        """異常系テスト"""

        def test_should_return_500_on_unexpected_error(self, client, mock_domain_service):
            """予期しないエラー時に500を返す"""
            # Arrange
            mock_domain_service.list_domains.side_effect = Exception("Unexpected error")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.get("/api/v1/tenants/tenant_test/domains")
            
            # Assert
            assert response.status_code == 500
            app.dependency_overrides.clear()


class TestDeleteDomainAPI:
    """DELETE /tenants/{tenant_id}/domains/{domain_id} のテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_delete_domain_successfully(self, client, mock_domain_service):
            """ドメイン削除が成功する（204 No Content）"""
            # Arrange
            mock_domain_service.delete_domain.return_value = None
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.delete("/api/v1/tenants/tenant_test/domains/domain_test_example_com")
            
            # Assert
            assert response.status_code == 204
            app.dependency_overrides.clear()

    class Test異常系:
        """異常系テスト"""

        def test_should_return_404_when_domain_not_found(self, client, mock_domain_service):
            """ドメインが存在しない場合に404を返す"""
            # Arrange
            mock_domain_service.delete_domain.side_effect = ValueError("Domain domain_notfound not found")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.delete("/api/v1/tenants/tenant_test/domains/domain_notfound")
            
            # Assert
            assert response.status_code == 404
            app.dependency_overrides.clear()

        def test_should_return_500_on_unexpected_error(self, client, mock_domain_service):
            """予期しないエラー時に500を返す"""
            # Arrange
            mock_domain_service.delete_domain.side_effect = Exception("Unexpected error")
            app.dependency_overrides[get_domain_service] = lambda: mock_domain_service
            
            # Act
            response = client.delete("/api/v1/tenants/tenant_test/domains/domain_test_example_com")
            
            # Assert
            assert response.status_code == 500
            app.dependency_overrides.clear()

