# Lemuel EduSpace Backend

A FastAPI backend for an educational management system with user authentication and CRUD operations.

## Features

- **User Management**: Complete CRUD operations for users with profile pictures
- **Authentication**: JWT-based authentication with role-based access control
- **Role-based Access**: Support for admin, teacher, student, parent, and student_parent roles
- **Class & Subject Management**: Organize educational content with classes and subjects
- **Teacher-Subject Assignment**: Assign teachers to specific subjects
- **Student Enrollment**: Manage student enrollment in classes
- **Session Management**: Create and manage learning sessions with attachments
- **File Management**: Upload and manage session attachments (PDFs, documents, media)
- **Notification System**: Create and manage notifications with user targeting
- **Admin Logging**: Track admin authentication sessions
- **Profile Pictures**: Upload and manage user profile pictures
- **Modular Architecture**: Clean MVC pattern with services layer
- **Async Database**: SQLAlchemy with async MySQL support
- **Input Validation**: Pydantic schemas for request/response validation
- **Security**: Password hashing with bcrypt and file upload security

## Project Structure

```
lemuel-eduspace-backend/
├── app/
│   ├── __init__.py
│   ├── controllers/              # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── user_controller.py
│   │   ├── class_controller.py
│   │   ├── subject_controller.py
│   │   ├── teacher_subject_controller.py
│   │   ├── student_class_controller.py
│   │   ├── admin_auth_controller.py
│   │   ├── notification_controller.py
│   │   ├── user_notification_controller.py
│   │   ├── session_controller.py
│   │   └── session_attachment_controller.py
│   ├── core/                     # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication dependencies
│   │   ├── config.py            # Application settings
│   │   ├── database.py          # Database configuration
│   │   └── security.py          # Security utilities
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── classroom.py
│   │   ├── subject.py
│   │   ├── teacher_subject.py
│   │   ├── student_class.py
│   │   ├── admin_login_log.py
│   │   ├── notification.py
│   │   ├── user_notification.py
│   │   ├── session.py
│   │   └── session_attachment.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── classroom.py
│   │   ├── subject.py
│   │   ├── teacher_subject.py
│   │   ├── student_class.py
│   │   ├── notification.py
│   │   ├── user_notification.py
│   │   ├── session.py
│   │   └── session_attachment.py
│   └── services/                 # Business logic layer
│       ├── __init__.py
│       ├── user_service.py
│       ├── class_service.py
│       ├── subject_service.py
│       ├── teacher_subject_service.py
│       ├── student_class_service.py
│       ├── notification_service.py
│       ├── user_notification_service.py
│       ├── session_service.py
│       ├── session_attachment_service.py
│       └── profile_picture_service.py
├── uploads/                      # File storage directory
│   ├── profile_pictures/         # User profile pictures
│   └── session_attachments/      # Session file attachments
├── main.py                       # FastAPI application entry point
├── init_db.py                   # Database initialization script
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- MySQL 8.0+
- pip (Python package manager)

### 2. Installation

1. **Clone the repository** (if applicable)
   ```bash
   git clone <repository-url>
   cd lemuel-eduspace-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\\Scripts\\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   copy .env.example .env  # Windows
   cp .env.example .env    # macOS/Linux
   
   # Edit .env file with your configuration
   # Update database credentials, secret key, etc.
   ```

### 3. Database Setup

1. **Create MySQL database**
   ```sql
   CREATE DATABASE eduspace CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Initialize database tables**
   ```bash
   python init_db.py
   ```

### 4. Running the Application

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - User login
- `POST /api/v1/admin-auth/login` - Admin login with logging

### User Management
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user
- `POST /api/v1/users/me/change-password` - Change password
- `POST /api/v1/users/profile-picture` - Upload profile picture
- `GET /api/v1/users/profile-picture/{filename}` - Get profile picture
- `DELETE /api/v1/users/profile-picture` - Delete profile picture

### Admin Operations (Users)
- `GET /api/v1/users/` - List all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID (admin only)
- `PUT /api/v1/users/{user_id}` - Update user (admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)
- `POST /api/v1/users/{user_id}/profile-picture` - Upload user profile picture (admin only)

### Class Management
- `POST /api/v1/classes/` - Create class (admin/teacher)
- `GET /api/v1/classes/` - List classes
- `GET /api/v1/classes/{class_id}` - Get class by ID
- `PUT /api/v1/classes/{class_id}` - Update class (admin/teacher)
- `DELETE /api/v1/classes/{class_id}` - Delete class (admin/teacher)

### Subject Management
- `POST /api/v1/subjects/` - Create subject (admin/teacher)
- `GET /api/v1/subjects/` - List subjects
- `GET /api/v1/subjects/{subject_id}` - Get subject by ID
- `PUT /api/v1/subjects/{subject_id}` - Update subject (admin/teacher)
- `DELETE /api/v1/subjects/{subject_id}` - Delete subject (admin/teacher)

### Teacher-Subject Assignment
- `POST /api/v1/teacher-subjects/` - Assign teacher to subject (admin)
- `GET /api/v1/teacher-subjects/` - List teacher-subject assignments
- `GET /api/v1/teacher-subjects/teacher/{teacher_id}` - Get teacher's subjects
- `DELETE /api/v1/teacher-subjects/{assignment_id}` - Remove assignment (admin)

### Student Enrollment
- `POST /api/v1/student-classes/` - Enroll student in class (admin/teacher)
- `GET /api/v1/student-classes/` - List student enrollments
- `GET /api/v1/student-classes/student/{student_id}` - Get student's classes
- `DELETE /api/v1/student-classes/{enrollment_id}` - Remove enrollment (admin/teacher)

### Session Management
- `POST /api/v1/sessions/` - Create session (admin/teacher)
- `GET /api/v1/sessions/` - List sessions with filters
- `GET /api/v1/sessions/upcoming` - Get upcoming sessions
- `GET /api/v1/sessions/stats` - Session statistics (admin/teacher)
- `GET /api/v1/sessions/subject/{subject_id}` - Sessions by subject
- `GET /api/v1/sessions/{session_id}` - Get session with attachments
- `PUT /api/v1/sessions/{session_id}` - Update session (admin/teacher)
- `DELETE /api/v1/sessions/{session_id}` - Delete session (admin/teacher)

### Session Attachments
- `POST /api/v1/session-attachments/upload` - Upload file to session (admin/teacher)
- `POST /api/v1/session-attachments/bulk-upload` - Upload multiple files (admin/teacher)
- `GET /api/v1/session-attachments/session/{session_id}` - List session attachments
- `GET /api/v1/session-attachments/{attachment_id}` - Get attachment info
- `GET /api/v1/session-attachments/{attachment_id}/download` - Download file
- `PUT /api/v1/session-attachments/{attachment_id}` - Update attachment (admin/teacher)
- `DELETE /api/v1/session-attachments/{attachment_id}` - Delete attachment (admin/teacher)

### Notification Management
- `POST /api/v1/notifications/` - Create notification (admin/teacher)
- `GET /api/v1/notifications/` - List notifications
- `GET /api/v1/notifications/stats` - Notification statistics (admin/teacher)
- `GET /api/v1/notifications/{notification_id}` - Get notification
- `PUT /api/v1/notifications/{notification_id}` - Update notification (admin/teacher)
- `DELETE /api/v1/notifications/{notification_id}` - Delete notification (admin/teacher)

### User Notifications
- `POST /api/v1/user-notifications/assign` - Assign notification to users (admin/teacher)
- `POST /api/v1/user-notifications/assign-bulk` - Bulk assign notifications (admin/teacher)
- `POST /api/v1/user-notifications/assign-by-role` - Assign by user role (admin/teacher)
- `GET /api/v1/user-notifications/my-notifications` - Get user's notifications
- `POST /api/v1/user-notifications/{notification_id}/read` - Mark notification as read
- `GET /api/v1/user-notifications/stats` - User notification statistics (admin/teacher)

## User Roles

- **admin**: Full system access
- **teacher**: Teacher-specific permissions
- **student**: Student-specific permissions
- **parent**: Parent-specific permissions
- **student_parent**: Combined student and parent permissions

## User Grades

- **TKA**, **TKB**: Kindergarten levels
- **SD1-SD6**: Elementary school grades 1-6
- **SMP1-SMP3**: Junior high school grades 1-3

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL database URL | `mysql+pymysql://root:password@localhost:3306/eduspace` |
| `ASYNC_DATABASE_URL` | Async MySQL database URL | `mysql+aiomysql://root:password@localhost:3306/eduspace` |
| `SECRET_KEY` | JWT secret key | `your-super-secret-key-change-this-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` |
| `DEBUG` | Debug mode | `True` |

## Development Notes

1. **Password Security**: Passwords are hashed using bcrypt for secure storage
2. **Token Authentication**: JWT tokens are used for session authentication
3. **Database**: Uses async SQLAlchemy with MySQL for high performance
4. **Validation**: Pydantic handles comprehensive input/output validation
5. **File Security**: File uploads with type validation and size limits
6. **Role-based Access**: Granular permissions based on user roles
7. **CORS**: Configured for cross-origin requests in development
8. **Async Operations**: Full async/await support for database operations
9. **Error Handling**: Comprehensive error responses with proper HTTP status codes
10. **Data Relationships**: Complex relationships between users, classes, subjects, and sessions

## Database Schema

The system includes the following main entities:

- **Users**: Core user management with profile pictures
- **Classes**: Educational class organization
- **Subjects**: Subject management within classes
- **Teacher-Subject**: Assignment relationships
- **Student-Class**: Student enrollment tracking
- **Sessions**: Learning session management
- **Session Attachments**: File attachments for sessions
- **Notifications**: System-wide notification management
- **User Notifications**: User-specific notification delivery
- **Admin Login Logs**: Administrative access tracking

## File Storage

- **Profile Pictures**: Stored in `uploads/profile_pictures/`
- **Session Attachments**: Stored in `uploads/session_attachments/`
- **Supported Formats**: 
  - Images: JPG, PNG, GIF, WebP
  - Documents: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX
  - Media: MP4, AVI, MOV, MP3, WAV
  - Archives: ZIP, RAR
- **Security**: File type validation, size limits, unique naming

## Notification System

- **Types**: General, Announcement, Assignment, Event, Payment
- **Targeting**: Individual users, bulk assignment, role-based distribution
- **Features**: Read status tracking, delivery monitoring
- **Enhanced Fields**: Description, payment amounts, event dates

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set up your MySQL database**
3. **Configure your `.env` file** with database credentials
4. **Run database initialization**: `python init_db.py`
5. **Start the server**: `uvicorn main:app --reload`
6. **Visit http://localhost:8000/docs** to explore the comprehensive API
7. **Create your first admin user** through the registration endpoint
8. **Start managing classes, subjects, and sessions**

## Recent Updates

- ✅ **Session Management**: Complete session system with file attachments
- ✅ **Enhanced Notifications**: Rich notifications with type-specific fields
- ✅ **Profile Pictures**: User profile picture upload and management
- ✅ **File Security**: Comprehensive file validation and storage
- ✅ **Admin Logging**: Administrative access tracking
- ✅ **Role-based Permissions**: Granular access control throughout the system

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs (Interactive API documentation)
- **ReDoc**: http://localhost:8000/redoc (Alternative documentation format)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (Raw API specification)

## License

This project is for educational purposes.