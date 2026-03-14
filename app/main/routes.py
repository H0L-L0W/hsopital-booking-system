from datetime import datetime

from flask import Blueprint, redirect, render_template, url_for  # redirect & url_for for dashboard
from flask_login import login_required, current_user

from .. import db
from ..models import (
    Appointment,
    AppointmentStatus,
    HospitalConfig,
    RevenueRecord,
    Department,
    DoctorProfile,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    config = HospitalConfig.query.first()
    if not config:
        config = HospitalConfig()
    doctors = DoctorProfile.query.filter_by(is_active=True).all()
    departments = Department.query.all()
    return render_template(
        "main/index.html",
        config=config,
        doctors=doctors,
        departments=departments,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    if current_user.is_doctor:
        return redirect(url_for("doctor.dashboard"))
    if current_user.is_staff:
        return redirect(url_for("staff.dashboard"))
    return redirect(url_for("patient.dashboard"))


@main_bp.route("/analytics")
@login_required
def analytics():
    # Simple analytics overview for admin/staff; patients can see limited stats
    total_appointments = Appointment.query.count()
    total_confirmed = Appointment.query.filter(
        Appointment.status == AppointmentStatus.CONFIRMED
    ).count()
    total_cancelled = Appointment.query.filter(
        Appointment.status == AppointmentStatus.CANCELLED
    ).count()

    # revenue
    total_revenue_cents = (
        RevenueRecord.query.with_entities(
            db.func.coalesce(db.func.sum(RevenueRecord.amount_cents), 0)
        ).scalar()
    )

    # per doctor
    per_doctor = (
        RevenueRecord.query.join(DoctorProfile)
        .with_entities(
            DoctorProfile.id,
            DoctorProfile.user_id,
            db.func.coalesce(db.func.sum(RevenueRecord.amount_cents), 0),
        )
        .group_by(DoctorProfile.id, DoctorProfile.user_id)
        .all()
    )

    return render_template(
        "main/analytics.html",
        total_appointments=total_appointments,
        total_confirmed=total_confirmed,
        total_cancelled=total_cancelled,
        total_revenue_cents=total_revenue_cents,
        per_doctor=per_doctor,
    )

