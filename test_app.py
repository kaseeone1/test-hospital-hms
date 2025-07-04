import unittest
import tempfile
import os
from app import create_app
from extensions import db
from models import User, Role

class HMSTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        with self.app.app_context():
            db.create_all()
            self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after each test"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_home_page(self):
        """Test that home page redirects to login when not authenticated"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_login_page(self):
        """Test that login page is accessible"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_invalid_login(self):
        """Test invalid login attempt"""
        response = self.client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = self.client.get('/login')
        headers = response.headers
        
        # Check for security headers
        self.assertIn('X-Content-Type-Options', headers)
        self.assertIn('X-Frame-Options', headers)
        self.assertIn('X-XSS-Protection', headers)
    
    def test_rate_limiting(self):
        """Test rate limiting on login attempts"""
        # Make multiple login attempts
        for i in range(6):
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # The 6th attempt should be rate limited
        self.assertIn(b'Rate limit exceeded', response.data)

if __name__ == '__main__':
    unittest.main() 