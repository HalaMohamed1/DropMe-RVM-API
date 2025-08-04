# Drop Me RVM Backend API

A Django REST API for Drop Me's AI-driven Recycling Vending Machine platform. This system handles user authentication, deposit tracking, and automated reward calculations for Egypt's circular economy initiative.

## About Drop Me

Drop Me is a tech-powered circularity startup leveraging AI and local manufacturing to make recycling more accessible and rewarding across Egypt and the Middle East. Our mission: "Your waste can be your card for your supplies."

## Features

### Core Functionality
- Secure user registration and authentication with token-based sessions
- Automated deposit tracking with precise weight measurements
- Real-time reward calculations based on material type and weight
- Comprehensive user analytics and transaction history
- RVM machine location management and status tracking
- Administrative dashboard with system-wide analytics

### Reward System
The API calculates rewards automatically using this simple formula:

**Points Earned = Weight (kg) × Material Points per kg**

Current point values:
- Plastic: 1.0 points per kg
- Metal: 3.0 points per kg  
- Glass: 2.0 points per kg

### Additional Features
- Automatic user profile updates with each deposit
- Unique transaction IDs for all deposits
- Comprehensive input validation and error handling
- Paginated data retrieval for large datasets

## Technology Stack

- **Framework**: Django 4.2.7 with Django REST Framework 3.14.0
- **Authentication**: Token-based with automatic session management
- **API Design**: RESTful endpoints with JSON responses
- **Testing**: Comprehensive test suite included

## Installation

### Requirements
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone and prepare environment**
   \`\`\`bash
   git clone https://github.com/HalaMohamed1/DropMe-RVM-API.git
   cd DropMe-RVM-API
   python -m venv venv
   \`\`\`

2. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Setup database**
   \`\`\`bash
   python manage.py makemigrations
   python manage.py migrate
   \`\`\`

4. **Initialize sample data**
   \`\`\`bash
   python scripts/setup_database.py
   \`\`\`
   This creates sample materials, machines, and a test user account.

5. **Start the server**
   \`\`\`bash
   python manage.py runserver
   \`\`\`

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Create new user account
- `POST /api/auth/login/` - User login (returns authentication token)
- `POST /api/auth/logout/` - User logout (invalidates token)

### Data Access
- `GET /api/materials/` - List available recyclable materials
- `GET /api/machines/` - List active RVM machines

### Deposits
- `POST /api/deposits/` - Record new recycling deposit
- `GET /api/deposits/history/` - Get user's deposit history

### User Information
- `GET /api/user/summary/` - Get user's recycling statistics

### System
- `GET /api/` - API documentation and welcome

## Testing

### Automated Testing
Run the complete test suite:
\`\`\`bash
python test.py
\`\`\`

This verifies:
- User authentication (login/logout)
- Material and machine data access
- Reward calculation accuracy
- User summary generation
- Token security and invalidation

### Manual Testing with PowerShell

**User Login:**
\`\`\`powershell
$loginData = @{
    username = "testuser"
    password = "testpass123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginData

$token = $response.token
Write-Host "Login successful. Token: $token"
\`\`\`

**Get Materials:**
\`\`\`powershell
$headers = @{
    "Authorization" = "Token $token"
}

$materials = Invoke-RestMethod -Uri "http://localhost:8000/api/materials/" `
    -Method GET `
    -Headers $headers

$materials | ConvertTo-Json -Depth 3
\`\`\`

**Create Deposit:**
\`\`\`powershell
$depositData = @{
    weight_kg = 2.5
    material_name = "Plastic"
    machine_id = "RVM-001"
    notes = "Plastic bottles"
} | ConvertTo-Json

$deposit = Invoke-RestMethod -Uri "http://localhost:8000/api/deposits/" `
    -Method POST `
    -ContentType "application/json" `
    -Headers $headers `
    -Body $depositData

Write-Host "Deposit created successfully!"
$deposit | ConvertTo-Json -Depth 3
\`\`\`

**Get User Summary:**
\`\`\`powershell
$summary = Invoke-RestMethod -Uri "http://localhost:8000/api/user/summary/" `
    -Method GET `
    -Headers $headers

Write-Host "User Summary:"
$summary | ConvertTo-Json -Depth 3
\`\`\`

**User Logout:**
\`\`\`powershell
$logoutResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/logout/" `
    -Method POST `
    -Headers $headers

Write-Host "Logout successful: $($logoutResponse.message)"
\`\`\`

### Manual Testing with Python

For cross-platform testing, you can also use this Python script:

\`\`\`python
import requests

# Login
login_response = requests.post("http://localhost:8000/api/auth/login/", json={
    "username": "testuser",
    "password": "testpass123"
})
token = login_response.json()['token']
headers = {"Authorization": f"Token {token}"}

# Get materials
materials = requests.get("http://localhost:8000/api/materials/", headers=headers)
print("Materials:", materials.json())

# Create deposit
deposit_data = {
    "weight_kg": 2.5,
    "material_name": "Plastic",
    "machine_id": "RVM-001",
    "notes": "Test deposit"
}
deposit = requests.post("http://localhost:8000/api/deposits/", json=deposit_data, headers=headers)
print("Deposit:", deposit.json())

# Get user summary
summary = requests.get("http://localhost:8000/api/user/summary/", headers=headers)
print("Summary:", summary.json())

# Logout
logout = requests.post("http://localhost:8000/api/auth/logout/", headers=headers)
print("Logout:", logout.json())
\`\`\`

### Test Account
The setup script creates a test user:
- Username: `testuser`
- Password: `testpass123`

## Data Models

The system uses four main data models:

1. **Material** - Recyclable material types with point values and descriptions
2. **Machine** - RVM machine locations with GPS coordinates and status
3. **UserProfile** - Extended user data with recycling totals and statistics
4. **Deposit** - Individual recycling transactions with automatic calculations

## Security

- Token-based authentication with automatic token generation
- Comprehensive input validation and sanitization
- Secure password handling using Django's built-in systems
- CORS configuration for frontend integration
- Database transaction integrity for consistent data

### Project Structure
\`\`\`
DropMe-RVM-API/
├── rvm_project/          # Django settings
├── recycling/            # Main application
├── scripts/              # Setup scripts
├── test.py               # Test suite
└── requirements.txt      # Dependencies
\`\`\`

### Contributing
- Follow Django REST Framework best practices
- Maintain test coverage for new features
- Use proper error handling and validation
- Document API changes clearly

## Support

- API documentation: `/api/`
- Admin interface: `/admin/`
- Test verification: `python test.py`

---

**Drop Me RVM Backend API** - Version 1.0.0  
Built with Django REST Framework for Egypt's recycling revolution.
