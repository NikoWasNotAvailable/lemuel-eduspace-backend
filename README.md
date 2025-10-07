# Lemuel EduSpace Backend

A FastAPI backend for an educational management system with user authentication and CRUD operations.

## Features

- **User Management**: Complete CRUD operations for users
- **Authentication**: JWT-based authentication with role-based access control
- **Role-based Access**: Support for admin, teacher, student, parent, and student_parent roles
- **Modular Architecture**: Clean MVC pattern with services layer
- **Async Database**: SQLAlchemy with async MySQL support
- **Input Validation**: Pydantic schemas for request/response validation
- **Security**: Password hashing with bcrypt

## Project Structure

```
lemuel-eduspace-backend/
├── app/
│   ├── __init__.py
│   ├── controllers/          # FastAPI route handlers
│   │   ├── __init__.py
│   │   └── user_controller.py
│   ├── core/                 # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication dependencies
│   │   ├── config.py        # Application settings
│   │   ├── database.py      # Database configuration
│   │   └── security.py      # Security utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   └── user.py
│   └── services/            # Business logic layer
│       ├── __init__.py
│       └── user_service.py
├── main.py                  # FastAPI application entry point
├── init_db.py              # Database initialization script
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
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

### User Management
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user
- `POST /api/v1/users/me/change-password` - Change password

### Admin Operations
- `GET /api/v1/users/` - List all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID (admin only)
- `PUT /api/v1/users/{user_id}` - Update user (admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)

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

1. **Password Security**: Passwords are hashed using bcrypt
2. **Token Authentication**: JWT tokens are used for authentication
3. **Database**: Uses async SQLAlchemy with MySQL
4. **Validation**: Pydantic handles input/output validation
5. **CORS**: Configured for local development

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Set up your MySQL database
3. Configure your `.env` file
4. Run database initialization: `python init_db.py`
5. Start the server: `uvicorn main:app --reload`
6. Visit http://localhost:8000/docs to explore the API

## License

This project is for educational purposes.