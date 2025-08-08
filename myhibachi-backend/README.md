# MyHibachi Backend API

FastAPI backend for the MyHibachi booking system.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- POST `/api/v1/bookings` - Create a new booking
- GET `/api/v1/bookings` - Get all bookings (admin)
- GET `/api/v1/bookings/check` - Check availability for date/time

## Database

Currently using in-memory storage for demonstration. In production, integrate with PostgreSQL.

## Environment Variables

Create a `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost/myhibachi
SECRET_KEY=your-secret-key
DEBUG=True
CORS_ORIGINS=http://localhost:3000,https://myhibachi.com
```
