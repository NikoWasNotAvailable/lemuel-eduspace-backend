from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.models.user import User, UserRole
from app.models.admin_login_log import AdminLoginLog
from app.schemas.admin_auth import AdminLoginRequest, AdminLogoutRequest
from app.core.security import verify_password, create_access_token
from fastapi import HTTPException, status, Request
from datetime import datetime
from jose import jwt, JWTError
from app.core.config import settings

class AdminAuthService:
    """Service layer for admin authentication and logging."""
    
    @staticmethod
    async def authenticate_admin(
        db: AsyncSession, 
        login_data: AdminLoginRequest,
        request: Optional[Request] = None
    ) -> tuple[User, AdminLoginLog]:
        """Authenticate admin user and create login log."""
        
        # Find admin user by email
        query = select(User).where(
            and_(
                User.email == login_data.email,
                User.role == UserRole.admin
            )
        )
        result = await db.execute(query)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin account not found with this email",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password (admin passwords are hashed)
        if not verify_password(login_data.password, admin_user.password, is_admin=True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token with admin info
        token_data = {
            "sub": str(admin_user.id),
            "admin_name": login_data.name,
            "role": "admin"
        }
        access_token = create_access_token(data=token_data)
        
        # Get client information
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Create login log
        login_log = AdminLoginLog(
            admin_user_id=admin_user.id,
            admin_name=login_data.name,
            admin_email=login_data.email,
            session_token=access_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(login_log)
        await db.commit()
        await db.refresh(login_log)
        
        return admin_user, login_log
    
    @staticmethod
    async def logout_admin(
        db: AsyncSession, 
        logout_data: AdminLogoutRequest
    ) -> bool:
        """Log admin logout."""
        
        # Update logout time for the session
        query = update(AdminLoginLog).where(
            AdminLoginLog.id == logout_data.session_id
        ).values(logout_time=datetime.utcnow())
        
        result = await db.execute(query)
        await db.commit()
        
        return result.rowcount > 0
    
    @staticmethod
    async def get_admin_login_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        admin_user_id: Optional[int] = None,
        admin_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AdminLoginLog]:
        """Get admin login logs with filters."""
        
        query = select(AdminLoginLog)
        
        if admin_user_id:
            query = query.where(AdminLoginLog.admin_user_id == admin_user_id)
        
        if admin_name:
            query = query.where(AdminLoginLog.admin_name.ilike(f"%{admin_name}%"))
        
        if start_date:
            query = query.where(AdminLoginLog.login_time >= start_date)
        
        if end_date:
            query = query.where(AdminLoginLog.login_time <= end_date)
        
        query = query.order_by(AdminLoginLog.login_time.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_active_admin_sessions(db: AsyncSession) -> List[AdminLoginLog]:
        """Get currently active admin sessions (not logged out)."""
        
        query = select(AdminLoginLog).where(
            AdminLoginLog.logout_time.is_(None)
        ).order_by(AdminLoginLog.login_time.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def verify_admin_session(db: AsyncSession, token: str) -> Optional[AdminLoginLog]:
        """Verify if admin session is still active."""
        
        try:
            # Decode token to get session info
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            # Find active session with this token
            query = select(AdminLoginLog).where(
                and_(
                    AdminLoginLog.session_token == token,
                    AdminLoginLog.logout_time.is_(None)
                )
            )
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except JWTError:
            return None
    
    @staticmethod
    async def force_logout_session(db: AsyncSession, session_id: int) -> bool:
        """Force logout a specific admin session."""
        
        query = update(AdminLoginLog).where(
            AdminLoginLog.id == session_id
        ).values(logout_time=datetime.utcnow())
        
        result = await db.execute(query)
        await db.commit()
        
        return result.rowcount > 0