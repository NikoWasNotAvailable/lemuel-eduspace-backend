# Parent Access Module Documentation

## Overview

Parent access is implemented as a simple extension of the student user system. Instead of having separate parent accounts, parents can access their child's student account using a secondary password field (`parent_password`). This approach:

- Avoids duplicate accounts
- Keeps the relationship simple (same account, different password)
- Allows frontend to differentiate via the `parent_access` flag in login response/token

## How It Works

1. **Student registers** with a regular account (NIS/email + password)
2. **Student sets parent password** via `/me/parent-password/set` endpoint
3. **Parent logs in** using the student's NIS/email but with the `parent_password`
4. **Token includes** `parent_access: true` claim for frontend differentiation

## Database Schema

The parent password is stored directly on the `users` table:

```sql
CREATE TABLE `users` (
  ...
  `parent_password` VARCHAR(255) DEFAULT NULL,  -- Parent password for student accounts
  ...
);
```

## API Endpoints

### Parent Authentication
- `POST /api/v1/users/login/parent` - Parent login using student identifier + parent password

### Parent Password Management (Student Self-Service)
- `POST /api/v1/users/me/parent-password/set` - Set parent password (requires student password verification)
- `POST /api/v1/users/me/parent-password/change` - Change parent password (requires current parent password)
- `DELETE /api/v1/users/me/parent-password` - Remove parent password (requires student password)

## Authentication Flow

### Parent Login Request
```json
POST /api/v1/users/login/parent
{
    "identifier": "STU001",       // Student's NIS or email
    "password": "parentpass123"   // Parent's password (not the student password)
}
```

### Parent Login Response
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": { ... student data ... },
    "parent_access": true          // Indicates this is a parent session
}
```

The JWT token also includes `"parent_access": true` in its claims.

## Setting Up Parent Access

### 1. Student Sets Parent Password
```json
POST /api/v1/users/me/parent-password/set
Authorization: Bearer <student_token>
{
    "student_password": "studentpass123",  // Verify student ownership
    "parent_password": "parentpass123"     // New parent password
}
```

### 2. Parent Logs In
```json
POST /api/v1/users/login/parent
{
    "identifier": "STU001",
    "password": "parentpass123"
}
```

## Frontend Integration

The frontend can differentiate between student and parent sessions by:

1. **Login endpoint used**: `/login/student` vs `/login/parent`
2. **Response field**: `parent_access: true` in login response
3. **JWT claim**: `parent_access: true` in decoded token

Store this information in your auth state to show appropriate UI/features.

## Security Considerations

1. Parent passwords use the same bcrypt hashing as regular passwords
2. Setting parent password requires student password verification
3. Parent sessions are clearly marked in both response and token
4. Parents access the same student account but frontend can restrict actions based on `parent_access` flag
5. Minimum 8 character password requirement applies to parent passwords

This will:
1. Create a test student
2. Create a parent for that student
3. Test parent authentication with student NIS + parent password
4. Test parent authentication with student email + parent password