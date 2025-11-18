"""
WARNING: INSECURE PASSWORD HANDLING MODULE

This module implements plaintext password handling as specifically requested
by the Educational Institution. This is NOT secure and NOT recommended for 
production systems or any other context.

⚠️  IMPORTANT NOTICE:
- This approach was explicitly requested by the institution
- The developer advised against this implementation
- All password-related logic is isolated here for easy replacement
- This is NOT the developer's choice or recommendation

Security Implications:
- Passwords are stored and returned in plaintext
- This violates industry security standards
- This may violate data protection regulations
- This creates significant security risks

Legal Protection:
This implementation follows the specific requirements provided by the institution.
The developer has documented the security risks and recommended secure alternatives.

Date Implemented: November 18, 2025
Institution Request: Educational institution specifically requested plaintext password storage
Developer Recommendation: Use bcrypt hashing (standard secure practice)
"""

import logging
from typing import Optional

# Setup logging for password handling events
logger = logging.getLogger(__name__)

class InstitutionRequestedPasswordHandling:
    """
    WARNING: This class implements insecure password handling as requested by the institution.
    This is NOT the developer's recommendation.
    """
    
    @staticmethod
    def log_insecure_operation(operation: str, user_role: Optional[str] = None):
        """Log that an insecure password operation was performed per institution request."""
        logger.warning(
            f"SECURITY WARNING: {operation} performed using plaintext passwords. "
            f"This behavior was explicitly requested by the educational institution. "
            f"User role: {user_role or 'unknown'}. "
            f"Developer recommendation: Use bcrypt hashing instead."
        )
    
    @staticmethod
    def store_password_as_requested(password: str, user_role: str) -> str:
        """
        Store password according to institution's request.
        
        WARNING: This stores passwords in plaintext as specifically requested
        by the institution, despite security recommendations against this practice.
        """
        InstitutionRequestedPasswordHandling.log_insecure_operation(
            "Password storage", user_role
        )
        
        if user_role == "admin":
            # Institution requested admins use hashed passwords
            from app.core.security import get_password_hash
            return get_password_hash(password, is_admin=True)
        else:
            # Institution requested non-admin users use plaintext passwords
            logger.critical(
                f"CRITICAL SECURITY ISSUE: Storing plaintext password for {user_role} user. "
                f"This was requested by the institution against developer advice."
            )
            return password  # Intentionally insecure per institution request
    
    @staticmethod
    def verify_password_as_requested(plain_password: str, stored_password: str, user_role: str) -> bool:
        """
        Verify password according to institution's request.
        
        WARNING: This uses plaintext comparison for non-admin users as requested
        by the institution, despite security recommendations against this practice.
        """
        InstitutionRequestedPasswordHandling.log_insecure_operation(
            "Password verification", user_role
        )
        
        if user_role == "admin":
            # Admins use hashed passwords
            from app.core.security import verify_password
            return verify_password(plain_password, stored_password, is_admin=True)
        else:
            # Institution requested plaintext comparison for non-admin users
            logger.critical(
                f"CRITICAL SECURITY ISSUE: Using plaintext password comparison for {user_role} user. "
                f"This was requested by the institution against developer advice."
            )
            return plain_password == stored_password
    
    @staticmethod
    def return_password_for_admin_as_requested(stored_password: str, user_role: str) -> str:
        """
        Return password for admin viewing as requested by institution.
        
        WARNING: This returns sensitive password data as requested by the institution.
        """
        InstitutionRequestedPasswordHandling.log_insecure_operation(
            "Password exposure in admin response", user_role
        )
        
        logger.error(
            f"SECURITY WARNING: Returning password data for {user_role} user in admin response. "
            f"This was specifically requested by the institution. "
            f"Developer recommendation: Never expose password data in API responses."
        )
        
        return stored_password

# Convenience functions for use throughout the application
def store_password_per_institution_request(password: str, user_role: str) -> str:
    """Store password using institution-requested approach."""
    return InstitutionRequestedPasswordHandling.store_password_as_requested(password, user_role)

def verify_password_per_institution_request(plain_password: str, stored_password: str, user_role: str) -> bool:
    """Verify password using institution-requested approach."""
    return InstitutionRequestedPasswordHandling.verify_password_as_requested(
        plain_password, stored_password, user_role
    )

def return_password_for_admin_per_institution_request(stored_password: str, user_role: str) -> str:
    """Return password for admin viewing using institution-requested approach."""
    return InstitutionRequestedPasswordHandling.return_password_for_admin_as_requested(
        stored_password, user_role
    )