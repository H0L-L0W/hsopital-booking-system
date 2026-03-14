from datetime import datetime, time
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager


class RoleEnum(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    STAFF = "staff"
    ADMIN = "admin"  # super admin / CEO


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.PATIENT)
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient_profile = db.relationship("PatientProfile", backref="user", uselist=False)
    doctor_profile = db.relationship("DoctorProfile", backref="user", uselist=False)
    staff_profile = db.relationship("StaffProfile", backref="user", uselist=False)

    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == RoleEnum.ADMIN

    @property
    def is_doctor(self) -> bool:
        return self.role == RoleEnum.DOCTOR

    @property
    def is_staff(self) -> bool:
        return self.role == RoleEnum.STAFF

    @property
    def is_patient(self) -> bool:
        return self.role == RoleEnum.PATIENT


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)

    doctors = db.relationship("DoctorProfile", backref="department", lazy="dynamic")


class HospitalConfig(db.Model):
    """Singleton-style configuration for hospital / platform."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), default="Acme Health Platform")
    description = db.Column(db.Text, default="Modern hospital appointment and management SaaS.")
    ceo_name = db.Column(db.String(255), default="CEO Name")
    ceo_bio = db.Column(db.Text, default="Short CEO bio.")
    homepage_content = db.Column(db.Text, default="Welcome to our hospital platform.")
    pricing_page_content = db.Column(db.Text, default="Pricing plans coming soon.")

    default_consultation_fee = db.Column(db.Integer, default=50)  # basic fee
    online_booking_enabled = db.Column(db.Boolean, default=True)
    operating_hours_start = db.Column(db.Time, default=time(9, 0))
    operating_hours_end = db.Column(db.Time, default=time(17, 0))


class PatientProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    dob = db.Column(db.Date)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    insurance_provider = db.Column(db.String(255))

    appointments = db.relationship("Appointment", backref="patient", lazy="dynamic")


class DoctorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    bio = db.Column(db.Text)
    consultation_fee = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship("Appointment", backref="doctor", lazy="dynamic")
    availabilities = db.relationship(
        "DoctorAvailability",
        backref="doctor",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class StaffProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    position = db.Column(db.String(255))
    approved = db.Column(db.Boolean, default=False)


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient_profile.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profile.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))

    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    consultation_fee = db.Column(db.Integer)
    revenue_record = db.relationship(
        "RevenueRecord",
        backref="appointment",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profile.id"), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0=Monday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)


class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    monthly_price = db.Column(db.Integer, nullable=False)
    per_appointment_fee = db.Column(db.Integer, nullable=False)


class RevenueRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), unique=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profile.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))

    amount_cents = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NotificationType(str, Enum):
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

