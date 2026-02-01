"""ドメインスキーマ"""
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class DomainCreateRequest(BaseModel):
    """ドメイン作成リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    domain: str = Field(..., min_length=3, max_length=253)

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """ドメイン形式の検証（ホモグラフ攻撃対策含む）"""
        # Unicode正規化（ホモグラフ攻撃対策）
        try:
            v_normalized = v.encode('idna').decode('ascii')
        except (UnicodeError, UnicodeDecodeError):
            raise ValueError('Invalid domain format: contains unsupported characters')
        
        # ドメイン名の正規表現パターン
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(pattern, v_normalized):
            raise ValueError('Invalid domain format')
        
        # 禁止ドメインリストチェック
        forbidden_domains = ['localhost', 'local', '127.0.0.1', 'internal', 'example.com', 'test.local']
        v_lower = v_normalized.lower()
        if any(forbidden in v_lower for forbidden in forbidden_domains):
            raise ValueError('Forbidden domain')
        
        return v_lower


class DomainResponse(BaseModel):
    """ドメインレスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    tenant_id: str = Field(..., alias="tenantId")
    domain: str
    verified: bool
    verification_token: Optional[str] = Field(None, alias="verificationToken")
    verification_instructions: Optional[Dict[str, str]] = Field(None, alias="verificationInstructions")
    verified_at: Optional[datetime] = Field(None, alias="verifiedAt")
    verified_by: Optional[str] = Field(None, alias="verifiedBy")
    created_at: datetime = Field(..., alias="createdAt")
    created_by: str = Field(..., alias="createdBy")


class DomainVerificationResponse(BaseModel):
    """ドメイン検証レスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    domain: str
    verified: bool
    verified_at: Optional[datetime] = Field(None, alias="verifiedAt")
    verified_by: Optional[str] = Field(None, alias="verifiedBy")


class DomainListResponse(BaseModel):
    """ドメイン一覧レスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    data: list[DomainResponse]
