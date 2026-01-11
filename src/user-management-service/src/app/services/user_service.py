"""User Management Service - User Service"""
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from app.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserSearchCriteria,
    PaginationParams,
    PaginatedResponse,
    ErrorCode
)
from app.repositories import user_repository, audit_repository
from app.schemas.audit import AuditAction, CreateAuditLogRequest, AuditChangeSchema
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class UserService:
    """User service for business logic"""
    
    def __init__(self):
        self.user_repo = user_repository
        self.audit_repo = audit_repository
    
    async def create_user(
        self,
        request: CreateUserRequest,
        created_by: str
    ) -> UserResponse:
        """Create a new user"""
        # Check if user with same email already exists
        existing_user = await self.user_repo.get_by_email(
            request.email,
            request.tenant_id
        )
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": ErrorCode.CONFLICT,
                    "message": "User with this email already exists"
                }
            )
        
        # Create user data
        user_id = str(uuid4())
        now = datetime.utcnow()
        user_data = {
            "id": user_id,
            "tenantId": request.tenant_id,
            "email": request.email,
            "username": request.username,
            "firstName": request.first_name,
            "lastName": request.last_name,
            "profile": request.profile.model_dump() if request.profile else {},
            "status": request.status.value if request.status else "ACTIVE",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "createdBy": created_by,
            "updatedBy": created_by
        }
        
        # Save to database
        created_user = await self.user_repo.create(user_data)
        
        # Create audit log
        await self._create_audit_log(
            tenant_id=request.tenant_id,
            entity_id=user_id,
            action=AuditAction.CREATE,
            performed_by=created_by
        )
        
        return self._map_to_response(created_user)
    
    async def get_user(self, user_id: str, tenant_id: str) -> UserResponse:
        """Get user by ID"""
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "User not found"
                }
            )
        
        # Verify tenant ID matches
        if user.get("tenantId") != tenant_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": ErrorCode.TENANT_MISMATCH,
                    "message": "Tenant ID mismatch"
                }
            )
        
        return self._map_to_response(user)
    
    async def update_user(
        self,
        user_id: str,
        tenant_id: str,
        request: UpdateUserRequest,
        updated_by: str
    ) -> UserResponse:
        """Update user"""
        # Get existing user
        existing_user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "User not found"
                }
            )
        
        # Verify tenant ID matches
        if existing_user.get("tenantId") != tenant_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": ErrorCode.TENANT_MISMATCH,
                    "message": "Tenant ID mismatch"
                }
            )
        
        # Track changes for audit log
        changes = []
        update_data = {"updatedBy": updated_by}
        
        if request.email is not None and request.email != existing_user.get("email"):
            changes.append(AuditChangeSchema(
                field="email",
                old_value=existing_user.get("email"),
                new_value=request.email
            ))
            update_data["email"] = request.email
        
        if request.username is not None and request.username != existing_user.get("username"):
            changes.append(AuditChangeSchema(
                field="username",
                old_value=existing_user.get("username"),
                new_value=request.username
            ))
            update_data["username"] = request.username
        
        if request.first_name is not None and request.first_name != existing_user.get("firstName"):
            changes.append(AuditChangeSchema(
                field="firstName",
                old_value=existing_user.get("firstName"),
                new_value=request.first_name
            ))
            update_data["firstName"] = request.first_name
        
        if request.last_name is not None and request.last_name != existing_user.get("lastName"):
            changes.append(AuditChangeSchema(
                field="lastName",
                old_value=existing_user.get("lastName"),
                new_value=request.last_name
            ))
            update_data["lastName"] = request.last_name
        
        if request.profile is not None:
            update_data["profile"] = request.profile.model_dump()
            changes.append(AuditChangeSchema(
                field="profile",
                old_value=existing_user.get("profile"),
                new_value=request.profile.model_dump()
            ))
        
        if request.status is not None and request.status.value != existing_user.get("status"):
            changes.append(AuditChangeSchema(
                field="status",
                old_value=existing_user.get("status"),
                new_value=request.status.value
            ))
            update_data["status"] = request.status.value
        
        # Update user
        updated_user = await self.user_repo.update(user_id, tenant_id, update_data)
        
        # Create audit log
        await self._create_audit_log(
            tenant_id=tenant_id,
            entity_id=user_id,
            action=AuditAction.UPDATE,
            performed_by=updated_by,
            changes=[change.model_dump() for change in changes]
        )
        
        return self._map_to_response(updated_user)
    
    async def delete_user(
        self,
        user_id: str,
        tenant_id: str,
        deleted_by: str
    ) -> bool:
        """Delete user (soft delete)"""
        # Verify user exists and tenant matches
        existing_user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "User not found"
                }
            )
        
        if existing_user.get("tenantId") != tenant_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": ErrorCode.TENANT_MISMATCH,
                    "message": "Tenant ID mismatch"
                }
            )
        
        # Soft delete
        success = await self.user_repo.delete(user_id, tenant_id)
        
        if success:
            # Create audit log
            await self._create_audit_log(
                tenant_id=tenant_id,
                entity_id=user_id,
                action=AuditAction.DELETE,
                performed_by=deleted_by
            )
        
        return success
    
    async def search_users(
        self,
        criteria: UserSearchCriteria,
        pagination: PaginationParams
    ) -> PaginatedResponse:
        """Search users with pagination"""
        items, total_count = await self.user_repo.search(criteria, pagination)
        
        # Map to response
        user_responses = [self._map_to_response(item) for item in items]
        
        # Calculate pagination metadata
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        has_next_page = pagination.page_number < total_pages
        has_previous_page = pagination.page_number > 1
        
        return PaginatedResponse(
            items=user_responses,
            total_count=total_count,
            page_number=pagination.page_number,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page
        )
    
    def _map_to_response(self, user_data: dict) -> UserResponse:
        """Map database user to response schema"""
        from app.schemas.user import UserProfileSchema
        
        profile_data = user_data.get("profile", {})
        profile = UserProfileSchema(**profile_data) if profile_data else UserProfileSchema()
        
        return UserResponse(
            id=user_data["id"],
            tenant_id=user_data["tenantId"],
            email=user_data["email"],
            username=user_data["username"],
            first_name=user_data["firstName"],
            last_name=user_data["lastName"],
            profile=profile,
            status=user_data["status"],
            created_at=datetime.fromisoformat(user_data["createdAt"]),
            updated_at=datetime.fromisoformat(user_data["updatedAt"]),
            created_by=user_data["createdBy"],
            updated_by=user_data["updatedBy"]
        )
    
    async def _create_audit_log(
        self,
        tenant_id: str,
        entity_id: str,
        action: AuditAction,
        performed_by: str,
        changes: Optional[List[dict]] = None
    ):
        """Create an audit log entry"""
        audit_data = {
            "id": str(uuid4()),
            "tenantId": tenant_id,
            "entityType": "User",
            "entityId": entity_id,
            "action": action.value,
            "performedBy": performed_by,
            "performedAt": datetime.utcnow().isoformat(),
            "changes": changes or [],
            "metadata": {}
        }
        
        try:
            await self.audit_repo.create(audit_data)
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            # Don't fail the main operation if audit logging fails


user_service = UserService()
