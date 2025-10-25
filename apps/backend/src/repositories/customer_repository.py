"""
Customer Repository Implementation
Handles customer-specific data access patterns and business logic
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session
from enum import Enum

from core.repository import BaseRepository, FilterCriteria, SortCriteria
from core.exceptions import (
    NotFoundException, ConflictException, ValidationException,
    ErrorCode, raise_not_found, raise_validation_error, raise_conflict
)
from models.customer import Customer, CustomerStatus

class CustomerSearchFilters(str, Enum):
    """Available search filters for customers"""
    BY_EMAIL = "email"
    BY_PHONE = "phone"
    BY_NAME = "name"
    BY_STATUS = "status"
    BY_LOYALTY_TIER = "loyalty_tier"
    BY_DIETARY_PREFERENCES = "dietary_preferences"
    BY_REGISTRATION_DATE = "registration_date"
    BY_LAST_VISIT = "last_visit"

class CustomerRepository(BaseRepository[Customer]):
    """
    Repository for customer operations with specialized business logic
    
    Features:
    - Duplicate detection
    - Loyalty point management
    - Customer segmentation
    - Communication preferences
    - Profile completion tracking
    - Search and filtering
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Customer)
    
    # Specialized Find Methods
    
    def find_by_email(self, email: str, include_deleted: bool = False) -> Optional[Customer]:
        """Find customer by email address"""
        query = self.session.query(self.model).filter(
            func.lower(self.model.email) == func.lower(email.strip())
        )
        
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        return query.first()
    
    def find_by_phone(self, phone: str, include_deleted: bool = False) -> Optional[Customer]:
        """Find customer by phone number"""
        # Normalize phone number (remove non-digits)
        normalized_phone = ''.join(filter(str.isdigit, phone))
        
        query = self.session.query(self.model).filter(
            func.regexp_replace(self.model.phone, '[^0-9]', '', 'g') == normalized_phone
        )
        
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        return query.first()
    
    def search_by_name(
        self,
        search_term: str,
        limit: Optional[int] = 50
    ) -> List[Customer]:
        """Search customers by name (first or last)"""
        search_pattern = f"%{search_term.strip()}%"
        
        query = self.session.query(self.model).filter(
            and_(
                self.model.is_deleted == False,
                or_(
                    func.lower(self.model.first_name).like(func.lower(search_pattern)),
                    func.lower(self.model.last_name).like(func.lower(search_pattern)),
                    func.concat(
                        func.lower(self.model.first_name), 
                        ' ', 
                        func.lower(self.model.last_name)
                    ).like(func.lower(search_pattern))
                )
            )
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.order_by(self.model.first_name, self.model.last_name).all()
    
    def find_by_status(self, status: CustomerStatus) -> List[Customer]:
        """Find customers by status"""
        return self.session.query(self.model).filter(
            and_(
                self.model.status == status,
                self.model.is_deleted == False
            )
        ).order_by(self.model.created_at.desc()).all()
    
    def find_vip_customers(self) -> List[Customer]:
        """Find VIP customers"""
        return self.find_by_status(CustomerStatus.VIP)
    
    def find_inactive_customers(self, days_inactive: int = 90) -> List[Customer]:
        """Find customers who haven't visited in X days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        return self.session.query(self.model).filter(
            and_(
                self.model.is_deleted == False,
                self.model.status == CustomerStatus.ACTIVE,
                or_(
                    self.model.last_visit_date < cutoff_date,
                    self.model.last_visit_date.is_(None)
                )
            )
        ).order_by(self.model.last_visit_date.asc()).all()
    
    def find_new_customers(self, days_ago: int = 30) -> List[Customer]:
        """Find customers registered in the last X days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_ago)
        
        return self.session.query(self.model).filter(
            and_(
                self.model.created_at >= cutoff_date,
                self.model.is_deleted == False
            )
        ).order_by(self.model.created_at.desc()).all()
    
    def find_high_value_customers(self, min_spent_cents: int = 100000) -> List[Customer]:
        """Find customers who have spent more than X amount"""
        return self.session.query(self.model).filter(
            and_(
                self.model.total_spent >= min_spent_cents,
                self.model.is_deleted == False
            )
        ).order_by(self.model.total_spent.desc()).all()
    
    def find_customers_with_dietary_restrictions(self, restriction: str) -> List[Customer]:
        """Find customers with specific dietary restrictions"""
        return self.session.query(self.model).filter(
            and_(
                self.model.dietary_preferences.ilike(f'%"{restriction}"%'),
                self.model.is_deleted == False
            )
        ).all()
    
    # Customer Creation and Validation
    
    def create_customer(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        dietary_preferences: Optional[List[str]] = None,
        email_notifications: bool = True,
        sms_notifications: bool = False,
        marketing_emails: bool = True
    ) -> Customer:
        """Create a new customer with validation"""
        # Validate required fields
        if not first_name or not first_name.strip():
            raise_validation_error(
                "First name is required",
                field_errors={"first_name": ["Field is required"]}
            )
        
        if not last_name or not last_name.strip():
            raise_validation_error(
                "Last name is required",
                field_errors={"last_name": ["Field is required"]}
            )
        
        if not email or not email.strip():
            raise_validation_error(
                "Email is required",
                field_errors={"email": ["Field is required"]}
            )
        
        # Validate email format (basic check)
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            raise_validation_error(
                "Invalid email format",
                field_errors={"email": ["Invalid email format"]}
            )
        
        # Check for duplicate email
        existing_customer = self.find_by_email(email.strip())
        if existing_customer:
            raise_conflict(
                f"Customer with email '{email.strip()}' already exists",
                conflicting_resource="customer"
            )
        
        # Check for duplicate phone if provided
        if phone:
            existing_customer_phone = self.find_by_phone(phone)
            if existing_customer_phone:
                raise_conflict(
                    f"Customer with phone '{phone}' already exists",
                    conflicting_resource="customer"
                )
        
        # Create customer data
        customer_data = {
            "first_name": first_name.strip().title(),
            "last_name": last_name.strip().title(),
            "email": email.strip().lower(),
            "phone": phone.strip() if phone else None,
            "status": CustomerStatus.ACTIVE,
            "email_notifications": email_notifications,
            "sms_notifications": sms_notifications,
            "marketing_emails": marketing_emails,
            "loyalty_points": 0,
            "total_visits": 0,
            "total_spent": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        customer = self.create(customer_data)
        
        # Set dietary preferences if provided
        if dietary_preferences:
            customer.set_dietary_preferences(dietary_preferences)
            self.session.commit()
        
        return customer
    
    def update_customer_profile(
        self,
        customer_id: int,
        update_data: Dict[str, Any]
    ) -> Customer:
        """Update customer profile with validation"""
        customer = self.get_by_id(customer_id)
        if not customer:
            raise_not_found("Customer", str(customer_id))
        
        # Validate email uniqueness if email is being updated
        if "email" in update_data:
            new_email = update_data["email"].strip().lower()
            if new_email != customer.email:
                existing_customer = self.find_by_email(new_email)
                if existing_customer:
                    raise_conflict(
                        f"Customer with email '{new_email}' already exists",
                        conflicting_resource="customer"
                    )
        
        # Validate phone uniqueness if phone is being updated
        if "phone" in update_data and update_data["phone"]:
            new_phone = update_data["phone"].strip()
            if new_phone != customer.phone:
                existing_customer = self.find_by_phone(new_phone)
                if existing_customer:
                    raise_conflict(
                        f"Customer with phone '{new_phone}' already exists",
                        conflicting_resource="customer"
                    )
        
        # Handle dietary preferences specially
        if "dietary_preferences" in update_data:
            dietary_prefs = update_data.pop("dietary_preferences")
            if isinstance(dietary_prefs, list):
                customer.set_dietary_preferences(dietary_prefs)
        
        # Update other fields
        update_data["updated_at"] = datetime.utcnow()
        
        return self.update(customer_id, update_data)
    
    # Loyalty and Activity Management
    
    def add_loyalty_points(
        self,
        customer_id: int,
        points: int,
        reason: Optional[str] = None
    ) -> Customer:
        """Add loyalty points to customer account"""
        customer = self.get_by_id(customer_id)
        if not customer:
            raise_not_found("Customer", str(customer_id))
        
        if points <= 0:
            raise_validation_error(
                "Points must be greater than 0",
                field_errors={"points": ["Must be a positive number"]}
            )
        
        customer.add_loyalty_points(points)
        customer.updated_at = datetime.utcnow()
        
        self.session.commit()
        
        # Here you could log the loyalty transaction
        # loyalty_service.log_transaction(customer_id, points, reason)
        
        return customer
    
    def record_visit(
        self,
        customer_id: int,
        visit_date: Optional[datetime] = None,
        amount_spent_cents: Optional[int] = None
    ) -> Customer:
        """Record a customer visit"""
        customer = self.get_by_id(customer_id)
        if not customer:
            raise_not_found("Customer", str(customer_id))
        
        visit_datetime = visit_date or datetime.utcnow()
        
        update_data = {
            "last_visit_date": visit_datetime,
            "total_visits": (customer.total_visits or 0) + 1,
            "updated_at": datetime.utcnow()
        }
        
        if amount_spent_cents:
            update_data["total_spent"] = (customer.total_spent or 0) + amount_spent_cents
            
            # Calculate loyalty points (1 point per dollar spent)
            loyalty_points = amount_spent_cents // 100
            if loyalty_points > 0:
                update_data["loyalty_points"] = (customer.loyalty_points or 0) + loyalty_points
        
        return self.update(customer_id, update_data)
    
    def promote_to_vip(
        self,
        customer_id: int,
        reason: Optional[str] = None
    ) -> Customer:
        """Promote customer to VIP status"""
        customer = self.get_by_id(customer_id)
        if not customer:
            raise_not_found("Customer", str(customer_id))
        
        if customer.status == CustomerStatus.VIP:
            raise_validation_error(
                "Customer is already VIP",
                field_errors={"status": ["Already VIP status"]}
            )
        
        update_data = {
            "status": CustomerStatus.VIP,
            "updated_at": datetime.utcnow()
        }
        
        return self.update(customer_id, update_data)
    
    def suspend_customer(
        self,
        customer_id: int,
        reason: Optional[str] = None
    ) -> Customer:
        """Suspend customer account"""
        customer = self.get_by_id(customer_id)
        if not customer:
            raise_not_found("Customer", str(customer_id))
        
        update_data = {
            "status": CustomerStatus.SUSPENDED,
            "special_notes": f"Suspended: {reason}" if reason else "Account suspended",
            "updated_at": datetime.utcnow()
        }
        
        return self.update(customer_id, update_data)
    
    def reactivate_customer(self, customer_id: int) -> Customer:
        """Reactivate suspended customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            raise_not_found("Customer", str(customer_id))
        
        update_data = {
            "status": CustomerStatus.ACTIVE,
            "updated_at": datetime.utcnow()
        }
        
        return self.update(customer_id, update_data)
    
    # Analytics and Reporting
    
    def get_customer_statistics(self) -> Dict[str, Any]:
        """Get overall customer statistics"""
        # Total customers by status
        status_counts = self.session.query(
            self.model.status,
            func.count(self.model.id)
        ).filter(
            self.model.is_deleted == False
        ).group_by(self.model.status).all()
        
        # New customers this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = self.session.query(func.count(self.model.id)).filter(
            and_(
                self.model.created_at >= start_of_month,
                self.model.is_deleted == False
            )
        ).scalar()
        
        # Average loyalty points
        avg_loyalty_points = self.session.query(func.avg(self.model.loyalty_points)).filter(
            self.model.is_deleted == False
        ).scalar()
        
        # Top spending customers
        top_spenders = self.session.query(
            self.model.id,
            self.model.first_name,
            self.model.last_name,
            self.model.total_spent
        ).filter(
            self.model.is_deleted == False
        ).order_by(self.model.total_spent.desc()).limit(10).all()
        
        return {
            "total_customers": sum(count for _, count in status_counts),
            "status_breakdown": {status.value: count for status, count in status_counts},
            "new_customers_this_month": new_this_month,
            "average_loyalty_points": float(avg_loyalty_points) if avg_loyalty_points else 0,
            "top_spenders": [
                {
                    "id": customer_id,
                    "name": f"{first_name} {last_name}",
                    "total_spent_dollars": total_spent / 100 if total_spent else 0
                }
                for customer_id, first_name, last_name, total_spent in top_spenders
            ]
        }
    
    def get_customer_segments(self) -> Dict[str, Any]:
        """Get customer segmentation data"""
        # VIP customers
        vip_count = self.session.query(func.count(self.model.id)).filter(
            and_(
                self.model.status == CustomerStatus.VIP,
                self.model.is_deleted == False
            )
        ).scalar()
        
        # High-value customers (spent > $500)
        high_value_count = self.session.query(func.count(self.model.id)).filter(
            and_(
                self.model.total_spent >= 50000,  # $500 in cents
                self.model.is_deleted == False
            )
        ).scalar()
        
        # Frequent visitors (> 10 visits)
        frequent_visitors_count = self.session.query(func.count(self.model.id)).filter(
            and_(
                self.model.total_visits >= 10,
                self.model.is_deleted == False
            )
        ).scalar()
        
        # Inactive customers (no visit in 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        inactive_count = self.session.query(func.count(self.model.id)).filter(
            and_(
                self.model.is_deleted == False,
                self.model.status == CustomerStatus.ACTIVE,
                or_(
                    self.model.last_visit_date < cutoff_date,
                    self.model.last_visit_date.is_(None)
                )
            )
        ).scalar()
        
        return {
            "vip_customers": vip_count,
            "high_value_customers": high_value_count,
            "frequent_visitors": frequent_visitors_count,
            "inactive_customers": inactive_count
        }
    
    def search_customers(
        self,
        search_criteria: Dict[str, Any],
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Customer], int]:
        """Advanced customer search with multiple criteria"""
        query = self.session.query(self.model).filter(self.model.is_deleted == False)
        
        # Apply filters based on search criteria
        if "email" in search_criteria:
            email_pattern = f"%{search_criteria['email']}%"
            query = query.filter(self.model.email.ilike(email_pattern))
        
        if "phone" in search_criteria:
            phone_digits = ''.join(filter(str.isdigit, search_criteria['phone']))
            query = query.filter(
                func.regexp_replace(self.model.phone, '[^0-9]', '', 'g').ilike(f"%{phone_digits}%")
            )
        
        if "name" in search_criteria:
            name_pattern = f"%{search_criteria['name']}%"
            query = query.filter(
                or_(
                    self.model.first_name.ilike(name_pattern),
                    self.model.last_name.ilike(name_pattern),
                    func.concat(self.model.first_name, ' ', self.model.last_name).ilike(name_pattern)
                )
            )
        
        if "status" in search_criteria:
            statuses = search_criteria["status"]
            if isinstance(statuses, list):
                query = query.filter(self.model.status.in_(statuses))
            else:
                query = query.filter(self.model.status == statuses)
        
        if "min_loyalty_points" in search_criteria:
            query = query.filter(self.model.loyalty_points >= search_criteria["min_loyalty_points"])
        
        if "min_total_spent" in search_criteria:
            query = query.filter(self.model.total_spent >= search_criteria["min_total_spent"])
        
        if "dietary_preference" in search_criteria:
            pref = search_criteria["dietary_preference"]
            query = query.filter(self.model.dietary_preferences.ilike(f'%"{pref}"%'))
        
        if "registration_date_range" in search_criteria:
            date_range = search_criteria["registration_date_range"]
            if "start_date" in date_range:
                query = query.filter(self.model.created_at >= date_range["start_date"])
            if "end_date" in date_range:
                query = query.filter(self.model.created_at <= date_range["end_date"])
        
        if "last_visit_range" in search_criteria:
            date_range = search_criteria["last_visit_range"]
            if "start_date" in date_range:
                query = query.filter(self.model.last_visit_date >= date_range["start_date"])
            if "end_date" in date_range:
                query = query.filter(self.model.last_visit_date <= date_range["end_date"])
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        customers = query.order_by(
            self.model.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return customers, total_count