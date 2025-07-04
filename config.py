import os
import secrets

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///test_hospital.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Security configuration - Generate a strong secret key
SECRET_KEY = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# Application configuration
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
HOST = '0.0.0.0'  # This allows access from other computers on the network
PORT = 5000

# Session configuration - Enhanced security
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
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
RATE_LIMIT_DEFAULT = "100 per minute"
RATE_LIMIT_LOGIN = "5 per minute"
RATE_LIMIT_API = "60 per minute"

# Security headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains' if not DEBUG else None,
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
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
