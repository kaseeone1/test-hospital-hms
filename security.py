import re
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, g, current_app
from werkzeug.security import generate_password_hash
import logging

# Configure logging
logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, app=None):
        self.app = app
        self.failed_attempts = {}  # Store failed login attempts
        self.blocked_ips = set()
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        # Register security middleware
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Register error handlers
        app.register_error_handler(429, self.rate_limit_exceeded)
        app.register_error_handler(403, self.forbidden)
    
    def before_request(self):
        """Security checks before each request"""
        # Check if IP is blocked
        client_ip = request.remote_addr
        if client_ip in self.blocked_ips:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check rate limiting
        if not self.check_rate_limit():
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Add security headers
        self.add_security_headers()
        
        # Log suspicious activity
        self.log_suspicious_activity()
    
    def after_request(self, response):
        """Add security headers after response"""
        # Add security headers
        for header, value in current_app.config.get('SECURITY_HEADERS', {}).items():
            if value is not None:
                response.headers[header] = value
        
        # Remove server information
        response.headers.pop('Server', None)
        
        return response
    
    def check_rate_limit(self):
        """Check rate limiting for current request"""
        if not current_app.config.get('RATE_LIMIT_ENABLED', True):
            return True
        
        client_ip = request.remote_addr
        current_time = time.time()
        
        # Get rate limit configuration
        if request.endpoint == 'login':
            limit = current_app.config.get('RATE_LIMIT_LOGIN', '5 per minute')
        elif request.path.startswith('/api/'):
            limit = current_app.config.get('RATE_LIMIT_API', '60 per minute')
        else:
            limit = current_app.config.get('RATE_LIMIT_DEFAULT', '100 per minute')
        
        # Parse limit (e.g., "5 per minute")
        count, period = limit.split(' per ')
        count = int(count)
        
        if period == 'minute':
            window = 60
        elif period == 'hour':
            window = 3600
        elif period == 'day':
            window = 86400
        else:
            return True
        
        # Check rate limit
        key = f"rate_limit:{client_ip}:{request.endpoint}"
        requests = session.get(key, [])
        
        # Remove old requests outside the window
        requests = [req_time for req_time in requests if current_time - req_time < window]
        
        if len(requests) >= count:
            return False
        
        # Add current request
        requests.append(current_time)
        session[key] = requests
        
        return True
    
    def add_security_headers(self):
        """Add security headers to response"""
        # This will be handled in after_request
        pass
    
    def log_suspicious_activity(self):
        """Log suspicious activity patterns"""
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'sqlmap',
            r'nmap',
            r'nikto',
            r'burp',
            r'owasp',
            r'<script',
            r'javascript:',
            r'data:text/html'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                logger.warning(f"Suspicious activity detected from {client_ip}: {user_agent}")
                break
    
    def rate_limit_exceeded(self, error):
        """Handle rate limit exceeded"""
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    
    def forbidden(self, error):
        """Handle forbidden access"""
        return jsonify({'error': 'Access denied'}), 403
    
    def validate_password(self, password):
        """Validate password strength"""
        config = current_app.config
        
        if len(password) < config.get('MIN_PASSWORD_LENGTH', 8):
            return False, f"Password must be at least {config.get('MIN_PASSWORD_LENGTH', 8)} characters long"
        
        if len(password) > config.get('MAX_PASSWORD_LENGTH', 128):
            return False, f"Password must be no more than {config.get('MAX_PASSWORD_LENGTH', 128)} characters long"
        
        if config.get('PASSWORD_REQUIRE_UPPERCASE', True) and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if config.get('PASSWORD_REQUIRE_LOWERCASE', True) and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if config.get('PASSWORD_REQUIRE_DIGITS', True) and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if config.get('PASSWORD_REQUIRE_SPECIAL_CHARS', True) and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'admin', 'qwerty', 'letmein',
            'welcome', 'monkey', 'dragon', 'master', 'football'
        ]
        
        if password.lower() in weak_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, "Password is valid"
    
    def record_failed_login(self, username, ip_address):
        """Record a failed login attempt"""
        key = f"{username}:{ip_address}"
        current_time = time.time()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
        
        self.failed_attempts[key].append(current_time)
        
        # Clean old attempts
        window = current_app.config.get('ACCOUNT_LOCKOUT_DURATION', 900)
        self.failed_attempts[key] = [
            attempt for attempt in self.failed_attempts[key] 
            if current_time - attempt < window
        ]
        
        # Log failed attempt
        logger.warning(f"Failed login attempt for user '{username}' from IP {ip_address}")
        
        # Check if account should be locked
        threshold = current_app.config.get('ACCOUNT_LOCKOUT_THRESHOLD', 5)
        if len(self.failed_attempts[key]) >= threshold:
            logger.warning(f"Account '{username}' locked due to multiple failed attempts")
            return True  # Account should be locked
        
        return False
    
    def is_account_locked(self, username, ip_address):
        """Check if account is locked due to failed attempts"""
        key = f"{username}:{ip_address}"
        current_time = time.time()
        
        if key not in self.failed_attempts:
            return False
        
        # Clean old attempts
        window = current_app.config.get('ACCOUNT_LOCKOUT_DURATION', 900)
        self.failed_attempts[key] = [
            attempt for attempt in self.failed_attempts[key] 
            if current_time - attempt < window
        ]
        
        threshold = current_app.config.get('ACCOUNT_LOCKOUT_THRESHOLD', 5)
        return len(self.failed_attempts[key]) >= threshold
    
    def clear_failed_attempts(self, username, ip_address):
        """Clear failed attempts after successful login"""
        key = f"{username}:{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def block_ip(self, ip_address):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP address {ip_address} has been blocked")
    
    def unblock_ip(self, ip_address):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip_address)
        logger.info(f"IP address {ip_address} has been unblocked")

# Create global security manager instance
security_manager = SecurityManager()

def require_https(f):
    """Decorator to require HTTPS"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not current_app.debug:
            return jsonify({'error': 'HTTPS required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_file_upload(file):
    """Validate file upload security"""
    if not file:
        return False, "No file provided"
    
    # Check file size
    max_size = current_app.config.get('MAX_FILE_SIZE', 16 * 1024 * 1024)
    if len(file.read()) > max_size:
        file.seek(0)  # Reset file pointer
        return False, f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB"
    
    file.seek(0)  # Reset file pointer
    
    # Check file extension
    filename = file.filename
    if not filename:
        return False, "Invalid filename"
    
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    allowed_extensions = set()
    for extensions in current_app.config.get('ALLOWED_FILE_TYPES', {}).values():
        allowed_extensions.update(extensions)
    
    if extension not in allowed_extensions:
        return False, f"File type '{extension}' is not allowed"
    
    return True, "File is valid"

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    
    # Remove potentially dangerous HTML tags
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea']
    for tag in dangerous_tags:
        text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(f'<{tag}[^>]*/>', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    # Remove data: protocol
    text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
    
    return text

def log_security_event(event_type, details, user_id=None, ip_address=None):
    """Log security events for audit trail"""
    if not current_app.config.get('AUDIT_LOG_ENABLED', True):
        return
    
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(current_app.config.get('AUDIT_LOG_LEVEL', 'INFO'))
    
    # Create file handler if not exists
    if not audit_logger.handlers:
        handler = logging.FileHandler(current_app.config.get('AUDIT_LOG_FILE', 'audit.log'))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details,
        'user_id': user_id,
        'ip_address': ip_address or request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'endpoint': request.endpoint
    }
    
    audit_logger.info(f"SECURITY_EVENT: {log_entry}") 