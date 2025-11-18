# Parent Module Documentation

## Overview

The parent module is a simple extension of the user system that adds a separate password field for parents. Parents use the student's existing credentials (NIS or email) but with their own password. This allows parents to access student-related information without sharing the actual student password.

## Database Schema

### Parents Table

```sql
CREATE TABLE `parents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL UNIQUE,                   -- FK to users table (must be student, one-to-one)
  `parent_password` VARCHAR(255) NOT NULL,            -- Parent's separate password hash
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`student_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_student_id` (`student_id`)
);
```

## API Endpoints

### Parent Authentication
- `POST /api/v1/parents/login` - Parent login (can use parent email or student NIS)

### Parent Management (Admin Only)
- `POST /api/v1/parents/register` - Register new parent for student
- `GET /api/v1/parents/` - Get all parents
- `GET /api/v1/parents/{parent_id}` - Get parent by ID
- `DELETE /api/v1/parents/{parent_id}` - Delete parent record
- `GET /api/v1/parents/student/{student_id}` - Get parent for specific student

### Parent Self-Service
- `GET /api/v1/parents/me` - Get student information (parent access)
- `POST /api/v1/parents/me/change-password` - Change parent password

## Authentication

Parents authenticate using:
1. Student's NIS (Nomor Induk Siswa) + Parent password
2. Student's email + Parent password

The system creates JWT tokens with the format `parent_{parent_id}` in the subject field to distinguish parent tokens from user tokens.

## Key Features

1. **Simple Extension**: Just adds a password field to existing student records
2. **One-to-One Relationship**: Each student can have one parent record
3. **Reuse Student Credentials**: Parents login with student's NIS/email but their own password
4. **Security**: Uses the same institution-requested password handling as the main user system
5. **Admin Management**: Admins can create and delete parent records
6. **Self-Service**: Parents can change their password and view student information

## Usage Examples

### Creating a Parent Record (Admin)

```python
parent_data = ParentCreate(
    student_id=123,
    parent_password="securepass123"
)
```

### Parent Login

```python
# Login with student NIS + parent password
login_data = ParentLogin(
    identifier="STU001",  # Student's NIS
    password="securepass123"  # Parent's password
)

# Or login with student email + parent password
login_data = ParentLogin(
    identifier="student@school.com",  # Student's email
    password="securepass123"  # Parent's password
)
```



## Security Considerations

1. Parent passwords are stored using the same secure hashing mechanism as user passwords
2. Parent authentication generates separate JWT tokens to maintain security boundaries
3. Parents can only access information related to their linked student
4. All parent management operations require admin privileges
5. Parents use student identifiers (NIS/email) but cannot change student information

## Testing

Run the test script to verify parent functionality:

```bash
python test_parent.py
```

This will:
1. Create a test student
2. Create a parent for that student
3. Test parent authentication with student NIS + parent password
4. Test parent authentication with student email + parent password