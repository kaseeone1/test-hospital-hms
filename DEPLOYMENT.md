# 🚀 Deployment Guide

This guide covers deploying the Test Hospital HMS to various platforms.

## 📋 Prerequisites

- Python 3.8+
- Git
- Database (SQLite for development, PostgreSQL for production)
- Web server (Gunicorn, uWSGI, etc.)

## 🏠 Local Development

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/test-hospital-hms.git
cd test-hospital-hms
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
cp env.example .env

# Edit .env with your settings
DATABASE_URL=sqlite:///test_hospital.db
SESSION_SECRET=your-secret-key-here
DEBUG=True
```

### 5. Initialize Database
```bash
python app.py
```

### 6. Run Development Server
```bash
python app.py
```

Access the application at `http://localhost:5000`

## ☁️ Render.com Deployment

### 1. Fork Repository
- Fork this repository to your GitHub account
- Ensure all files are committed and pushed

### 2. Create Render Account
- Sign up at [render.com](https://render.com)
- Connect your GitHub account

### 3. Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `test-hospital-hms`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### 4. Set Environment Variables
Add these environment variables in Render dashboard:

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_SECRET=your-super-secret-production-key
DEBUG=False
FLASK_ENV=production
```

### 5. Deploy
- Click "Create Web Service"
- Render will automatically deploy your application
- Your app will be available at `https://your-app-name.onrender.com`

## 🐳 Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### 2. Create docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/hms
      - SESSION_SECRET=your-secret-key
      - DEBUG=False
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=hms
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 3. Build and Run
```bash
docker-compose up --build
```

## 🌐 Heroku Deployment

### 1. Install Heroku CLI
```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Create Heroku App
```bash
heroku create your-hospital-hms
```

### 3. Add PostgreSQL
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### 4. Set Environment Variables
```bash
heroku config:set SESSION_SECRET=your-secret-key
heroku config:set DEBUG=False
heroku config:set FLASK_ENV=production
```

### 5. Deploy
```bash
git push heroku main
```

## 🔧 Production Configuration

### Security Checklist
- [ ] Change default passwords
- [ ] Set strong SESSION_SECRET
- [ ] Enable HTTPS
- [ ] Configure database backups
- [ ] Set up monitoring
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up error tracking

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_SECRET=your-super-secret-key

# Optional
DEBUG=False
FLASK_ENV=production
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=True
AUDIT_LOG_ENABLED=True
```

### Database Setup
```bash
# PostgreSQL
createdb hospital_hms
psql hospital_hms -c "CREATE USER hms_user WITH PASSWORD 'secure_password';"
psql hospital_hms -c "GRANT ALL PRIVILEGES ON DATABASE hospital_hms TO hms_user;"
```

## 📊 Monitoring & Logs

### Application Logs
```bash
# View application logs
tail -f app.log

# View audit logs
tail -f audit.log
```

### Health Check Endpoint
Add this to your routes.py:
```python
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
```

### Performance Monitoring
- Use tools like New Relic, DataDog, or Sentry
- Monitor database performance
- Track response times
- Monitor error rates

## 🔒 Security Hardening

### 1. SSL/TLS Configuration
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### 3. Database Security
```sql
-- Create read-only user for reports
CREATE USER hms_readonly WITH PASSWORD 'readonly_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hms_readonly;
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Verify environment variables
echo $DATABASE_URL
```

#### 2. Permission Errors
```bash
# Fix file permissions
chmod 755 uploads/
chmod 644 *.py
```

#### 3. Memory Issues
```bash
# Increase worker memory
gunicorn --workers 2 --worker-class gevent --worker-connections 1000 app:app
```

#### 4. Log Rotation
```bash
# Set up log rotation
sudo logrotate -f /etc/logrotate.d/hms
```

### Support
For deployment issues:
- Check application logs
- Verify environment variables
- Test database connectivity
- Review security configuration

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Multiple application instances
- Database connection pooling
- Redis for session storage

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Enable caching
- Use CDN for static files

---

**Need help?** Check the [SECURITY.md](SECURITY.md) for security best practices. 