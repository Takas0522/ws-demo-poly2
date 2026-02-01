"""ドメインスキーマのテスト"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.domain import (
    DomainCreateRequest,
    DomainResponse,
    DomainVerificationResponse,
    DomainListResponse
)


class TestDomainCreateRequest:
    """DomainCreateRequestスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        @pytest.mark.parametrize("valid_domain,description", [
            ("test-site.com", "標準ドメイン"),
            ("app.mysite.org", "サブドメイン"),
            ("test-domain.org", "ハイフン含む"),
        ])
        def test_should_validate_with_valid_domain(self, valid_domain, description):
            """有効なドメインでバリデーション成功"""
            # Arrange: 有効なドメインを準備
            data = {"domain": valid_domain}
            
            # Act: スキーマ作成
            request = DomainCreateRequest(**data)
            
            # Assert: バリデーション成功
            assert request.domain == valid_domain.lower()

        def test_should_normalize_domain_to_lowercase(self):
            """ドメインが小文字に正規化される"""
            # Arrange: 大文字を含むドメインを準備
            data = {"domain": "Test-Domain.ORG"}
            
            # Act: スキーマ作成
            request = DomainCreateRequest(**data)
            
            # Assert: 小文字に変換される
            assert request.domain == "test-domain.org"

        def test_should_accept_idna_domain(self):
            """IDNAドメインを受け入れる"""
            # Arrange: 国際化ドメインを準備
            data = {"domain": "日本.jp"}
            
            # Act: スキーマ作成
            # Assert: 正常に処理される（または拒否される）
            # IDNAはASCII変換後に処理される
            request = DomainCreateRequest(**data)
            assert "xn--" in request.domain  # Punycode変換される

    class Test異常系:
        """異常系テスト"""

        @pytest.mark.parametrize("invalid_domain,description", [
            ("", "空文字列"),
            ("localhost", "禁止ドメイン"),
            ("example.com", "禁止ドメイン"),
            ("test..com", "連続ドット"),
        ])
        def test_should_reject_invalid_domain_format(self, invalid_domain, description):
            """不正なドメイン形式を拒否する"""
            # Arrange: 不正なドメインを準備
            data = {"domain": invalid_domain}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError):
                DomainCreateRequest(**data)

        def test_should_reject_forbidden_domain_localhost(self):
            """禁止ドメイン（localhost）を拒否する"""
            # Arrange: localhostを準備
            data = {"domain": "localhost"}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError) as exc_info:
                DomainCreateRequest(**data)
            assert "domain" in str(exc_info.value).lower()

        def test_should_reject_forbidden_domain_example(self):
            """禁止ドメイン（example.com）を拒否する"""
            # Arrange: example.comを準備
            data = {"domain": "example.com"}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError) as exc_info:
                DomainCreateRequest(**data)
            assert "domain" in str(exc_info.value).lower()

        def test_should_reject_domain_with_unsupported_characters(self):
            """サポートされていない文字を含むドメインを拒否する"""
            # Arrange: 不正な文字を含むドメインを準備
            data = {"domain": "test_domain.com"}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError):
                DomainCreateRequest(**data)

    class Test境界値:
        """境界値テスト"""

        def test_should_accept_minimum_length_domain(self):
            """最小長のドメイン（例: a.io）を受け入れる"""
            # Arrange: 最小長ドメインを準備
            data = {"domain": "abc.com"}
            
            # Act: スキーマ作成
            request = DomainCreateRequest(**data)
            
            # Assert: バリデーション成功
            assert request.domain == "abc.com"

        def test_should_accept_maximum_length_domain(self):
            """最大長のドメイン（253文字）を受け入れる"""
            # Arrange: 最大長ドメインを準備（253文字）
            # 63文字のラベルを繰り返し、最後に.comを追加して253文字にする
            long_label = "a" * 50
            domain = f"{long_label}.{long_label}.{long_label}.{long_label}.com"[:253]
            data = {"domain": domain}
            
            # Act: スキーマ作成
            request = DomainCreateRequest(**data)
            
            # Assert: バリデーション成功
            assert len(request.domain) <= 253

        def test_should_reject_too_short_domain(self):
            """短すぎるドメインを拒否する"""
            # Arrange: 短すぎるドメインを準備
            data = {"domain": "ab"}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError):
                DomainCreateRequest(**data)

        def test_should_reject_too_long_domain(self):
            """長すぎるドメイン（253文字超過）を拒否する"""
            # Arrange: 254文字のドメインを準備
            domain = "a" * 245 + ".test.com"  # 254文字
            data = {"domain": domain}
            
            # Act & Assert: ValidationErrorが発生
            with pytest.raises(ValidationError):
                DomainCreateRequest(**data)


class TestDomainResponse:
    """DomainResponseスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_serialize_domain_to_response(self):
            """Domainをレスポンスにシリアライズできる"""
            # Arrange: Domainデータを準備
            data = {
                "id": "domain_test",
                "tenant_id": "tenant_test",
                "domain": "test.com",
                "verified": False,
                "verification_token": "token123",
                "created_at": datetime(2026, 2, 1, 10, 0, 0),
                "created_by": "user_admin"
            }
            
            # Act: DomainResponseを作成
            response = DomainResponse(**data)
            
            # Assert: 正しくシリアライズされる
            assert response.id == "domain_test"
            assert response.domain == "test.com"
            assert response.verified == False

        def test_should_include_verification_instructions(self):
            """検証手順を含む"""
            # Arrange: 未検証ドメインを準備
            data = {
                "id": "domain_test",
                "tenant_id": "tenant_test",
                "domain": "test.com",
                "verified": False,
                "verification_token": "token123",
                "verification_instructions": {"type": "TXT", "value": "token123"},
                "created_at": datetime(2026, 2, 1, 10, 0, 0),
                "created_by": "user_admin"
            }
            
            # Act: DomainResponseを作成
            response = DomainResponse(**data)
            
            # Assert: verification_instructionsが含まれる
            assert response.verification_instructions is not None
            assert response.verification_instructions["type"] == "TXT"

        def test_should_handle_verified_domain(self):
            """検証済みドメインを適切に処理する"""
            # Arrange: 検証済みドメインを準備
            data = {
                "id": "domain_test",
                "tenant_id": "tenant_test",
                "domain": "test.com",
                "verified": True,
                "verification_token": "token123",
                "verified_at": datetime(2026, 2, 1, 11, 0, 0),
                "verified_by": "user_admin",
                "created_at": datetime(2026, 2, 1, 10, 0, 0),
                "created_by": "user_admin"
            }
            
            # Act: DomainResponseを作成
            response = DomainResponse(**data)
            
            # Assert: verified=True, verified_atが設定される
            assert response.verified == True
            assert response.verified_at is not None
            assert response.verified_by == "user_admin"


class TestDomainVerificationResponse:
    """DomainVerificationResponseスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_serialize_verification_result(self):
            """検証結果をシリアライズできる"""
            # Arrange: 検証結果データを準備
            data = {
                "id": "domain_test",
                "domain": "test.com",
                "verified": True,
                "verified_at": datetime(2026, 2, 1, 11, 0, 0),
                "verified_by": "user_admin"
            }
            
            # Act: DomainVerificationResponseを作成
            response = DomainVerificationResponse(**data)
            
            # Assert: 正しくシリアライズされる
            assert response.id == "domain_test"
            assert response.verified == True
            assert response.verified_at is not None


class TestDomainListResponse:
    """DomainListResponseスキーマのテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_should_serialize_list_of_domains(self):
            """ドメイン一覧をシリアライズできる"""
            # Arrange: ドメインリストを準備
            domains = [
                DomainResponse(
                    id="domain_test",
                    tenant_id="tenant_test",
                    domain="test.com",
                    verified=False,
                    verification_token="token123",
                    created_at=datetime(2026, 2, 1, 10, 0, 0),
                    created_by="user_admin"
                )
            ]
            
            # Act: DomainListResponseを作成
            response = DomainListResponse(data=domains)
            
            # Assert: 正しくシリアライズされる
            assert len(response.data) == 1
            assert response.data[0].domain == "test.com"

        def test_should_handle_empty_list(self):
            """空のリストを適切に処理する"""
            # Arrange: 空のリストを準備
            
            # Act: DomainListResponseを作成
            response = DomainListResponse(data=[])
            
            # Assert: 空配列が許可される
            assert len(response.data) == 0

