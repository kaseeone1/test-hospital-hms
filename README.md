# 🏥 Test Hospital HMS - Bluwik HMS

A comprehensive Hospital Management System built with Flask, designed for efficient healthcare facility management with robust security features.

## 🌟 Features

### 🔐 **Security Features**
- **Multi-factor Authentication Ready**
- **Role-based Access Control**
- **Account Lockout Protection**
- **Rate Limiting & DDoS Protection**
- **XSS & SQL Injection Prevention**
- **Comprehensive Audit Logging**
- **Secure File Upload Validation**
- **HTTPS Enforcement**

### 👥 **User Management**
- **Super Admin Control** (Hidden from regular users)
- **Role-based Permissions**
- **User Activity Tracking**
- **Session Management**
- **Password Policy Enforcement**

### 🏥 **Patient Management**
- **Patient Registration & Records**
- **Medical History Tracking**
- **Visit Management**
- **Treatment Records**
- **Prescription Management**

### 💊 **Pharmacy Management**
- **Medicine Inventory**
- **Stock Management**
- **Prescription Filling**
- **Sales Tracking**
- **Expiry Date Monitoring**

### 💰 **Financial Management**
- **Payment Processing**
- **Receipt Generation**
- **Service Charges**
- **Revenue Reports**
- **Financial Analytics**

### 📊 **Reporting & Analytics**
- **Patient Reports**
- **Financial Reports**
- **Inventory Reports**
- **Activity Logs**
- **Custom Report Generation**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/test-hospital-hms.git
   cd test-hospital-hms
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env with your configuration
   DATABASE_URL=sqlite:///test_hospital.db
   SESSION_SECRET=your-secret-key-here
   DEBUG=False
   ```

5. **Initialize the database**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Login with default credentials (see below)

## 🔑 Default Access

### Super Admin (Hidden)
- **Username**: `Kaseeone`
- **Password**: `@Kenya3404@Kenya3404`
- **Access**: Full system control, hidden from user management

### Regular Admin
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Standard administrative functions

## 📁 Project Structure

```
test-hospital-hms/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── security.py           # Security middleware
├── models.py             # Database models
├── routes.py             # Application routes
├── utils.py              # Utility functions
├── extensions.py         # Flask extensions
├── requirements.txt      # Python dependencies
├── render.yaml           # Render deployment config
├── gunicorn.conf.py      # Gunicorn configuration
├── SECURITY.md           # Security documentation
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
├── migrations/           # Database migrations
├── uploads/              # File uploads
└── instance/             # Instance-specific files
```

## 🛡️ Security Features

### Authentication & Authorization
- **Password Policy**: 8+ characters, complexity requirements
- **Account Lockout**: 5 failed attempts = 15-minute lockout
- **Session Management**: 30-minute timeout, secure cookies
- **Role-based Access**: Granular permissions per role

### Protection Against
- ✅ Brute force attacks
- ✅ SQL injection
- ✅ XSS attacks
- ✅ CSRF attacks
- ✅ DDoS attacks
- ✅ File upload attacks
- ✅ Session hijacking
- ✅ Information disclosure

### Audit Logging
- Complete activity tracking
- Security event logging
- User action history
- System access logs

## 🚀 Deployment

### Render.com Deployment
1. Fork this repository
2. Connect to Render.com
3. Create a new Web Service
4. Set environment variables
5. Deploy automatically

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_SECRET=your-secret-key
DEBUG=False
FLASK_ENV=production
```

## 📊 Demo Data

The system includes comprehensive demo data:
- **Patients**: 50+ sample patients
- **Visits**: 200+ patient visits
- **Medicines**: 30+ medicine types
- **Sales**: 150+ pharmacy sales
- **Users**: Multiple role types
- **Activities**: Complete audit trail

## 🔧 Configuration

### Security Settings
```python
# config.py
MIN_PASSWORD_LENGTH = 8
ACCOUNT_LOCKOUT_THRESHOLD = 5
RATE_LIMIT_LOGIN = "5 per minute"
SESSION_TIMEOUT = 1800  # 30 minutes
```

### Database Configuration
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///test_hospital.db')
```

## 📈 Monitoring & Logs

### Log Files
- `app.log` - Application logs
- `audit.log` - Security audit logs
- `access.log` - Access logs

### Monitoring Features
- Failed login attempt tracking
- Suspicious activity detection
- Performance monitoring
- Error tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- **Email**: support@testhospital.com
- **Documentation**: [SECURITY.md](SECURITY.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/test-hospital-hms/issues)

## 🔄 Version History

- **v1.3.0** - Enhanced security features, audit logging
- **v1.2.0** - Added pharmacy management, reporting
- **v1.1.0** - Patient management, user roles
- **v1.0.0** - Initial release with basic functionality

## ⚠️ Important Notes

- **Default passwords should be changed** after first login
- **Super admin account is hidden** from regular user management
- **Database backups** should be performed regularly
- **Security updates** should be applied promptly
- **HTTPS** is required in production environments

---

**Built with ❤️ for healthcare management** 