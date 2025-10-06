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
import json

# Initialize FastAPI app with documentation
app = FastAPI(
    title="MH Webapps Production Test API",
    description="Comprehif __name__ == "__main__":
    print("Starting MH Webapps Production Test API Server...")
    print("Features included:")
    print("   - Booking CRUD operations (Create, Read, Update, Delete)")
    print("   - Customer database with history tracking")
    print("   - Lead database and management")
    print("   - AI API for chat and assistance")
    print("   - Swagger documentation at /docs")
    print("   - Analytics and health monitoring")
    print("")
    print("Server will be available at:")
    print("   - Main API: http://localhost:8001")
    print("   - Swagger Docs: http://localhost:8001/docs")
    print("   - ReDoc: http://localhost:8001/redoc")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)("🌐 Server will be available at:")
    print("   • Main API: http://localhost:8001")
    print("   • Swagger Docs: http://localhost:8001/docs")
    print("   • ReDoc: http://localhost:8001/redoc") for booking management, customer history, lead tracking, and AI integration",
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
    preferences: Optional[Dict[str, Any]] = None

class Customer(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    address: Optional[str]
    preferences: Optional[Dict[str, Any]]
    total_bookings: int
    total_spent: float
    created_at: datetime
    last_booking_date: Optional[datetime]

class CustomerHistory(BaseModel):
    customer: Customer
    bookings: List[Booking]
    payments: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]

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
    score: int
    created_at: datetime
    updated_at: datetime
    converted_at: Optional[datetime]

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    context: Optional[Dict[str, Any]] = None

# In-memory storage for testing
bookings_db = {}
customers_db = {}
leads_db = {}
booking_counter = 1
customer_counter = 1
lead_counter = 1

# Initialize with sample data
def initialize_sample_data():
    global booking_counter, customer_counter, lead_counter
    
    # Sample customer
    sample_customer = Customer(
        id=1,
        name="John Doe",
        email="john@example.com",
        phone="555-0123",
        address="123 Main St, City, State",
        preferences={"dietary": "vegetarian", "seating": "outdoor"},
        total_bookings=2,
        total_spent=450.00,
        created_at=datetime.now(),
        last_booking_date=datetime.now()
    )
    customers_db[1] = sample_customer
    customer_counter = 2
    
    # Sample booking
    sample_booking = Booking(
        id=1,
        customer_name="John Doe",
        customer_email="john@example.com",
        customer_phone="555-0123",
        event_date=date(2024, 2, 15),
        event_time=time(18, 30),
        guest_count=4,
        venue="Main Dining Room",
        special_requests="Window table preferred",
        status=BookingStatus.CONFIRMED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        total_amount=225.00
    )
    bookings_db[1] = sample_booking
    booking_counter = 2
    
    # Sample lead
    sample_lead = Lead(
        id=1,
        name="Jane Smith",
        email="jane@example.com",
        phone="555-0456",
        source="website",
        status=LeadStatus.QUALIFIED,
        notes="Interested in catering services",
        score=75,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        converted_at=None
    )
    leads_db[1] = sample_lead
    lead_counter = 2

# Initialize sample data
initialize_sample_data()

# Health Check
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "MH Webapps Production Test API",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "swagger_docs": "/docs",
            "redoc": "/redoc",
            "booking_crud": "/bookings/",
            "customer_history": "/customers/",
            "lead_database": "/leads/",
            "ai_api": "/ai/"
        }
    }

# BOOKING CRUD OPERATIONS (As requested by user)
@app.post("/bookings/", response_model=Booking, tags=["Bookings"])
async def create_booking(booking: BookingCreate):
    """Create a new booking"""
    global booking_counter
    
    new_booking = Booking(
        id=booking_counter,
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
        total_amount=booking.guest_count * 50.0  # Sample pricing
    )
    
    bookings_db[booking_counter] = new_booking
    booking_counter += 1
    
    return new_booking

@app.get("/bookings/", response_model=List[Booking], tags=["Bookings"])
async def get_all_bookings():
    """Get all bookings"""
    return list(bookings_db.values())

@app.get("/bookings/{booking_id}", response_model=Booking, tags=["Bookings"])
async def get_booking(booking_id: int):
    """Get a specific booking by ID"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    return bookings_db[booking_id]

@app.put("/bookings/{booking_id}", response_model=Booking, tags=["Bookings"])
async def update_booking(booking_id: int, booking_update: BookingUpdate):
    """Update booking details (date/time, guest count, etc.) - PUT operation as requested"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    
    # Update fields if provided
    if booking_update.event_date is not None:
        booking.event_date = booking_update.event_date
    if booking_update.event_time is not None:
        booking.event_time = booking_update.event_time
    if booking_update.guest_count is not None:
        booking.guest_count = booking_update.guest_count
        booking.total_amount = booking.guest_count * 50.0  # Recalculate amount
    if booking_update.venue is not None:
        booking.venue = booking_update.venue
    if booking_update.special_requests is not None:
        booking.special_requests = booking_update.special_requests
    if booking_update.status is not None:
        booking.status = booking_update.status
    
    booking.updated_at = datetime.now()
    bookings_db[booking_id] = booking
    
    return booking

@app.delete("/bookings/{booking_id}", tags=["Bookings"])
async def cancel_booking(booking_id: int):
    """Cancel/Delete booking - DELETE operation as requested"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Mark as cancelled instead of deleting for audit trail
    booking = bookings_db[booking_id]
    booking.status = BookingStatus.CANCELLED
    booking.updated_at = datetime.now()
    
    return {"message": f"Booking {booking_id} has been cancelled", "booking": booking}

# CUSTOMER DATABASE & HISTORY (As requested by user)
@app.post("/customers/", response_model=Customer, tags=["Customers"])
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    global customer_counter
    
    new_customer = Customer(
        id=customer_counter,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        preferences=customer.preferences,
        total_bookings=0,
        total_spent=0.0,
        created_at=datetime.now(),
        last_booking_date=None
    )
    
    customers_db[customer_counter] = new_customer
    customer_counter += 1
    
    return new_customer

@app.get("/customers/", response_model=List[Customer], tags=["Customers"])
async def get_all_customers():
    """Get all customers"""
    return list(customers_db.values())

@app.get("/customers/{customer_id}/history", response_model=CustomerHistory, tags=["Customers"])
async def get_customer_history(customer_id: int):
    """Get complete customer history including bookings, payments, messages"""
    if customer_id not in customers_db:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = customers_db[customer_id]
    
    # Get customer bookings
    customer_bookings = [
        booking for booking in bookings_db.values() 
        if booking.customer_email == customer.email
    ]
    
    # Mock payments and messages for demonstration
    payments = [
        {
            "id": 1,
            "booking_id": booking.id,
            "amount": booking.total_amount,
            "status": "completed",
            "date": booking.created_at.isoformat()
        }
        for booking in customer_bookings
    ]
    
    messages = [
        {
            "id": 1,
            "content": "Thank you for your booking!",
            "timestamp": datetime.now().isoformat(),
            "direction": "outbound"
        },
        {
            "id": 2,
            "content": "Looking forward to your event",
            "timestamp": datetime.now().isoformat(),
            "direction": "inbound"
        }
    ]
    
    return CustomerHistory(
        customer=customer,
        bookings=customer_bookings,
        payments=payments,
        messages=messages
    )

# LEAD DATABASE (As requested by user)
@app.post("/leads/", response_model=Lead, tags=["Leads"])
async def create_lead(lead: LeadCreate):
    """Create a new lead"""
    global lead_counter
    
    new_lead = Lead(
        id=lead_counter,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=LeadStatus.NEW,
        notes=lead.notes,
        score=50,  # Default score
        created_at=datetime.now(),
        updated_at=datetime.now(),
        converted_at=None
    )
    
    leads_db[lead_counter] = new_lead
    lead_counter += 1
    
    return new_lead

@app.get("/leads/", response_model=List[Lead], tags=["Leads"])
async def get_all_leads():
    """Get all leads"""
    return list(leads_db.values())

@app.get("/leads/{lead_id}", response_model=Lead, tags=["Leads"])
async def get_lead(lead_id: int):
    """Get a specific lead by ID"""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    return leads_db[lead_id]

@app.put("/leads/{lead_id}/convert", response_model=Lead, tags=["Leads"])
async def convert_lead_to_customer(lead_id: int):
    """Convert lead to customer"""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_db[lead_id]
    lead.status = LeadStatus.CONVERTED
    lead.converted_at = datetime.now()
    lead.updated_at = datetime.now()
    
    # Create customer from lead
    global customer_counter
    new_customer = Customer(
        id=customer_counter,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        address=None,
        preferences=None,
        total_bookings=0,
        total_spent=0.0,
        created_at=datetime.now(),
        last_booking_date=None
    )
    
    customers_db[customer_counter] = new_customer
    customer_counter += 1
    
    return lead

# AI API TEST ENDPOINTS (As requested by user)
@app.post("/ai/chat", response_model=ChatResponse, tags=["AI API"])
async def ai_chat(message: ChatMessage):
    """AI Chat endpoint for customer support and booking assistance"""
    
    # Mock AI response logic
    user_message = message.message.lower()
    
    if "booking" in user_message or "reservation" in user_message:
        response = "I can help you with bookings! Would you like to make a new reservation or modify an existing one?"
    elif "menu" in user_message or "food" in user_message:
        response = "Our menu features authentic hibachi cuisine with fresh ingredients. What type of dish interests you?"
    elif "price" in user_message or "cost" in user_message:
        response = "Our pricing starts at $50 per person. Would you like details about our different packages?"
    elif "cancel" in user_message:
        response = "I can help you cancel your booking. Please provide your booking ID or email address."
    else:
        response = f"Thank you for your message: '{message.message}'. How can I assist you with your hibachi dining experience today?"
    
    session_id = message.session_id or f"session_{datetime.now().timestamp()}"
    
    return ChatResponse(
        response=response,
        session_id=session_id,
        context={
            "timestamp": datetime.now().isoformat(),
            "user_message": message.message,
            "intent": "general_inquiry"
        }
    )

@app.get("/ai/knowledge-base", tags=["AI API"])
async def get_knowledge_base():
    """Get AI knowledge base information"""
    return {
        "knowledge_base": {
            "topics": ["bookings", "menu", "pricing", "locations", "events"],
            "languages": ["english"],
            "last_updated": datetime.now().isoformat(),
            "total_articles": 150,
            "categories": {
                "booking_help": 45,
                "menu_info": 30,
                "pricing": 20,
                "policies": 25,
                "general": 30
            }
        }
    }

@app.post("/ai/assistant", tags=["AI API"])
async def ai_assistant(request: Dict[str, Any]):
    """AI Assistant endpoint for complex queries and multi-step assistance"""
    
    query = request.get("query", "")
    context = request.get("context", {})
    
    return {
        "assistant_response": f"Processing your request: {query}",
        "suggested_actions": ["book_table", "view_menu", "check_availability"],
        "confidence": 0.95,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }

# Analytics and Reporting
@app.get("/analytics/dashboard", tags=["Analytics"])
async def get_analytics_dashboard():
    """Get analytics dashboard data"""
    total_bookings = len(bookings_db)
    total_customers = len(customers_db)
    total_leads = len(leads_db)
    
    confirmed_bookings = len([b for b in bookings_db.values() if b.status == BookingStatus.CONFIRMED])
    total_revenue = sum(b.total_amount for b in bookings_db.values() if b.status == BookingStatus.CONFIRMED)
    
    return {
        "metrics": {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "total_customers": total_customers,
            "total_leads": total_leads,
            "total_revenue": total_revenue,
            "conversion_rate": (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
        },
        "status": "operational",
        "last_updated": datetime.now().isoformat()
    }

# System Status
@app.get("/system/health", tags=["System"])
async def system_health():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "booking_system": "operational",
            "customer_database": "operational", 
            "lead_management": "operational",
            "ai_api": "operational"
        },
        "database": {
            "bookings": len(bookings_db),
            "customers": len(customers_db),
            "leads": len(leads_db)
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting MH Webapps Production Test API Server...")
    print("📋 Features included:")
    print("   ✅ Booking CRUD operations (Create, Read, Update, Delete)")
    print("   ✅ Customer database with history tracking")
    print("   ✅ Lead database and management")
    print("   ✅ AI API for chat and assistance")
    print("   ✅ Swagger documentation at /docs")
    print("   ✅ Analytics and health monitoring")
    print("\n🌐 Server will be available at:")
    print("   • Main API: http://localhost:8000")
    print("   • Swagger Docs: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)