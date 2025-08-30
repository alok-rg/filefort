# FileFort - Secure File Vault System
<div align="center">
  <img src="authentication\static\img\fort.ico" alt="Cindox Logo" width="80" height="80" style="border-radius: 10px; box-shadow: 0 0 10px 1px #4df9f9ff;">
    <br>
    <br>

    
![Django](https://img.shields.io/badge/Django-5.2.5-092E20?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite)
</div>



## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [User Roles](#-user-roles)
- [API Endpoints](#-api-endpoints)
- [Database Schema](#-database-schema)
- [Security](#-security)
- [Configuration](#-configuration)
- [Deployment](#-deployment)

## 🎯 Overview

**FileFort** is a secure, role-based file vault system built with Django for educational institutions. It enables safe PDF document sharing between teachers and students with comprehensive access controls.

**Key Design Goals:**
- **Teachers** upload and share educational PDFs with students
- **Students** securely view materials without unauthorized downloads
- **Administrators** manage user roles and system oversight
- **Security-first** approach preventing direct file access

The system uses token-based authentication, secure file serving outside the web root, and role-based permissions to ensure files remain protected while accessible to authorized users.

## ✨ Features

### 🔐 Security & Access Control
- **Token-based file access** with unique, time-limited tokens (30-min expiry)
- **Secure file serving** - files stored outside web root with 64-character unique IDs
- **Role-based permissions** - admin, teacher, and student access levels
- **Session validation** and continuous authentication checks
- **PDF-only uploads** with 50MB size limit and file type validation

### 📚 File Management & Sharing
- **File metadata tracking** - size, upload date, expiry date, access permissions
- **Sharing policies** - Private (teacher only), Public (all users), or Group-specific
- **Access types** - View-only or downloadable permissions per file
- **Built-in PDF viewer** using PDF.js for secure viewing without downloads
- **File expiry** with automatic access revocation

### 👥 Group Management
- **Student groups** created by teachers using student usernames
- **Real-time username validation** during group creation
- **Group-based file sharing** with member-only access
- **Group analytics** showing member count and creation date

### 🎨 User Interface
- **Modern dark theme** with professional color palette
- **Responsive design** for desktop, tablet, and mobile
- **AJAX-powered interactions** for real-time updates without page refresh
- **Admin search panel** for user management and role updates

## 🏗 System Architecture

```
FileFort/
├── 🗂 zcore/                  # Django project settings
│   ├── settings.py            # Main configuration
│   ├── urls.py                # Root URL routing
│   └── wsgi.py                # WSGI configuration
├── 🔐 authentication/         # User authentication app
│   ├── models.py              # UserProfile model
│   ├── views.py               # Login/logout views
│   └── templates/             # Login templates
├── 📊 dashboard/              # Main application
│   ├── models.py              # FileDetail, studentGroup models
│   ├── views.py               # Core business logic
│   ├── urls.py                # App-specific routing
│   └── templates/             # Dashboard templates
├── 🗃 db.sqlite3              # SQLite database
└── 📋 manage.py              # Django management script
└── 📁 private_media/         # Secure file storage (outside web root)
```

## 🚀 Installation

### Prerequisites
- Python 3.8+ and pip
- Virtual environment (recommended)

### Setup Steps
```bash
# 1. Clone and setup environment
git clone <repository-url>
cd fileFort
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install django pillow

# 3. Database setup
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 4. Create secure media directory
mkdir ..\private_media
mkdir ..\private_media\uploads

# 5. Run development server
python manage.py runserver
```

**Access Points:**
- Main app: `http://127.0.0.1:8000`
- Admin panel: `http://127.0.0.1:8000/admin`

## 👤 User Roles

| Role | Capabilities |
|------|-------------|
| **🛡 Admin** | Search users, promote students to teachers, system oversight |
| **👨‍🏫 Teacher** | Upload PDFs, create student groups, set file permissions, manage own content |
| **👨‍🎓 Student** | View public files, access group files (if member), secure PDF viewing |

### Access Control Matrix
| Action | Student | Teacher | Admin |
|--------|---------|---------|-------|
| Upload Files | ❌ | ✅ | ❌ |
| Create Groups | ❌ | ✅ | ❌ |
| View Public Files | ✅ | ✅ | ✅ |
| Access Group Files | ✅ (if member) | ✅ (own groups) | ✅ |
| Manage Users | ❌ | ❌ | ✅ |

## 🌐 API Endpoints

### Authentication
```python
POST /auth/login/           # User login
POST /auth/logout/          # User logout
```

### Dashboard Operations
```python
GET  /dashboard/            # Role-based dashboard
POST /upload/               # File upload (teachers only)
POST /group_create/         # Create student group (teachers)
POST /fetch_tables/         # Get files and groups data
PATCH /update_access/       # Update file permissions
DELETE /delete_file/        # Delete file
DELETE /delete_group/       # Delete group
```

### PDF Viewer & Streaming
```python
GET  /pdf/view/<file_id>/               # PDF viewer page
GET  /pdf/stream/<token>/               # Secure PDF streaming
GET  /pdf/stream/<token>/?download=1    # Download (if permitted)
```

### Admin Panel
```python
GET  /search_user/?username=<name>      # Search users
POST /update_role/                      # Update user role
```

## 🗄 Database Schema

### Core Models

**UserProfile** (1:1 with User)
```python
- id: CharField (primary key)
- user: OneToOneField(User)
- role: CharField (student/teacher/admin)
```

**FileDetail**
```python
- file_id: CharField (64-char unique ID)
- file: FileField (PDF storage path)
- file_name, file_size, file_upload_date
- file_expiry_date: DateTimeField (optional)
- uploaded_by: ForeignKey(User)
- sharing_policy: CharField (private/public/shared)
- access_type: CharField (view/download)
- shared_group: ForeignKey(studentGroup)
```

**studentGroup**
```python
- name: CharField
- created_by: ForeignKey(User)
- students: ManyToManyField(User)
- no_of_students: IntegerField
- created_at: DateTimeField
```

### Key Relationships
- User ↔ UserProfile (1:1) for role management
- User → FileDetail (1:N) for file ownership
- studentGroup ↔ User (M:N) for group membership
- studentGroup → FileDetail (1:N) for group file sharing

## 🛡 Security

### Token-Based File Access
1. User requests file → System generates UUID token
2. Token cached with user ID + file ID (30-min expiry)
3. File served only with valid token + permission check
4. Multi-layer validation: auth → role → ownership → token

### Secure File Storage
```python
# Files stored outside web root
MEDIA_ROOT = BASE_DIR.parent / 'private_media'  # Outside project
MEDIA_URL = '/media/'  # Internal URL only

# File naming convention
original_name: "assignment.pdf"
stored_as: "EV15iZLQS20OScD76qgE26x61Itwob14z5cul6t1ksouGJzkasMpUstEtCuyeHN9.pdf"
```

### Validation Layers
- **Authentication**: Active user session required
- **Authorization**: Role-appropriate permissions
- **Ownership**: File/group access verification
- **Token**: Valid file access token
- **Session**: Active session validation

### PDF Viewer Security
```javascript
// Security features implemented
- Right-click context menu disabled
- Ctrl+S (Save) blocked
- Ctrl+P (Print) blocked
- Token-based PDF loading
- No direct file URL exposure
- Session-based access control
```

### PDF.js Integration
```javascript
// PDF loading with secure token
const pdfUrl = '/pdf/stream/{{ token }}/';
pdfjsLib.getDocument(pdfUrl).promise.then(function(pdfDoc) {
    // PDF rendering and control logic
});
```

## ⚙ Configuration

### Key Settings (settings.py)
```python
# File Security
MEDIA_ROOT = BASE_DIR.parent / 'private_media'

# Timezone
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True

# Security (Production)
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
```


## 🚀 Deployment

### Production Checklist
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`
- Use PostgreSQL/MySQL instead of SQLite
- Set up Redis for token caching
- Configure SSL certificates
- Set up static file serving (whitenoise/nginx)
- Configure backup strategy
- Set up monitoring and logging


### Environment Variables
```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/filefort
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

---

**FileFort** - Secure file management for educational environments 🎓  
Built with Django, designed for security and ease of use.
