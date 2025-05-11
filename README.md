# Delivery Management System

A Flask-based delivery management system that helps manage delivery boys, optimize routes, and track deliveries.

## Features

- User Authentication (Delivery Boys)
- Email Verification
- Delivery Boy Management
- Location Management
- Route Optimization
- Delivery Assignment
- Real-time Delivery Tracking
- Admin Dashboard

## Prerequisites

- Python 3.7+
- pip (Python package installer)
- SQLite3
- Gmail account (for email verification)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd delivery-management-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
FLASK_SECRET_KEY=your_secret_key_here
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

5. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
delivery-management-system/
├── app.py                 # Main application file
├── route_optimizer.py     # Route optimization logic
├── init_db.py            # Database initialization
├── requirements.txt      # Project dependencies
├── .env                 # Environment variables
├── templates/           # HTML templates
│   ├── admin/          # Admin templates
│   └── ...             # Other templates
└── tests/              # Test files
```

## Testing

Run the test suite:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 