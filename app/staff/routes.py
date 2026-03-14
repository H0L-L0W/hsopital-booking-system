from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from .. import db
from ..models import Appointment, AppointmentStatus

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_staff:
        flash("Access restricted to hospital staff.", "danger")
        return redirect(url_for("main.dashboard"))
    # Simple calendar-style view of all upcoming appointments
    upcoming = (
        Appointment.query.filter(Appointment.start_time >= db.func.now())
        .order_by(Appointment.start_time.asc())
        .all()
    )
    return render_template("staff/dashboard.html", upcoming=upcoming)


@staff_bp.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@login_required
def update_status(appointment_id):
    if not current_user.is_staff:
        flash("Access restricted to hospital staff.", "danger")
        return redirect(url_for("staff.dashboard"))
    appt = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get("status")
    if new_status not in [s.value for s in AppointmentStatus]:
        flash("Invalid status.", "danger")
        return redirect(url_for("staff.dashboard"))
    appt.status = AppointmentStatus(new_status)
    db.session.commit()
    flash("Appointment status updated.", "success")
    return redirect(url_for("staff.dashboard"))

