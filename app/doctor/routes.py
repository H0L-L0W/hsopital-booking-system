from datetime import time

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from .. import db
from ..forms import AvailabilityForm
from ..models import (
    Appointment,
    AppointmentStatus,
    DoctorProfile,
    DoctorAvailability,
)

doctor_bp = Blueprint("doctor", __name__)


@doctor_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_doctor:
        flash("Access restricted to doctors.", "danger")
        return redirect(url_for("main.dashboard"))
    doctor_profile: DoctorProfile = current_user.doctor_profile
    upcoming = (
        Appointment.query.filter_by(doctor_id=doctor_profile.id)
        .filter(Appointment.start_time >= db.func.now())
        .order_by(Appointment.start_time.asc())
        .all()
    )
    return render_template(
        "doctor/dashboard.html", doctor=doctor_profile, upcoming=upcoming
    )


@doctor_bp.route("/availability", methods=["GET", "POST"])
@login_required
def manage_availability():
    if not current_user.is_doctor:
        flash("Access restricted to doctors.", "danger")
        return redirect(url_for("main.dashboard"))
    doctor_profile: DoctorProfile = current_user.doctor_profile
    form = AvailabilityForm()
    if form.validate_on_submit():
        # Simple HH:MM parsing
        start_h, start_m = map(int, form.start_time.data.split(":"))
        end_h, end_m = map(int, form.end_time.data.split(":"))
        avail = DoctorAvailability(
            doctor_id=doctor_profile.id,
            weekday=form.weekday.data,
            start_time=time(start_h, start_m),
            end_time=time(end_h, end_m),
        )
        db.session.add(avail)
        db.session.commit()
        flash("Availability added.", "success")
        return redirect(url_for("doctor.manage_availability"))
    availabilities = doctor_profile.availabilities.all()
    return render_template(
        "doctor/availability.html", form=form, availabilities=availabilities
    )

