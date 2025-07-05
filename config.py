import os
import secrets
from datetime import timedelta

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/bluwik_hms.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Handle Render's PostgreSQL URL format
if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

# Security configuration - Generate a strong secret key
SECRET_KEY = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# Application configuration
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
HOST = '0.0.0.0'  # This allows access from other computers on the network
PORT = 5000

# Session configuration - Enhanced security
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_REFRESH_EACH_REQUEST = True  # Refresh session on each request

# Upload configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# Logging configuration
LOG_LEVEL = 'INFO' if not DEBUG else 'DEBUG'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'app.log'

# Application settings
TESTING = False

# Application configuration
APP_NAME = 'Bluwik HMS'
HOSPITAL_NAME = 'Test Hospital'

# Security settings
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True
PASSWORD_HISTORY_COUNT = 5  # Remember last 5 passwords
ACCOUNT_LOCKOUT_THRESHOLD = 5  # Lock account after 5 failed attempts
ACCOUNT_LOCKOUT_DURATION = 900  # 15 minutes lockout
SESSION_TIMEOUT = 1800  # 30 minutes in seconds
DEFAULT_PAGINATION = 20
LOW_STOCK_THRESHOLD = 10
EXPIRY_WARNING_DAYS = 90

# Rate limiting
RATE_LIMIT_ENABLED = True
RATE_LIMIT_DEFAULT = "200 per day;50 per hour"
RATE_LIMIT_LOGIN = "5 per minute"
RATE_LIMIT_API = "60 per minute"
RATE_LIMIT_STORAGE_URL = "memory://"

# Security headers
SECURITY_HEADERS = {
    'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains',
    'X_CONTENT_TYPE_OPTIONS': 'nosniff',
    'X_FRAME_OPTIONS': 'SAMEORIGIN',
    'X_XSS_PROTECTION': '1; mode=block',
    'REFERRER_POLICY': 'strict-origin-when-cross-origin'
}

# CSRF protection
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

# File upload security
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_FILE_TYPES = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'document': {'pdf', 'doc', 'docx'},
    'spreadsheet': {'xls', 'xlsx', 'csv'}
}

# Audit logging
AUDIT_LOG_ENABLED = True
AUDIT_LOG_LEVEL = 'INFO'
AUDIT_LOG_FILE = 'audit.log'

# Backup security
BACKUP_ENCRYPTION_ENABLED = True
BACKUP_RETENTION_DAYS = 30

# Network security
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.42.98']
BLOCKED_IPS = []  # Add IPs to block

class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    PERMANENT_SESSION_LIFETIME = PERMANENT_SESSION_LIFETIME
    SESSION_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = SESSION_COOKIE_HTTPONLY
    SESSION_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    UPLOAD_FOLDER = UPLOAD_FOLDER
    RATELIMIT_DEFAULT = RATE_LIMIT_DEFAULT
    RATE_LIMIT_LOGIN = RATE_LIMIT_LOGIN
    RATE_LIMIT_API = RATE_LIMIT_API
    SECURITY_HEADERS = SECURITY_HEADERS
    WTF_CSRF_ENABLED = WTF_CSRF_ENABLED
    WTF_CSRF_TIME_LIMIT = WTF_CSRF_TIME_LIMIT
    MAX_FILE_SIZE = MAX_FILE_SIZE
    ALLOWED_FILE_TYPES = ALLOWED_FILE_TYPES
    AUDIT_LOG_ENABLED = AUDIT_LOG_ENABLED
    AUDIT_LOG_LEVEL = AUDIT_LOG_LEVEL
    AUDIT_LOG_FILE = AUDIT_LOG_FILE
    BACKUP_ENCRYPTION_ENABLED = BACKUP_ENCRYPTION_ENABLED
    BACKUP_RETENTION_DAYS = BACKUP_RETENTION_DAYS
    ALLOWED_HOSTS = ALLOWED_HOSTS
    BLOCKED_IPS = BLOCKED_IPS
    RATE_LIMIT_STORAGE_URL = RATE_LIMIT_STORAGE_URL
