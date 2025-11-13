# Admin Management CLI

This document explains how to use the Admin Management CLI for creating and managing admin users.

## 🚀 Quick Start

### Create Your First Admin User (Interactive)
```bash
# Windows (PowerShell)
.\manage.ps1 create-admin

# Windows (Command Prompt)
manage.bat create-admin

# Direct Python (if venv is activated)
python manage.py create-admin
```

### Create Default Admin User (Automated)
```bash
# This creates an admin with preset credentials
.\manage.ps1 default-admin
```

## 📋 Available Commands

### 1. `create-admin` - Interactive Admin Creation
Creates a new admin user with interactive prompts.

**Features:**
- ✅ Interactive prompts for all user details
- ✅ Auto-generates NIS if not provided
- ✅ Password confirmation
- ✅ Warns if admins already exist
- ✅ Validates input data

**Example:**
```bash
PS C:\...\lemuel-eduspace-backend> .\manage.ps1 create-admin

🔧 Admin User Creation Tool
==================================================

📝 Enter admin details:
Admin Name: John Administrator
Admin Email (optional): john@eduspace.com
Admin NIS (leave blank for auto-generate): ADMIN_JOHN

Gender options:
1. Male
2. Female  
3. Skip (leave blank)
Select gender (1/2/3): 1

🔑 Set admin password:
Admin Password (min 8 chars): ********
Confirm Password: ********

✅ Admin user created successfully!
==================================================
👤 ID: 1
🏷️  NIS: ADMIN_JOHN
📛 Name: John Administrator
📧 Email: john@eduspace.com
⚡ Role: admin
📅 Created: 2025-11-13 10:30:45
==================================================
```

### 2. `default-admin` - Quick Default Admin
Creates a default admin user with preset credentials (only if no admins exist).

**Default Credentials:**
- **NIS:** ADMIN001
- **Email:** admin@eduspace.com
- **Password:** SuperSecretAdmin123!

**Example:**
```bash
PS C:\...\lemuel-eduspace-backend> .\manage.ps1 default-admin

🔧 Creating default admin user...
✅ Default admin user created successfully!
============================================================
📧 Email/Identifier: admin@eduspace.com
🏷️  NIS: ADMIN001
🔑 Default Password: SuperSecretAdmin123!
⚠️  CRITICAL: Change this password immediately after first login!
============================================================
```

### 3. `list-admins` - List All Admin Users
Displays all existing admin users in the system.

**Example:**
```bash
PS C:\...\lemuel-eduspace-backend> .\manage.ps1 list-admins

👥 Admin Users List
============================================================
Found 2 admin user(s):

1. ID: 1
   🏷️  NIS: ADMIN001
   📛 Name: System Administrator
   📧 Email: admin@eduspace.com
   📅 Created: 2025-11-13 09:15:30
   🔄 Updated: 2025-11-13 09:15:30

2. ID: 5
   🏷️  NIS: ADMIN_JOHN
   📛 Name: John Administrator
   📧 Email: john@eduspace.com
   📅 Created: 2025-11-13 10:30:45
   🔄 Updated: 2025-11-13 10:30:45
```

### 4. `help` - Show Help Information
Displays available commands and usage examples.

## 🔧 Setup Instructions

### Prerequisites
1. Virtual environment should be created and activated
2. All dependencies should be installed
3. Database should be configured and accessible

### File Permissions (Linux/Mac)
```bash
chmod +x manage.py
chmod +x manage.ps1
```

### Windows Execution Policy
If you get execution policy errors with PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🛡️ Security Notes

### First-Time Setup
1. **Use Interactive Mode:** For production, always use `create-admin` (interactive)
2. **Strong Passwords:** Ensure admin passwords are complex and unique
3. **Change Default Credentials:** If using `default-admin`, change the password immediately
4. **Limit Admin Users:** Only create necessary admin accounts

### Best Practices
- **Regular Audits:** Use `list-admins` to audit admin accounts
- **Unique Credentials:** Each admin should have unique NIS and email
- **Documentation:** Keep track of who has admin access
- **Password Policy:** Enforce strong password requirements

## 🚨 Troubleshooting

### Common Issues

**1. Virtual Environment Not Found**
```
❌ Virtual environment not found!
```
**Solution:** Create venv with `python -m venv venv` and install dependencies.

**2. Database Connection Error**
```
❌ Error creating admin: (database connection error)
```
**Solution:** Ensure database is running and connection settings are correct.

**3. Admin Already Exists (default-admin)**
```
ℹ️  Admin users already exist (1 found). Skipping default creation.
```
**Solution:** This is normal. Use `create-admin` to create additional admins.

**4. Permission Denied (Windows)**
```
❌ Access denied
```
**Solution:** Run PowerShell as Administrator or adjust execution policy.

### Debug Mode
For detailed error information, run Python directly:
```bash
python manage.py create-admin
```

## 📖 Usage Scenarios

### Scenario 1: First-Time Application Setup
```bash
# 1. Create default admin quickly
.\manage.ps1 default-admin

# 2. Login to application with default credentials
# 3. Change password immediately
# 4. Create proper admin users through web interface or CLI
```

### Scenario 2: Adding New Admin User
```bash
# 1. List existing admins
.\manage.ps1 list-admins

# 2. Create new admin interactively
.\manage.ps1 create-admin

# 3. Verify creation
.\manage.ps1 list-admins
```

### Scenario 3: Production Deployment
```bash
# In your deployment script:
.\manage.ps1 default-admin  # Only creates if none exist
```

## 🔗 Integration

### Docker Integration
```dockerfile
# In your Dockerfile
COPY manage.py .
RUN python manage.py default-admin
```

### CI/CD Pipeline
```yaml
# In your deployment pipeline
- name: Create Initial Admin
  run: python manage.py default-admin
```

This CLI provides a secure and convenient way to manage admin users for your Lemuel Eduspace Backend application.