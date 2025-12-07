from typing import Optional
import datetime
import uuid

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    PrimaryKeyConstraint,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Chefs(Base):
    __tablename__ = "chefs"
    __table_args__ = (PrimaryKeyConstraint("id", name="chefs_pkey"), {"schema": "core"})

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    zones: Mapped[list[str]] = mapped_column(ARRAY(String(length=50)), nullable=False)
    buffer_setup_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    buffer_teardown_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    skills: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(length=50)))
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(255))
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    bookings: Mapped[list["Bookings"]] = relationship("Bookings", back_populates="chef")


class SocialAccounts(Base):
    __tablename__ = "social_accounts"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="social_accounts_pkey"),
        Index("ix_social_accounts_created_at", "created_at"),
        Index("ix_social_accounts_platform", "platform"),
        Index("ix_social_accounts_platform_page_active", "platform", "page_id", unique=True),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    platform: Mapped[str] = mapped_column(
        Enum(
            "instagram",
            "facebook",
            "google_business",
            "yelp",
            "tiktok",
            "twitter",
            name="social_platform",
        ),
        nullable=False,
    )
    page_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Platform-specific page/business ID"
    )
    page_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Display name of the business page"
    )
    connected_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, comment="User who connected this account"
    )
    connected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    webhook_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    handle: Mapped[Optional[str]] = mapped_column(
        String(100), comment="@username or handle if applicable"
    )
    profile_url: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    token_ref: Mapped[Optional[str]] = mapped_column(
        Text, comment="Encrypted reference to access tokens"
    )
    last_sync_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, comment="Platform-specific settings and capabilities"
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    social_threads: Mapped[list["SocialThreads"]] = relationship(
        "SocialThreads", back_populates="account"
    )
    reviews: Mapped[list["Reviews"]] = relationship("Reviews", back_populates="account")


class SocialIdentities(Base):
    __tablename__ = "social_identities"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="social_identities_pkey"),
        Index("ix_social_identities_customer_id", "customer_id"),
        Index("ix_social_identities_last_active", "last_active_at"),
        Index("ix_social_identities_platform_handle", "platform", "handle", unique=True),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    platform: Mapped[str] = mapped_column(
        Enum(
            "instagram",
            "facebook",
            "google_business",
            "yelp",
            "tiktok",
            "twitter",
            name="social_platform",
        ),
        nullable=False,
    )
    handle: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Social handle without @ prefix"
    )
    confidence_score: Mapped[float] = mapped_column(
        Double(53), nullable=False, comment="Confidence in customer mapping"
    )
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False)
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    profile_url: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment="Link to known customer")
    last_active_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    social_threads: Mapped[list["SocialThreads"]] = relationship(
        "SocialThreads", back_populates="social_identity"
    )


class Stations(Base):
    __tablename__ = "stations"
    __table_args__ = (
        CheckConstraint("booking_lead_time_hours >= 0", name="station_lead_time_non_negative"),
        CheckConstraint("max_concurrent_bookings > 0", name="station_max_bookings_positive"),
        CheckConstraint(
            "status::text = ANY (ARRAY['active'::character varying, 'inactive'::character varying, 'suspended'::character varying, 'maintenance'::character varying]::text[])",
            name="station_status_valid",
        ),
        PrimaryKeyConstraint("id", name="stations_pkey"),
        UniqueConstraint("code", name="unique_station_code"),
        Index("idx_station_code", "code"),
        Index("idx_station_status", "status"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("'US'::character varying")
    )
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'America/New_York'::character varying")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'active'::character varying")
    )
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'{}'::json"))
    max_concurrent_bookings: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("10")
    )
    booking_lead_time_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("24")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    business_hours: Mapped[Optional[dict]] = mapped_column(JSON)
    service_area_radius: Mapped[Optional[int]] = mapped_column(Integer)
    branding_config: Mapped[Optional[dict]] = mapped_column(JSON)

    customers: Mapped[list["Customers"]] = relationship("Customers", back_populates="station")
    bookings: Mapped[list["Bookings"]] = relationship("Bookings", back_populates="station")
    message_threads: Mapped[list["MessageThreads"]] = relationship(
        "MessageThreads", back_populates="station"
    )


class Customers(Base):
    __tablename__ = "customers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["station_id"],
            ["identity.stations.id"],
            ondelete="RESTRICT",
            name="fk_customers_station",
        ),
        PrimaryKeyConstraint("id", name="customers_pkey"),
        Index("idx_customer_station_created", "station_id", "created_at"),
        Index("idx_customer_station_email", "station_id", "email_encrypted", unique=True),
        Index("ix_core_customers_email_active", "email_encrypted", unique=True),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    phone_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    consent_sms: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_email: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    station_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    consent_updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(length=50)))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    station: Mapped["Stations"] = relationship("Stations", back_populates="customers")
    bookings: Mapped[list["Bookings"]] = relationship("Bookings", back_populates="customer")
    message_threads: Mapped[list["MessageThreads"]] = relationship(
        "MessageThreads", back_populates="customer"
    )
    social_threads: Mapped[list["SocialThreads"]] = relationship(
        "SocialThreads", back_populates="customer"
    )
    reviews: Mapped[list["Reviews"]] = relationship("Reviews", back_populates="customer")


class Bookings(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("deposit_due_cents >= 0", name="check_deposit_non_negative"),
        CheckConstraint("party_adults > 0", name="check_party_adults_positive"),
        CheckConstraint("party_kids >= 0", name="check_party_kids_non_negative"),
        CheckConstraint("total_due_cents >= deposit_due_cents", name="check_total_gte_deposit"),
        ForeignKeyConstraint(
            ["chef_id"], ["ops.chefs.id"], ondelete="SET NULL", name="bookings_chef_id_fkey"
        ),
        ForeignKeyConstraint(
            ["customer_id"],
            ["core.customers.id"],
            ondelete="RESTRICT",
            name="bookings_customer_id_fkey",
        ),
        ForeignKeyConstraint(
            ["station_id"],
            ["identity.stations.id"],
            ondelete="RESTRICT",
            name="fk_bookings_station",
        ),
        PrimaryKeyConstraint("id", name="bookings_pkey"),
        Index("idx_booking_date_slot_active", "date", "slot", "status", unique=True),
        Index("idx_booking_station_customer", "station_id", "customer_id"),
        Index("idx_booking_station_date", "station_id", "date", "slot"),
        Index("ix_bookings_customer_deposit_deadline", "customer_deposit_deadline", "status"),
        Index(
            "ix_bookings_internal_deadline",
            "internal_deadline",
            "status",
            "hold_on_request",
            "deposit_confirmed_at",
        ),
        Index("ix_bookings_sms_consent", "sms_consent"),
        Index("ix_core_bookings_chef_slot_unique", "chef_id", "date", "slot", unique=True),
        Index("ix_core_bookings_customer_id", "customer_id"),
        Index("ix_core_bookings_date_slot", "date", "slot"),
        Index("ix_core_bookings_status", "status"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    slot: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    address_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    zone: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "new",
            "deposit_pending",
            "confirmed",
            "completed",
            "cancelled",
            "no_show",
            name="booking_status",
        ),
        nullable=False,
    )
    party_adults: Mapped[int] = mapped_column(Integer, nullable=False)
    party_kids: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_due_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_due_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    station_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    hold_on_request: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    sms_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    chef_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    menu_items: Mapped[Optional[dict]] = mapped_column(JSONB)
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    customer_deposit_deadline: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    internal_deadline: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    deposit_deadline: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    deposit_confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    deposit_confirmed_by: Mapped[Optional[str]] = mapped_column(String(255))
    held_by: Mapped[Optional[str]] = mapped_column(String(255))
    held_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    hold_reason: Mapped[Optional[str]] = mapped_column(Text)
    sms_consent_timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    chef: Mapped[Optional["Chefs"]] = relationship("Chefs", back_populates="bookings")
    customer: Mapped["Customers"] = relationship("Customers", back_populates="bookings")
    station: Mapped["Stations"] = relationship("Stations", back_populates="bookings")


class MessageThreads(Base):
    __tablename__ = "message_threads"
    __table_args__ = (
        ForeignKeyConstraint(
            ["customer_id"],
            ["core.customers.id"],
            ondelete="CASCADE",
            name="message_threads_customer_id_fkey",
        ),
        ForeignKeyConstraint(
            ["station_id"],
            ["identity.stations.id"],
            ondelete="RESTRICT",
            name="fk_message_threads_station",
        ),
        PrimaryKeyConstraint("id", name="message_threads_pkey"),
        Index("ix_core_message_threads_customer", "customer_id"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    channel: Mapped[str] = mapped_column(
        Enum("web_chat", "sms", "email", "phone", "admin", name="message_channel"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "active", "waiting", "resolved", "escalated", "closed", "urgent", name="thread_status"
        ),
        nullable=False,
    )
    ai_mode: Mapped[bool] = mapped_column(Boolean, nullable=False)
    last_message_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    station_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    external_thread_id: Mapped[Optional[str]] = mapped_column(String(255))
    assigned_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    customer: Mapped["Customers"] = relationship("Customers", back_populates="message_threads")
    station: Mapped["Stations"] = relationship("Stations", back_populates="message_threads")
    messages: Mapped[list["Messages"]] = relationship("Messages", back_populates="thread")


class SocialThreads(Base):
    __tablename__ = "social_threads"
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 5", name="ck_social_threads_priority_range"),
        ForeignKeyConstraint(
            ["account_id"],
            ["core.social_accounts.id"],
            ondelete="CASCADE",
            name="social_threads_account_id_fkey",
        ),
        ForeignKeyConstraint(
            ["customer_id"],
            ["core.customers.id"],
            ondelete="SET NULL",
            name="social_threads_customer_id_fkey",
        ),
        ForeignKeyConstraint(
            ["social_identity_id"],
            ["core.social_identities.id"],
            ondelete="SET NULL",
            name="social_threads_social_identity_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="social_threads_pkey"),
        Index("ix_social_threads_account_thread_ref", "account_id", "thread_ref", unique=True),
        Index("ix_social_threads_assigned_to", "assigned_to"),
        Index("ix_social_threads_customer_id", "customer_id"),
        Index("ix_social_threads_last_message_at", "last_message_at"),
        Index("ix_social_threads_lead_id", "lead_id"),
        Index("ix_social_threads_status", "status"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    platform: Mapped[str] = mapped_column(
        Enum(
            "instagram",
            "facebook",
            "google_business",
            "yelp",
            "tiktok",
            "twitter",
            name="social_platform",
        ),
        nullable=False,
    )
    thread_ref: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Platform-specific thread/conversation ID"
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, comment="Our social account"
    )
    status: Mapped[str] = mapped_column(
        Enum("open", "pending", "resolved", "snoozed", "escalated", name="social_thread_status"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, comment="1=urgent, 5=low")
    message_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, comment="Linked customer if known"
    )
    lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, comment="Generated lead if applicable"
    )
    social_identity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, comment="Other party social identity"
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Thread subject or first message preview"
    )
    context_url: Mapped[Optional[str]] = mapped_column(
        Text, comment="Link to original post/content"
    )
    last_message_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    last_response_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment="Assigned team member")
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(length=50)))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    account: Mapped["SocialAccounts"] = relationship(
        "SocialAccounts", back_populates="social_threads"
    )
    customer: Mapped[Optional["Customers"]] = relationship(
        "Customers", back_populates="social_threads"
    )
    social_identity: Mapped[Optional["SocialIdentities"]] = relationship(
        "SocialIdentities", back_populates="social_threads"
    )
    reviews: Mapped[list["Reviews"]] = relationship("Reviews", back_populates="thread")
    social_messages: Mapped[list["SocialMessages"]] = relationship(
        "SocialMessages", back_populates="thread"
    )


class Messages(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "direction::text = ANY (ARRAY['inbound'::character varying, 'outbound'::character varying]::text[])",
            name="check_message_direction",
        ),
        CheckConstraint(
            "sender_type::text = ANY (ARRAY['customer'::character varying, 'agent'::character varying, 'ai'::character varying, 'system'::character varying]::text[])",
            name="check_sender_type",
        ),
        ForeignKeyConstraint(
            ["thread_id"],
            ["core.message_threads.id"],
            ondelete="CASCADE",
            name="messages_thread_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="messages_pkey"),
        Index("ix_core_messages_thread_created", "thread_id", "created_at"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    thread: Mapped["MessageThreads"] = relationship("MessageThreads", back_populates="messages")


class Reviews(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        CheckConstraint(
            "sentiment_score >= '-1.0'::numeric::double precision AND sentiment_score <= 1.0::double precision",
            name="ck_reviews_sentiment_range",
        ),
        ForeignKeyConstraint(
            ["account_id"],
            ["core.social_accounts.id"],
            ondelete="CASCADE",
            name="reviews_account_id_fkey",
        ),
        ForeignKeyConstraint(
            ["customer_id"],
            ["core.customers.id"],
            ondelete="SET NULL",
            name="reviews_customer_id_fkey",
        ),
        ForeignKeyConstraint(
            ["thread_id"],
            ["core.social_threads.id"],
            ondelete="SET NULL",
            name="reviews_thread_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="reviews_pkey"),
        Index("ix_reviews_account_review_ref", "account_id", "review_ref", unique=True),
        Index("ix_reviews_assigned_to", "assigned_to"),
        Index("ix_reviews_created_at", "created_at"),
        Index("ix_reviews_customer_id", "customer_id"),
        Index("ix_reviews_platform_status", "platform", "status"),
        Index("ix_reviews_rating", "rating"),
        Index("ix_reviews_response_due_at", "response_due_at"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    platform: Mapped[str] = mapped_column(
        Enum(
            "instagram",
            "facebook",
            "google_business",
            "yelp",
            "tiktok",
            "twitter",
            name="social_platform",
        ),
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    review_ref: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Platform-specific review ID"
    )
    status: Mapped[str] = mapped_column(
        Enum("new", "acknowledged", "responded", "escalated", "closed", name="review_status"),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, comment="Associated thread if replies exist"
    )
    author_handle: Mapped[Optional[str]] = mapped_column(String(100))
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    rating: Mapped[Optional[int]] = mapped_column(
        Integer, comment="1-5 star rating where applicable"
    )
    title: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    review_url: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Double(53))
    keywords: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(length=50)))
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    booking_ref: Mapped[Optional[str]] = mapped_column(
        String(50), comment="Reference to related booking if found"
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    escalation_reason: Mapped[Optional[str]] = mapped_column(String(255))
    response_due_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), comment="SLA deadline"
    )
    responded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    account: Mapped["SocialAccounts"] = relationship("SocialAccounts", back_populates="reviews")
    customer: Mapped[Optional["Customers"]] = relationship("Customers", back_populates="reviews")
    thread: Mapped[Optional["SocialThreads"]] = relationship(
        "SocialThreads", back_populates="reviews"
    )


class SocialMessages(Base):
    __tablename__ = "social_messages"
    __table_args__ = (
        CheckConstraint(
            "sentiment_score >= '-1.0'::numeric::double precision AND sentiment_score <= 1.0::double precision",
            name="ck_social_messages_sentiment_range",
        ),
        ForeignKeyConstraint(
            ["parent_message_id"],
            ["core.social_messages.id"],
            ondelete="CASCADE",
            name="social_messages_parent_message_id_fkey",
        ),
        ForeignKeyConstraint(
            ["thread_id"],
            ["core.social_threads.id"],
            ondelete="CASCADE",
            name="social_messages_thread_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="social_messages_pkey"),
        Index("ix_social_messages_created_at", "created_at"),
        Index("ix_social_messages_direction_kind", "direction", "kind"),
        Index("ix_social_messages_requires_approval", "requires_approval"),
        Index("ix_social_messages_thread_id", "thread_id"),
        {"schema": "core"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    direction: Mapped[str] = mapped_column(
        Enum("in", "out", name="social_message_direction"), nullable=False
    )
    kind: Mapped[str] = mapped_column(
        Enum(
            "dm", "comment", "review", "reply", "mention", "story_reply", name="social_message_kind"
        ),
        nullable=False,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment="Public comment vs private DM"
    )
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment="AI response needs human approval"
    )
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    message_ref: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Platform-specific message ID"
    )
    author_handle: Mapped[Optional[str]] = mapped_column(String(100))
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    media: Mapped[Optional[dict]] = mapped_column(JSONB, comment="Attachments, images, videos")
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Double(53), comment="AI sentiment analysis -1 to 1"
    )
    intent_tags: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(length=50)), comment="Detected intents: booking, complaint, etc"
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, comment="Who approved the response"
    )
    parent_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, comment="Reply to this message"
    )
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), comment="When actually posted to platform"
    )
    failed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    error_details: Mapped[Optional[str]] = mapped_column(Text)

    parent_message: Mapped[Optional["SocialMessages"]] = relationship(
        "SocialMessages", remote_side=[id], back_populates="parent_message_reverse"
    )
    parent_message_reverse: Mapped[list["SocialMessages"]] = relationship(
        "SocialMessages", remote_side=[parent_message_id], back_populates="parent_message"
    )
    thread: Mapped["SocialThreads"] = relationship(
        "SocialThreads", back_populates="social_messages"
    )
