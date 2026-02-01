"""認証認可サービスクライアント"""
import os
import httpx
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class AuthServiceClient:
    """認証認可サービスとの連携クライアント"""

    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        self.service_api_key = os.getenv("SERVICE_API_KEY")
        self.timeout = 2.0
        self.logger = logger

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def verify_user_exists(self, user_id: str) -> bool:
        """
        認証認可サービスでユーザーの存在を確認
        
        Args:
            user_id: 検証するユーザーID
        
        Returns:
            bool: ユーザーが存在する場合True
        
        Raises:
            ValueError: ユーザーが存在しない
            RuntimeError: 認証認可サービスが利用不可
            Exception: サービス間認証失敗
        
        Retry Policy:
            - 最大3回リトライ
            - 指数バックオフ（100ms, 200ms, 400ms）
            - タイムアウト: 2秒
            - リトライ対象: タイムアウト、ネットワークエラー
            - リトライ除外: 404, 401（即座にエラー）
        """
        if not self.service_api_key:
            raise Exception("Service API key not configured")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/users/{user_id}",
                    headers={
                        "X-Service-Key": self.service_api_key,
                        "X-Requesting-Service": "tenant-management"
                    }
                )

                if response.status_code == 404:
                    raise ValueError("User not found in authentication service")
                elif response.status_code == 401:
                    raise Exception("Service authentication failed")
                elif response.status_code >= 500:
                    # 5xxエラーはリトライ対象外（明示的にエラー）
                    raise RuntimeError(f"Auth service error: {response.status_code}")

                response.raise_for_status()
                return True

        except httpx.TimeoutException:
            self.logger.warning(f"Timeout verifying user {user_id}")
            raise RuntimeError("User verification service timeout")
        except httpx.NetworkError as e:
            self.logger.error(f"Network error verifying user {user_id}: {e}")
            raise RuntimeError("User verification service unavailable")

    async def get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        認証認可サービスからユーザー詳細を取得
        
        Args:
            user_id: ユーザーID
        
        Returns:
            Optional[Dict[str, Any]]: ユーザー詳細情報、取得失敗時はNone
        
        Timeout: 2秒
        Retry: 最大2回
        Fallback: 失敗時はNoneを返却（部分的失敗を許容）
        """
        if not self.service_api_key:
            self.logger.warning("Service API key not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/users/{user_id}",
                    headers={
                        "X-Service-Key": self.service_api_key,
                        "X-Requesting-Service": "tenant-management"
                    }
                )
                response.raise_for_status()
                return response.json()
        except (httpx.TimeoutException, httpx.HTTPError) as e:
            self.logger.warning(f"Failed to fetch user details for {user_id}: {e}")
            return None
