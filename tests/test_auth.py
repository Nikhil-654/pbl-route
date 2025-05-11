import pytest
from app import app, db, DeliveryBoy
from werkzeug.security import generate_password_hash

def test_register(client):
    """Test user registration"""
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'test123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data

def test_login(client):
    """Test user login"""
    # First create a test user
    with app.app_context():
        user = DeliveryBoy(
            name='Test User',
            email='test@example.com',
            password=generate_password_hash('test123'),
            verification_code='TEST123',
            status='Confirmed'
        )
        db.session.add(user)
        db.session.commit()

    # Try to login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'test123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_logout(auth_client):
    """Test user logout"""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data

def test_protected_route(client):
    """Test accessing protected route without authentication"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data 