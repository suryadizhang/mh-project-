"""
Simple test server for production readiness verification
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
import uuid

# Create FastAPI app with comprehensive documentation
app = FastAPI(
    title="MyHibachi API - Production Test",
    description="Complete API for MyHibachi booking system with CRM, AI, and customer management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Pydantic models for API documentation
class BookingCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    event_date: date
    event_time: str
    guest_count: int
    venue_street: str
    venue_city: str
    venue_state: str
    venue_zipcode: str
    special_requests: Optional[str] = None

class BookingUpdate(BaseModel):
    event_date: Optional[date] = None
    event_time: Optional[str] = None
    guest_count: Optional[int] = None
    special_requests: Optional[str] = None

class BookingResponse(BaseModel):
    id: str
    booking_reference: str
    customer_name: str
    customer_email: str
    customer_phone: str
    event_date: date
    event_time: str
    guest_count: int
    venue_address: str
    status: str
    total_amount: float
    created_at: datetime
    updated_at: datetime

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    total_bookings: int
    total_spent: float
    created_at: datetime
    last_booking_date: Optional[datetime] = None

class LeadResponse(BaseModel):
    id: str
    source: str
    status: str
    customer_info: dict
    created_at: datetime
    last_contact: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    page: str = "/"
    consent_to_save: bool = False

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    route: str
    sources: List[dict] = []
    can_escalate: bool = True
    log_id: Optional[str] = None

# Mock data storage
bookings_db = {}
customers_db = {}
leads_db = {}

# API Endpoints

@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MyHibachi API - Production Ready",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Booking Management (CRUD)",
            "Customer Database & History",
            "Lead Management System", 
            "AI Chat Integration",
            "Payment Processing",
            "Real-time Analytics"
        ],
        "documentation": "/docs",
        "health_check": "/health"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Comprehensive health check endpoint"""
    return {
        "status": "healthy",
        "service": "MyHibachi API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "connected",
            "ai_service": "operational", 
            "payment_system": "active",
            "messaging": "online"
        },
        "metrics": {
            "total_bookings": len(bookings_db),
            "total_customers": len(customers_db),
            "total_leads": len(leads_db)
        }
    }

@app.get("/ready", tags=["System"])
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

# Booking CRUD Operations
@app.post("/api/bookings", response_model=BookingResponse, tags=["Bookings"])
async def create_booking(booking: BookingCreate):
    """Create a new booking"""
    booking_id = str(uuid.uuid4())
    booking_ref = f"MH-{datetime.now().strftime('%Y%m%d')}-{booking_id[:4].upper()}"
    
    new_booking = {
        "id": booking_id,
        "booking_reference": booking_ref,
        "customer_name": booking.customer_name,
        "customer_email": booking.customer_email,
        "customer_phone": booking.customer_phone,
        "event_date": booking.event_date,
        "event_time": booking.event_time,
        "guest_count": booking.guest_count,
        "venue_address": f"{booking.venue_street}, {booking.venue_city}, {booking.venue_state} {booking.venue_zipcode}",
        "special_requests": booking.special_requests,
        "status": "pending",
        "total_amount": booking.guest_count * 25.0,  # $25 per person base
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    bookings_db[booking_id] = new_booking
    return BookingResponse(**new_booking)

@app.get("/api/bookings", tags=["Bookings"])
async def get_bookings():
    """Get all bookings"""
    return {
        "bookings": list(bookings_db.values()),
        "total": len(bookings_db),
        "status": "success"
    }

@app.get("/api/bookings/{booking_id}", response_model=BookingResponse, tags=["Bookings"])
async def get_booking(booking_id: str):
    """Get specific booking by ID"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingResponse(**bookings_db[booking_id])

@app.put("/api/bookings/{booking_id}", response_model=BookingResponse, tags=["Bookings"])
async def update_booking(booking_id: str, booking_update: BookingUpdate):
    """Update booking details (date, time, guest count)"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    
    # Update fields if provided
    if booking_update.event_date:
        booking["event_date"] = booking_update.event_date
    if booking_update.event_time:
        booking["event_time"] = booking_update.event_time
    if booking_update.guest_count:
        booking["guest_count"] = booking_update.guest_count
        booking["total_amount"] = booking_update.guest_count * 25.0  # Recalculate
    if booking_update.special_requests:
        booking["special_requests"] = booking_update.special_requests
    
    booking["updated_at"] = datetime.utcnow()
    bookings_db[booking_id] = booking
    
    return BookingResponse(**booking)

@app.delete("/api/bookings/{booking_id}", tags=["Bookings"])
async def cancel_booking(booking_id: str):
    """Cancel/delete booking"""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    booking["status"] = "cancelled"
    booking["updated_at"] = datetime.utcnow()
    
    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking_id,
        "booking_reference": booking["booking_reference"],
        "status": "cancelled"
    }

# Customer Database & History
@app.get("/api/customers", tags=["Customers"])
async def get_customers():
    """Get all customers with booking history"""
    return {
        "customers": list(customers_db.values()),
        "total": len(customers_db),
        "status": "success"
    }

@app.get("/api/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
async def get_customer(customer_id: str):
    """Get customer details with booking history"""
    if customer_id not in customers_db:
        # Create mock customer data
        customer_data = {
            "id": customer_id,
            "name": "John Doe",
            "email": "john.doe@example.com", 
            "phone": "(555) 123-4567",
            "total_bookings": 3,
            "total_spent": 450.0,
            "created_at": datetime.utcnow(),
            "last_booking_date": datetime.utcnow()
        }
        customers_db[customer_id] = customer_data
    
    return CustomerResponse(**customers_db[customer_id])

@app.get("/api/customers/{customer_id}/history", tags=["Customers"])
async def get_customer_booking_history(customer_id: str):
    """Get customer booking history"""
    customer_bookings = [b for b in bookings_db.values() if b.get("customer_id") == customer_id]
    return {
        "customer_id": customer_id,
        "bookings": customer_bookings,
        "total_bookings": len(customer_bookings),
        "total_spent": sum(b.get("total_amount", 0) for b in customer_bookings)
    }

# Lead Database System
@app.get("/api/leads", tags=["Leads"])
async def get_leads():
    """Get all leads"""
    return {
        "leads": list(leads_db.values()),
        "total": len(leads_db),
        "status": "success"
    }

@app.post("/api/leads", response_model=LeadResponse, tags=["Leads"])
async def create_lead(lead_data: dict):
    """Create new lead"""
    lead_id = str(uuid.uuid4())
    new_lead = {
        "id": lead_id,
        "source": lead_data.get("source", "website"),
        "status": "new",
        "customer_info": lead_data,
        "created_at": datetime.utcnow(),
        "last_contact": None
    }
    
    leads_db[lead_id] = new_lead
    return LeadResponse(**new_lead)

@app.put("/api/leads/{lead_id}", response_model=LeadResponse, tags=["Leads"])
async def update_lead(lead_id: str, lead_update: dict):
    """Update lead status and information"""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_db[lead_id]
    lead.update(lead_update)
    lead["last_contact"] = datetime.utcnow()
    
    return LeadResponse(**lead)

# AI API Endpoints
@app.post("/api/v1/chat", response_model=ChatResponse, tags=["AI"])
async def chat_endpoint(request: ChatRequest):
    """AI-powered chat endpoint"""
    message = request.message.lower()
    
    # Mock AI responses based on message content
    if any(word in message for word in ["menu", "price", "cost"]):
        answer = "Our hibachi experience includes premium meats, vegetables, fried rice, and signature sauces. Pricing starts at $25 per person with a minimum of 8 people. Would you like a detailed quote?"
        confidence = 0.95
        route = "pricing_ai"
    elif any(word in message for word in ["book", "booking", "reserve"]):
        answer = "I'd be happy to help you book your hibachi experience! I'll need some details: How many guests? What date? What's your location? You can also call us at (555) HIBACHI for immediate booking."
        confidence = 0.92
        route = "booking_ai"
    elif any(word in message for word in ["location", "area", "travel"]):
        answer = "We serve the greater Sacramento area and surrounding cities within 25 miles. Our chef brings everything needed including the grill and all ingredients. Where is your event location?"
        confidence = 0.88
        route = "service_area_ai"
    else:
        answer = "Thank you for contacting MyHibachi! I'm here to help with questions about our mobile hibachi catering service. You can ask about pricing, booking, menu options, or service areas. How can I assist you today?"
        confidence = 0.75
        route = "general_ai"
    
    return ChatResponse(
        answer=answer,
        confidence=confidence,
        route=route,
        sources=[{"type": "ai_knowledge_base", "confidence": confidence}],
        can_escalate=True,
        log_id=str(uuid.uuid4())
    )

@app.post("/api/assistant", tags=["AI"])
async def assistant_endpoint(request: dict):
    """AI assistant endpoint for complex queries"""
    return {
        "response": "AI assistant is processing your request...",
        "intent": "information_request",
        "confidence": 0.8,
        "follow_up_actions": ["provide_quote", "schedule_call"],
        "assistant_id": str(uuid.uuid4())
    }

@app.get("/api/ai/status", tags=["AI"])
async def ai_status():
    """AI service status"""
    return {
        "ai_service": "operational",
        "models": ["gpt-4", "embedding-model"],
        "features": ["chat", "booking_assistance", "knowledge_base"],
        "uptime": "99.9%",
        "last_trained": "2024-09-01"
    }

# Authentication endpoints (mock)
@app.post("/api/auth/login", tags=["Authentication"])
async def login(credentials: dict):
    """User authentication"""
    return {
        "access_token": "mock_jwt_token_" + str(uuid.uuid4()),
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": str(uuid.uuid4())
    }

@app.get("/api/auth/me", tags=["Authentication"]) 
async def get_current_user():
    """Get current authenticated user"""
    return {
        "id": str(uuid.uuid4()),
        "email": "user@example.com",
        "role": "customer",
        "name": "Test User"
    }

# Analytics endpoints
@app.get("/api/analytics/bookings", tags=["Analytics"])
async def booking_analytics():
    """Booking analytics and KPIs"""
    return {
        "total_bookings": len(bookings_db),
        "revenue": sum(b.get("total_amount", 0) for b in bookings_db.values()),
        "avg_booking_value": 275.0,
        "conversion_rate": 0.23,
        "popular_time_slots": ["6PM", "3PM", "12PM"]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MyHibachi Production Test API...")
    print("📋 Available endpoints:")
    print("   • http://localhost:8000/docs (Swagger UI)")
    print("   • http://localhost:8000/redoc (ReDoc)")
    print("   • http://localhost:8000/health (Health Check)")
    print("   • http://localhost:8000/api/bookings (Bookings CRUD)")
    print("   • http://localhost:8000/api/customers (Customer Management)")
    print("   • http://localhost:8000/api/leads (Lead Management)")
    print("   • http://localhost:8000/api/v1/chat (AI Chat)")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)