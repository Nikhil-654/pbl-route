# Delivery Management System

A Flask-based web application for managing delivery locations and assigning deliveries to delivery boys.

## Features

- User authentication and authorization
- Delivery location management with Google Maps integration
- Delivery assignment and tracking
- Real-time delivery status updates
- Admin dashboard for managing deliveries and locations
- Mobile-responsive design

## Prerequisites

- Python 3.8 or higher
- Google Maps API key
- Gmail account for sending verification emails

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd delivery-management-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
FLASK_SECRET_KEY=your_secret_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
MAIL_USERNAME=your_gmail_address
MAIL_PASSWORD=your_gmail_app_password
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Usage

1. Start the development server:
```bash
flask run
```

2. Access the application at `http://localhost:5000`

3. Register as a delivery boy or admin user

4. Log in to access the dashboard

## Admin Features

### Managing Locations
- Add new delivery locations using the Google Maps interface
- View all existing locations
- Delete locations (if they have no active deliveries)

### Assigning Deliveries
- Create new delivery assignments
- Select delivery boy and location
- Add customer details and notes
- Track delivery status
- View delivery history

## Delivery Boy Features

- View assigned deliveries
- Update delivery status
- Track earnings
- View delivery history

## API Endpoints

### Admin Endpoints
- `GET /admin/locations` - List all delivery locations
- `POST /admin/locations` - Add a new location
- `DELETE /admin/locations/<id>` - Delete a location
- `GET /admin/assign-delivery` - View delivery assignment form
- `POST /admin/assign-delivery` - Create a new delivery assignment
- `GET /admin/deliveries/<id>` - Get delivery details
- `DELETE /admin/deliveries/<id>` - Delete a delivery
- `POST /admin/deliveries/<id>/status` - Update delivery status

### Delivery Boy Endpoints
- `GET /dashboard` - View delivery boy dashboard
- `GET /api/deliveries/<id>` - Get delivery details
- `POST /api/delivery/<id>/status` - Update delivery status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 