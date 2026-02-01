"""
JWT認証ユーティリティのユニットテスト

テストケース:
- TC-U001 ~ TC-U009: JWT検証、特権テナント判定
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt

from app.utils.jwt import verify_token, is_privileged_tenant, TokenData
from app.config import settings

# テスト用のJWT_SECRET_KEY（64文字以上）
TEST_JWT_SECRET_KEY = "test_jwt_secret_key_for_testing_purposes_at_least_64_characters_long"

@pytest.fixture(autouse=True)
def setup_jwt_secret(monkeypatch):
    """すべてのテストで自動的にJWT_SECRET_KEYを設定"""
    monkeypatch.setattr(settings, 'JWT_SECRET_KEY', TEST_JWT_SECRET_KEY)


class TestVerifyToken:
    """verify_token関数のテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_verify_token_有効なトークン(self):
            """
            テストケース: TC-U001
            目的: 有効なJWTトークンを検証できることを検証
            前提条件: 正しい署名、有効期限内のJWT
            実行手順:
              1. 有効なJWTトークンを生成
              2. verify_token(token)を呼び出す
            期待結果:
              - TokenDataオブジェクトが返却される
              - user_id, tenant_id, usernameが正しい
            """
            # Arrange
            payload = {
                "user_id": "user_001",
                "tenant_id": "tenant_test",
                "username": "testuser",
                "roles": ["tenant-management:閲覧者"],
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

            # Act
            result = verify_token(token)

            # Assert
            assert isinstance(result, TokenData)
            assert result.user_id == "user_001"
            assert result.tenant_id == "tenant_test"
            assert result.username == "testuser"
            assert "tenant-management:閲覧者" in result.roles

        def test_verify_token_ペイロード内容検証(self):
            """
            テストケース: TC-U001-2
            目的: トークンペイロードの各フィールドが正しく抽出されることを検証
            前提条件: user_id, tenant_id, username, roles含むJWT
            実行手順:
              1. すべてのフィールドを含むJWTを生成
              2. verify_token(token)を呼び出す
            期待結果:
              - TokenDataの各フィールドがペイロードと一致
            """
            # Arrange
            payload = {
                "user_id": "user_admin_001",
                "tenant_id": "tenant_privileged",
                "username": "admin",
                "roles": ["tenant-management:全体管理者", "tenant-management:管理者"],
                "exp": datetime.utcnow() + timedelta(hours=2),
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

            # Act
            result = verify_token(token)

            # Assert
            assert result.user_id == "user_admin_001"
            assert result.tenant_id == "tenant_privileged"
            assert result.username == "admin"
            assert len(result.roles) == 2
            assert "tenant-management:全体管理者" in result.roles

    class Test異常系:
        """異常系テスト"""

        def test_verify_token_期限切れトークン(self):
            """
            テストケース: TC-U002
            目的: 期限切れトークンで401エラーが発生することを検証
            前提条件: expが過去のJWT
            実行手順:
              1. 期限切れのJWTを生成
              2. verify_token(token)を呼び出す
            期待結果:
              - HTTPException(401)が発生
              - エラーメッセージに"expired"が含まれる
            """
            # Arrange
            payload = {
                "user_id": "user_001",
                "tenant_id": "tenant_test",
                "exp": datetime.utcnow() - timedelta(hours=1),  # 1時間前に期限切れ
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            
            assert exc_info.value.status_code == 401
            assert "expired" in str(exc_info.value.detail).lower()

        def test_verify_token_不正な署名(self):
            """
            テストケース: TC-U003
            目的: 不正な署名のトークンで401エラーが発生することを検証
            前提条件: 誤った秘密鍵で署名されたJWT
            実行手順:
              1. 誤った秘密鍵で署名されたJWTを生成
              2. verify_token(token)を呼び出す
            期待結果:
              - HTTPException(401)が発生
              - エラーメッセージに"invalid"が含まれる
            """
            # Arrange
            payload = {
                "user_id": "user_001",
                "tenant_id": "tenant_test",
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            # 誤った秘密鍵で署名
            wrong_key = "wrong_secret_key_for_testing_only_" * 2
            token = jwt.encode(payload, wrong_key, algorithm=settings.JWT_ALGORITHM)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            
            assert exc_info.value.status_code == 401
            assert "invalid" in str(exc_info.value.detail).lower()

        def test_verify_token_不正な形式(self):
            """
            テストケース: TC-U004
            目的: 不正な形式のトークンで401エラーが発生することを検証
            前提条件: JWT形式でない文字列
            実行手順:
              1. "invalid_token_format"を渡す
              2. verify_token(token)を呼び出す
            期待結果:
              - HTTPException(401)が発生
            """
            # Arrange
            invalid_token = "invalid_token_format"

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                verify_token(invalid_token)
            
            assert exc_info.value.status_code == 401

        def test_verify_token_空トークン(self):
            """
            テストケース: TC-U005
            目的: 空文字列で401エラーが発生することを検証
            前提条件: 空文字列
            実行手順:
              1. ""を渡す
              2. verify_token(token)を呼び出す
            期待結果:
              - HTTPException(401)が発生
              - エラーメッセージに"required"が含まれる
            """
            # Arrange
            empty_token = ""

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                verify_token(empty_token)
            
            assert exc_info.value.status_code == 401
            assert "required" in str(exc_info.value.detail).lower()

        def test_verify_token_必須フィールド欠如_user_id(self):
            """
            テストケース: TC-U006
            目的: user_id欠如時に401エラーが発生することを検証
            前提条件: user_idを含まないJWT
            実行手順:
              1. user_idを含まないJWTを生成
              2. verify_token(token)を呼び出す
            期待結果:
              - HTTPException(401)が発生
              - エラーメッセージに"missing required fields"が含まれる
            """
            # Arrange
            payload = {
                "tenant_id": "tenant_test",  # user_idなし
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            
            assert exc_info.value.status_code == 401
            assert "missing required fields" in str(exc_info.value.detail).lower()

        def test_verify_token_必須フィールド欠如_tenant_id(self):
            """
            テストケース: TC-U006-2
            目的: tenant_id欠如時に401エラーが発生することを検証
            前提条件: tenant_idを含まないJWT
            実行手順:
              1. tenant_idを含まないJWTを生成
              2. verify_token(token)を呼び出す
            期待結果:
              - HTTPException(401)が発生
              - エラーメッセージに"missing required fields"が含まれる
            """
            # Arrange
            payload = {
                "user_id": "user_001",  # tenant_idなし
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            
            assert exc_info.value.status_code == 401
            assert "missing required fields" in str(exc_info.value.detail).lower()


class TestIsPrivilegedTenant:
    """is_privileged_tenant関数のテスト"""

    class Test正常系:
        """正常系テスト"""

        def test_is_privileged_tenant_特権判定(self):
            """
            テストケース: TC-U007
            目的: 特権テナントIDでTrueが返却されることを検証
            前提条件: PRIVILEGED_TENANT_IDSに含まれるID
            実行手順:
              1. is_privileged_tenant("tenant_privileged")を呼び出す
            期待結果:
              - Trueが返却される
            """
            # Arrange & Act
            result = is_privileged_tenant("tenant_privileged")

            # Assert
            assert result is True

        def test_is_privileged_tenant_一般判定(self):
            """
            テストケース: TC-U008
            目的: 一般テナントIDでFalseが返却されることを検証
            前提条件: PRIVILEGED_TENANT_IDSに含まれないID
            実行手順:
              1. is_privileged_tenant("tenant-acme")を呼び出す
            期待結果:
              - Falseが返却される
            """
            # Arrange & Act
            result = is_privileged_tenant("tenant-acme")

            # Assert
            assert result is False

        def test_is_privileged_tenant_他のテナントID(self):
            """
            テストケース: TC-U008-2
            目的: 様々な一般テナントIDでFalseが返却されることを検証
            前提条件: PRIVILEGED_TENANT_IDSに含まれないID
            実行手順:
              1. 各一般テナントIDでis_privileged_tenant()を呼び出す
            期待結果:
              - すべてFalseが返却される
            """
            # Arrange
            regular_tenant_ids = [
                "tenant-acme",
                "tenant_test",
                "tenant-example-corp",
                "some_random_tenant",
            ]

            # Act & Assert
            for tenant_id in regular_tenant_ids:
                result = is_privileged_tenant(tenant_id)
                assert result is False, f"Expected False for {tenant_id}"

    class Test境界値:
        """境界値テスト"""

        def test_is_privileged_tenant_空文字列(self):
            """
            テストケース: TC-U009
            目的: 空文字列でFalseが返却されることを検証
            前提条件: 空文字列
            実行手順:
              1. is_privileged_tenant("")を呼び出す
            期待結果:
              - Falseが返却される
            """
            # Arrange & Act
            result = is_privileged_tenant("")

            # Assert
            assert result is False

        def test_is_privileged_tenant_None(self):
            """
            テストケース: TC-U009-2
            目的: NoneでFalseが返却されることを検証
            前提条件: None
            実行手順:
              1. is_privileged_tenant(None)を呼び出す
            期待結果:
              - Falseが返却される(または例外が発生しない)
            """
            # Arrange & Act
            result = is_privileged_tenant(None)

            # Assert
            assert result is False


class TestTokenData:
    """TokenDataクラスのテスト"""

    def test_token_data_初期化(self):
        """
        テストケース: TC-U-Extra-001
        目的: TokenDataが正しく初期化されることを検証
        前提条件: 必須フィールドを指定
        実行手順:
          1. TokenDataオブジェクトを作成
        期待結果:
          - user_id, tenant_idが設定される
          - rolesがデフォルト[]
        """
        # Arrange & Act
        token_data = TokenData(
            user_id="user_001",
            tenant_id="tenant_test",
        )

        # Assert
        assert token_data.user_id == "user_001"
        assert token_data.tenant_id == "tenant_test"
        assert token_data.username is None
        assert token_data.roles == []

    def test_token_data_全フィールド指定(self):
        """
        テストケース: TC-U-Extra-002
        目的: TokenDataの全フィールドを指定できることを検証
        前提条件: すべてのフィールドを指定
        実行手順:
          1. すべてのフィールドを指定してTokenDataオブジェクトを作成
        期待結果:
          - すべてのフィールドが設定される
        """
        # Arrange & Act
        token_data = TokenData(
            user_id="user_admin_001",
            tenant_id="tenant_privileged",
            username="admin",
            roles=["tenant-management:全体管理者", "tenant-management:管理者"],
        )

        # Assert
        assert token_data.user_id == "user_admin_001"
        assert token_data.tenant_id == "tenant_privileged"
        assert token_data.username == "admin"
        assert len(token_data.roles) == 2
        assert "tenant-management:全体管理者" in token_data.roles
        assert "tenant-management:管理者" in token_data.roles
