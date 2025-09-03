from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date, timedelta
from enum import Enum
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MyHibachi Booking API",
    description="Professional hibachi booking system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://myhibachi.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class TimeSlot(str, Enum):
    TWELVE_PM = "12PM"
    THREE_PM = "3PM"
    SIX_PM = "6PM"
    NINE_PM = "9PM"

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

# Pydantic Models
class BookingCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Customer full name")
    email: str = Field(..., description="Customer email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Customer phone number")
    event_date: date = Field(..., description="Event date (YYYY-MM-DD)")
    event_time: TimeSlot = Field(..., description="Event time slot")
    address_street: str = Field(..., min_length=1, max_length=200, description="Customer street address")
    address_city: str = Field(..., min_length=1, max_length=100, description="Customer city")
    address_state: str = Field(..., min_length=2, max_length=50, description="Customer state")
    address_zipcode: str = Field(..., min_length=5, max_length=10, description="Customer zipcode")
    venue_street: str = Field(..., min_length=1, max_length=200, description="Event venue street address")
    venue_city: str = Field(..., min_length=1, max_length=100, description="Event venue city")
    venue_state: str = Field(..., min_length=2, max_length=50, description="Event venue state")
    venue_zipcode: str = Field(..., min_length=5, max_length=10, description="Event venue zipcode")

    @validator('event_date')
    def validate_event_date(cls, v):
        today = date.today()
        min_date = today + timedelta(days=2)
        if v < min_date:
            raise ValueError('Event date must be at least 2 days in advance')
        return v

    @validator('email')
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError('Phone number must contain at least 10 digits')
        return v

class BookingResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    event_date: date
    event_time: TimeSlot
    address_street: str
    address_city: str
    address_state: str
    address_zipcode: str
    venue_street: str
    venue_city: str
    venue_state: str
    venue_zipcode: str
    status: BookingStatus
    created_at: datetime

class BookingSummary(BaseModel):
    id: str
    name: str
    email: str
    event_date: date
    event_time: TimeSlot
    status: BookingStatus
    created_at: datetime

class AvailabilityCheck(BaseModel):
    available: bool
    date: date
    time: TimeSlot
    reason: Optional[str] = None

class BookingCreateResponse(BaseModel):
    id: str
    message: str
    booking: dict

class ErrorResponse(BaseModel):
    detail: str
    errors: Optional[List[dict]] = None

# In-memory storage (replace with database in production)
bookings_storage: List[BookingResponse] = []

def generate_booking_id() -> str:
    """Generate a unique booking ID"""
    return str(uuid.uuid4())

def is_time_slot_available(event_date: date, event_time: TimeSlot) -> bool:
    """Check if a time slot is available"""
    return not any(
        booking.event_date == event_date and 
        booking.event_time == event_time and 
        booking.status != BookingStatus.CANCELLED
        for booking in bookings_storage
    )

# API Routes
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "MyHibachi Booking API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/bookings/check", response_model=AvailabilityCheck, tags=["Bookings"])
async def check_availability(
    date: date = Query(..., description="Event date (YYYY-MM-DD)"),
    time: TimeSlot = Query(..., description="Event time slot")
):
    """Check if a specific date and time slot is available"""
    try:
        # Validate date is at least 2 days in advance
        today = date.today()
        min_date = today + timedelta(days=2)
        
        if date < min_date:
            return AvailabilityCheck(
                available=False,
                date=date,
                time=time,
                reason="Date must be at least 2 days in advance"
            )
        
        # Check if time slot is available
        available = is_time_slot_available(date, time)
        
        return AvailabilityCheck(
            available=available,
            date=date,
            time=time,
            reason=None if available else "Time slot is already booked"
        )
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/bookings", response_model=BookingCreateResponse, tags=["Bookings"])
async def create_booking(booking_data: BookingCreate):
    """Create a new hibachi booking"""
    try:
        # Check if time slot is still available
        if not is_time_slot_available(booking_data.event_date, booking_data.event_time):
            raise HTTPException(
                status_code=409, 
                detail="This time slot is already booked"
            )
        
        # Create new booking
        booking_id = generate_booking_id()
        new_booking = BookingResponse(
            id=booking_id,
            name=booking_data.name,
            email=booking_data.email,
            phone=booking_data.phone,
            event_date=booking_data.event_date,
            event_time=booking_data.event_time,
            address_street=booking_data.address_street,
            address_city=booking_data.address_city,
            address_state=booking_data.address_state,
            address_zipcode=booking_data.address_zipcode,
            venue_street=booking_data.venue_street,
            venue_city=booking_data.venue_city,
            venue_state=booking_data.venue_state,
            venue_zipcode=booking_data.venue_zipcode,
            status=BookingStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Save booking
        bookings_storage.append(new_booking)
        
        logger.info(f"Created booking {booking_id} for {booking_data.name}")
        
        return BookingCreateResponse(
            id=booking_id,
            message="Booking created successfully! We will contact you within 1-2 hours to confirm your hibachi experience.",
            booking={
                "id": booking_id,
                "event_date": booking_data.event_date.isoformat(),
                "event_time": booking_data.event_time,
                "status": BookingStatus.PENDING
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/bookings", response_model=List[BookingSummary], tags=["Bookings"])
async def get_all_bookings():
    """Get all bookings (admin endpoint - should be protected with authentication in production)"""
    try:
        return [
            BookingSummary(
                id=booking.id,
                name=booking.name,
                email=booking.email,
                event_date=booking.event_date,
                event_time=booking.event_time,
                status=booking.status,
                created_at=booking.created_at
            )
            for booking in bookings_storage
        ]
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/bookings/{booking_id}", response_model=BookingResponse, tags=["Bookings"])
async def get_booking(booking_id: str):
    """Get a specific booking by ID"""
    try:
        booking = next((b for b in bookings_storage if b.id == booking_id), None)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching booking {booking_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/api/v1/bookings/{booking_id}/status", tags=["Bookings"])
async def update_booking_status(booking_id: str, status: BookingStatus):
    """Update booking status (admin endpoint)"""
    try:
        booking = next((b for b in bookings_storage if b.id == booking_id), None)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking.status = status
        logger.info(f"Updated booking {booking_id} status to {status}")
        
        return {"message": f"Booking status updated to {status}", "booking_id": booking_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking {booking_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    print("⚠️  DEPRECATED/LEGACY BACKEND - Use myhibachi-backend-fastapi for new features")
    print("🔗 Running on port 8001 (legacy)")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
