#!/usr/bin/env python3
"""
Comprehensive Test API Server for MH Webapps Production Readiness Check
Includes: Booking CRUD, Customer History, Lead Database, AI API, Swagger Documentation
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
import uvicorn
from enum import Enum

# Initialize FastAPI app with documentation
app = FastAPI(
    title="MH Webapps Production Test API",
    description="Comprehensive API for booking management, customer history, lead tracking, and AI integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enums
class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"

# Data Models
class BookingCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    event_date: date
    event_time: time
    guest_count: int
    venue: str
    special_requests: Optional[str] = None

class BookingUpdate(BaseModel):
    event_date: Optional[date] = None
    event_time: Optional[time] = None
    guest_count: Optional[int] = None
    venue: Optional[str] = None
    special_requests: Optional[str] = None
    status: Optional[BookingStatus] = None

class Booking(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: str
    event_date: date
    event_time: time
    guest_count: int
    venue: str
    special_requests: Optional[str]
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    total_amount: float

class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: str
    address: Optional[str] = None

class Customer(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    address: Optional[str]
    total_bookings: int
    total_spent: float
    created_at: datetime

class LeadCreate(BaseModel):
    name: str
    email: str  
    phone: str
    source: str
    notes: Optional[str] = None

class Lead(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    source: str
    status: LeadStatus
    notes: Optional[str]
    created_at: datetime

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# In-memory storage
bookings_db = {}
customers_db = {}
leads_db = {}
counter = 1

# Sample data
sample_booking = Booking(
    id=1,
    customer_name="John Doe",
    customer_email="john@test.com",
    customer_phone="555-0123",
    event_date=date(2024, 2, 15),
    event_time=time(18, 30),
    guest_count=4,
    venue="Main Hall",
    special_requests="Window table",
    status=BookingStatus.CONFIRMED,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    total_amount=200.0
)
bookings_db[1] = sample_booking

@app.get("/")
async def root():
    return {
        "message": "MH Webapps Production Test API",
        "status": "healthy",
        "endpoints": ["/docs", "/bookings/", "/customers/", "/leads/", "/ai/"]
    }

# BOOKING CRUD OPERATIONS
@app.post("/bookings/", response_model=Booking, tags=["Bookings"])
async def create_booking(booking: BookingCreate):
    global counter
    new_booking = Booking(
        id=counter,
        customer_name=booking.customer_name,
        customer_email=booking.customer_email,
        customer_phone=booking.customer_phone,
        event_date=booking.event_date,
        event_time=booking.event_time,
        guest_count=booking.guest_count,
        venue=booking.venue,
        special_requests=booking.special_requests,
        status=BookingStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        total_amount=booking.guest_count * 50.0
    )
    bookings_db[counter] = new_booking
    counter += 1
    return new_booking

@app.get("/bookings/", response_model=List[Booking], tags=["Bookings"])
async def get_all_bookings():
    return list(bookings_db.values())

@app.get("/bookings/{booking_id}", response_model=Booking, tags=["Bookings"])
async def get_booking(booking_id: int):
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    return bookings_db[booking_id]

@app.put("/bookings/{booking_id}", response_model=Booking, tags=["Bookings"])
async def update_booking(booking_id: int, booking_update: BookingUpdate):
    """Update booking - change date/time, guest count as requested"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    
    if booking_update.event_date is not None:
        booking.event_date = booking_update.event_date
    if booking_update.event_time is not None:
        booking.event_time = booking_update.event_time
    if booking_update.guest_count is not None:
        booking.guest_count = booking_update.guest_count
        booking.total_amount = booking.guest_count * 50.0
    if booking_update.status is not None:
        booking.status = booking_update.status
    
    booking.updated_at = datetime.now()
    return booking

@app.delete("/bookings/{booking_id}", tags=["Bookings"])
async def cancel_booking(booking_id: int):
    """Cancel booking - DELETE operation as requested"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    booking.status = BookingStatus.CANCELLED
    booking.updated_at = datetime.now()
    
    return {"message": f"Booking {booking_id} cancelled", "booking": booking}

# CUSTOMER DATABASE & HISTORY
@app.post("/customers/", response_model=Customer, tags=["Customers"])
async def create_customer(customer: CustomerCreate):
    global counter
    new_customer = Customer(
        id=counter,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        total_bookings=0,
        total_spent=0.0,
        created_at=datetime.now()
    )
    customers_db[counter] = new_customer
    counter += 1
    return new_customer

@app.get("/customers/", response_model=List[Customer], tags=["Customers"])
async def get_all_customers():
    return list(customers_db.values())

@app.get("/customers/{customer_id}/history", tags=["Customers"])
async def get_customer_history(customer_id: int):
    """Get customer history including bookings"""
    if customer_id not in customers_db:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = customers_db[customer_id]
    customer_bookings = [b for b in bookings_db.values() if b.customer_email == customer.email]
    
    return {
        "customer": customer,
        "bookings": customer_bookings,
        "total_bookings": len(customer_bookings),
        "total_spent": sum(b.total_amount for b in customer_bookings)
    }

# LEAD DATABASE
@app.post("/leads/", response_model=Lead, tags=["Leads"])
async def create_lead(lead: LeadCreate):
    global counter
    new_lead = Lead(
        id=counter,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=LeadStatus.NEW,
        notes=lead.notes,
        created_at=datetime.now()
    )
    leads_db[counter] = new_lead
    counter += 1
    return new_lead

@app.get("/leads/", response_model=List[Lead], tags=["Leads"])
async def get_all_leads():
    return list(leads_db.values())

@app.put("/leads/{lead_id}/convert", tags=["Leads"])
async def convert_lead(lead_id: int):
    """Convert lead to customer"""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_db[lead_id]
    lead.status = LeadStatus.CONVERTED
    
    # Create customer from lead
    global counter
    new_customer = Customer(
        id=counter,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        address=None,
        total_bookings=0,
        total_spent=0.0,
        created_at=datetime.now()
    )
    customers_db[counter] = new_customer
    counter += 1
    
    return {"message": "Lead converted to customer", "customer": new_customer}

# AI API TEST ENDPOINTS
@app.post("/ai/chat", response_model=ChatResponse, tags=["AI API"])
async def ai_chat(message: ChatMessage):
    """AI Chat for booking assistance"""
    user_message = message.message.lower()
    
    if "booking" in user_message:
        response = "I can help with bookings! What would you like to know?"
    elif "menu" in user_message:
        response = "Our hibachi menu features fresh ingredients and authentic flavors."
    elif "cancel" in user_message:
        response = "I can help cancel your booking. Please provide your booking ID."
    else:
        response = f"Thank you for your message. How can I help with your hibachi experience?"
    
    session_id = message.session_id or f"session_{datetime.now().timestamp()}"
    
    return ChatResponse(response=response, session_id=session_id)

@app.get("/ai/health", tags=["AI API"])
async def ai_health():
    return {"status": "operational", "endpoints": ["chat", "assistant"]}

# System endpoints
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "bookings": "operational",
            "customers": "operational", 
            "leads": "operational",
            "ai": "operational"
        },
        "counts": {
            "bookings": len(bookings_db),
            "customers": len(customers_db),
            "leads": len(leads_db)
        }
    }

if __name__ == "__main__":
    print("Starting MH Webapps Test API Server...")
    print("Features:")
    print("- Booking CRUD (Create, Read, Update, Delete)")
    print("- Customer database with history")
    print("- Lead database and conversion")
    print("- AI API endpoints")
    print("- Swagger docs at /docs")
    print("")
    print("Server starting at http://localhost:8001")
    print("Swagger documentation: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)