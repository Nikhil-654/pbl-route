import pytest
from app import app, db, Delivery, DeliveryLocation
from datetime import datetime

def test_create_location(admin_client):
    """Test creating a new delivery location"""
    response = admin_client.post('/admin/locations', data={
        'address': '123 Test St',
        'latitude': 40.7128,
        'longitude': -74.0060
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Location added successfully' in response.data

def test_assign_delivery(admin_client):
    """Test assigning a new delivery"""
    response = admin_client.post('/admin/assign-delivery', data={
        'delivery_boy_id': 1,
        'location_id': 1,
        'order_number': 'TEST-5678',
        'customer_name': 'Test Customer',
        'customer_phone': '123-456-7890',
        'notes': 'Test delivery'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Delivery assigned successfully' in response.data

def test_update_delivery_status(auth_client):
    """Test updating delivery status"""
    response = auth_client.post('/api/delivery/1/status', 
        json={'status': 'in_progress'},
        follow_redirects=True)
    assert response.status_code == 200
    assert b'success' in response.data

def test_get_delivery_details(auth_client):
    """Test getting delivery details"""
    response = auth_client.get('/api/deliveries/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['order_number'] == 'TEST-1234'
    assert data['customer_name'] == 'Test Customer'

def test_delete_delivery(admin_client):
    """Test deleting a delivery"""
    response = admin_client.delete('/admin/deliveries/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True 