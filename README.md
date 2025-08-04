
# Drop Me RVM Backend API

A Django REST API powering Drop Me's AI-driven Recycling Vending Machines (RVMs). This system enables user authentication, deposit tracking, and automatic reward calculation — all contributing to Egypt’s circular economy.

---

## About Drop Me

**Drop Me** is a circular-tech startup using AI and local manufacturing to make recycling **accessible and rewarding** across Egypt and the MENA region.

> *"Your waste can be your card for your supplies."*

---

## Features

### Authentication
- Secure user registration & token-based login
- Session management and logout endpoint

### Deposit & Reward System
- Real-time tracking of recycling deposits
- Automated reward calculation:  
  `Points = Weight (kg) × Points per Material`
  - Plastic: 1.0 pts/kg  
  - Glass: 2.0 pts/kg  
  - Metal: 3.0 pts/kg

### Analytics & Dashboard
- User deposit history and statistics
- Admin panel with system-wide analytics

### Machine Management
- Live status tracking of RVM machines
- GPS-based location management

---

## Tech Stack

- **Framework:** Django 4.2.7  
- **API:** Django REST Framework 3.14  
- **Auth:** Token-based  
- **Database:** SQLite (default, configurable)  
- **Testing:** Unit + integration test suite  

---

## Installation

### Requirements
- Python ≥ 3.8  
- `pip` package manager  

### Setup

```bash
git clone https://github.com/HalaMohamed1/DropMe-RVM-API.git
cd DropMe-RVM-API
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Migrate & Seed DB

```bash
python manage.py makemigrations
python manage.py migrate
python scripts/setup_database.py  # adds test user, materials, and RVM machines
```

### Run Server

```bash
python manage.py runserver
```

> The API will be available at:  
> `http://localhost:8000/api/`

---

## API Overview

### Auth
- `POST /api/auth/register/`  
- `POST /api/auth/login/`  
- `POST /api/auth/logout/`  

### Recycling
- `POST /api/deposits/` – Submit deposit  
- `GET /api/deposits/history/` – View history  
- `GET /api/user/summary/` – User stats  

### Materials & Machines
- `GET /api/materials/`  
- `GET /api/machines/`  

---

## Testing

### Automated

```bash
python test.py
```

Covers login, data access, reward logic, token validation, and more.

---

## Test User

- **Username:** `testuser`  
- **Password:** `testpass123`

---

## Data Models

| Model        | Description                                  |
|--------------|----------------------------------------------|
| `Material`   | Types of recyclable materials with points    |
| `Machine`    | RVMs with location and status                |
| `UserProfile`| Extended user statistics                     |
| `Deposit`    | Tracks each recycling transaction            |

---

## Security Highlights

- Token-based authentication  
- Input validation & sanitization  
- Secure password hashing  
- CORS setup for frontend  
- DB transaction safety

---

## Project Structure

```
DropMe-RVM-API/
├── recycling/        # Main app
├── rvm_project/      # Django settings
├── scripts/          # Setup scripts
├── test.py           # Testing script
└── requirements.txt  # Dependencies
```

---

## Admin & Docs

- API Docs: `http://localhost:8000/api/`  
- Admin Panel: `http://localhost:8000/admin/`  
- Tests: `python test.py`

