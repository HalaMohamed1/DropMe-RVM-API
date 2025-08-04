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

\`\`\`bash
git clone https://github.com/HalaMohamed1/DropMe-RVM-API.git
cd DropMe-RVM-API
python -m venv venv
pip install -r requirements.txt
\`\`\`

### Migrate & Seed DB

\`\`\`bash
python manage.py makemigrations
python manage.py migrate
python scripts/setup_database.py  # adds test user, materials, and RVM machines
\`\`\`

### Run Server

\`\`\`bash
python manage.py runserver
\`\`\`

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

## Architecture & Guarantees

### Robustness & Reliability
The API is designed for high performance and long-term stability through several mechanisms:
-   **Asynchronous Tasks**: Utilizes Celery with Redis as a message broker to offload heavy or time-consuming operations (e.g., analytics processing, token cleanup) to background tasks, preventing them from blocking the main API thread.
-   **Caching**: Leverages Redis for caching frequently accessed data and session management, reducing database load and improving response times.
-   **Database Connection Pooling**: Configured for PostgreSQL in production settings (`rvm_project/settings_production.py`) to efficiently manage database connections, ensuring stability under high concurrent requests.
-   **Input Validation**: Comprehensive validation at the serializer level and custom utility validators (`recycling/utils/validators.py`) ensure data integrity and reject malformed or suspicious requests early.
-   **Transaction Integrity**: Database operations for critical actions like deposit creation are wrapped in atomic transactions (`@transaction.atomic` in `recycling/views.py`) to ensure data consistency.
-   **Logging & Monitoring**: Detailed logging (including JSON format for production) and system health monitoring tasks (`recycling/tasks.py`, `recycling/views.py` health check) provide visibility into API performance and potential issues, enabling proactive intervention.
-   **Middleware**: `PerformanceMiddleware` (`recycling/middleware.py`) monitors request durations and logs slow requests, adding `X-Response-Time` headers for external monitoring.

### Security
Security is a paramount concern, addressed through:
-   **Token-Based Authentication**: Users authenticate once to receive a token, which is then used for subsequent requests, avoiding repeated credential transmission.
-   **Secure Password Handling**: Django's built-in authentication system handles password hashing and security best practices.
-   **Token Invalidation/Blacklisting**: Tokens are explicitly invalidated upon logout and can be blacklisted (`TokenValidationMiddleware` in `recycling/middleware.py`), preventing their reuse.
-   **Strict Authorization**: Django REST Framework permissions (`IsAuthenticated`, `IsAdminUser`) and custom logic (e.g., `is_staff` checks for admin endpoints) ensure only authorized users can access specific resources.
-   **Sensitive Endpoint Protection**: Admin-only endpoints like `/api/admin/stats/` are strictly protected. The `BrowsableAPIRenderer` is removed in production settings (`rvm_project/settings_production.py`) to prevent accidental exposure of API details.
-   **CORS Configuration**: Properly configured (`django-cors-headers`) to allow controlled access from frontend applications.
-   **HTTPS Enforcement**: Production settings (`rvm_project/settings_production.py`) enforce HTTPS redirection and HSTS to ensure all communication is encrypted.
-   **Information Disclosure Prevention**: Debug information is disabled in production (`DEBUG=False`), and error responses are generic to prevent leakage of internal system details.
-   **XSS & SQL Injection Protection**: Django's ORM and serializer validation inherently protect against common injection attacks, and additional custom validators are in place.

### Testability
Confidence in the codebase and prevention of regressions are maintained through a robust testing strategy:
-   **Comprehensive Test Suite**: The project includes multiple types of tests:
    -   `test.py`: Basic functional tests for core API flows and reward calculation accuracy.
    -   `test_production.py`: Comprehensive tests covering basic functionality, security, performance, and concurrent requests, simulating a production environment.
    -   `test_security.py`: Dedicated tests for common vulnerabilities like SQL injection, XSS and authentication bypass.
    -   `load_test.py`: Scripts to simulate high user loads and measure API performance under stress.
-   **Modular Design**: The codebase is structured into logical components (models, serializers, views, middleware, utilities, tasks), promoting separation of concerns and making individual units easier to test in isolation.
-   **Clear Error Handling**: Consistent error responses with specific error codes facilitate debugging and testing of failure scenarios.
-   **Automated Testing**: All tests are designed to be run automatically, allowing for continuous integration and rapid feedback on code changes.

---

## Testing

### Automated

\`\`\`bash
python test.py
\`\`\`

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

\`\`\`
DropMe-RVM-API/
├── recycling/        # Main app
├── rvm_project/      # Django settings
├── scripts/          # Setup scripts
├── test.py           # Testing script
└── requirements.txt  # Dependencies
\`\`\`

---

## Admin & Docs

- API Docs: `http://localhost:8000/api/`  
- Admin Panel: `http://localhost:8000/admin/`  
- Tests: `python test.py`
