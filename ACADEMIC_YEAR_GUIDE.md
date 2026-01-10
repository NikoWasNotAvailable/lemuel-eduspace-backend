# Academic Year History System

This feature allows tracking student/teacher grade and class history across academic years. Users can view their current active data as well as historical data from previous years.

## How It Works

### 1. Academic Years
Each school year has an `academic_year` record (e.g., "2024/2025") with:
- Start and end dates
- A flag indicating if it's the current academic year

### 2. User History Snapshots
When students are promoted (or at any time the admin chooses), the system takes a **snapshot** of all users' current grade/class and stores it in `user_academic_history`. This preserves:
- The student's grade at that time
- The class they were in
- Their role (student/teacher)

### 3. Viewing Historical Data
Users (students/parents/teachers) can:
- View their current grade/class (as always)
- Select a previous academic year to see what grade/class they were in
- Access materials, assignments, and submissions from those previous classes

## API Endpoints

### Academic Year Management (Admin Only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/academic-years/` | List all academic years |
| GET | `/api/v1/academic-years/current` | Get current academic year |
| POST | `/api/v1/academic-years/` | Create new academic year |
| PUT | `/api/v1/academic-years/{id}` | Update academic year |
| POST | `/api/v1/academic-years/{id}/set-current` | Set as current year |
| DELETE | `/api/v1/academic-years/{id}` | Delete academic year |
| POST | `/api/v1/academic-years/snapshot` | Snapshot all users' current state |

### User History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/academic-years/me/history` | Get my academic history |
| GET | `/api/v1/academic-years/users/{user_id}/history` | Get user's academic history |
| GET | `/api/v1/academic-years/users/{user_id}/history/{year_id}` | Get user's history for specific year |

## Workflow

### Start of School Year
1. Admin creates new academic year: `POST /api/v1/academic-years/`
   ```json
   {
     "name": "2025/2026",
     "start_date": "2025-08-01",
     "end_date": "2026-07-31",
     "is_current": true
   }
   ```

2. The system automatically sets this as current (and unsets previous)

### Before Mass Promotion
1. The promotion system automatically snapshots current user states
2. Or admin can manually snapshot: `POST /api/v1/academic-years/snapshot`
3. This saves everyone's current grade/class to the current academic year

### After Promotion
- Students have new grades/classes
- Their previous grades/classes are preserved in history
- They can view old materials by selecting the previous academic year

### Frontend Implementation
The frontend should:
1. Fetch available academic years: `GET /api/v1/academic-years/`
2. Show a year selector (dropdown) defaulting to current year
3. When user selects a different year:
   - Fetch their history for that year: `GET /api/v1/academic-years/me/history`
   - Use the `class_id` from history to fetch classes, subjects, sessions, materials, etc.

## Database Tables

### academic_years
```sql
CREATE TABLE `academic_years` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE,
  `start_date` DATE NOT NULL,
  `end_date` DATE NOT NULL,
  `is_current` BOOLEAN DEFAULT FALSE NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### user_academic_history
```sql
CREATE TABLE `user_academic_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `academic_year_id` INT NOT NULL,
  `grade` ENUM('TKA', 'TKB', ..., 'SMP3') DEFAULT NULL,
  `class_id` INT DEFAULT NULL,
  `role` ENUM('admin', 'teacher', 'student') NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_user_academic_year` (`user_id`, `academic_year_id`)
);
```

## Migration
Run `migrations/add_academic_year_history.sql` on existing databases to add the new tables.
