from datetime import timedelta

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_required, current_user

from .. import db
from ..forms import AppointmentForm
from ..models import (
    Appointment,
    AppointmentStatus,
    DoctorProfile,
    PatientProfile,
    HospitalConfig,
    Notification,
    NotificationType,
    RevenueRecord,
)

patient_bp = Blueprint("patient", __name__)


def _create_notification(user_id, notif_type: NotificationType, message: str):
    n = Notification(user_id=user_id, type=notif_type, message=message)
    db.session.add(n)


@patient_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_patient:
        flash("Access restricted to patients.", "danger")
        return redirect(url_for("main.dashboard"))
    profile = current_user.patient_profile
    upcoming = (
        Appointment.query.filter_by(patient_id=profile.id)
        .filter(Appointment.start_time >= db.func.now())
        .order_by(Appointment.start_time.asc())
        .all()
    )
    notifications = (
        current_user.notifications.order_by(
            Notification.created_at.desc()
        ).limit(10)
    )
    return render_template(
        "patient/dashboard.html",
        upcoming=upcoming,
        notifications=notifications,
    )


@patient_bp.route("/appointments/new", methods=["GET", "POST"])
@login_required
def book_appointment():
    if not current_user.is_patient:
        flash("Only patients can book appointments.", "danger")
        return redirect(url_for("main.dashboard"))

    form = AppointmentForm()
    doctors = DoctorProfile.query.filter_by(is_active=True).all()
    form.doctor_id.choices = [(d.id, d.user.full_name) for d in doctors]

    if form.validate_on_submit():
        patient_profile: PatientProfile = current_user.patient_profile
        doctor = DoctorProfile.query.get(form.doctor_id.data)
        start = form.start_time.data
        end = start + timedelta(minutes=30)

        # Prevent double booking for the doctor at the same slot
        conflict = (
            Appointment.query.filter_by(doctor_id=doctor.id)
            .filter(
                Appointment.start_time < end,
                Appointment.end_time > start,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .first()
        )
        if conflict:
            flash(
                "The selected doctor is not available at that time. Please choose a different slot.",
                "danger",
            )
            return render_template("patient/book_appointment.html", form=form)

        config = HospitalConfig.query.first()
        fee = doctor.consultation_fee or (
            config.default_consultation_fee if config else 50
        )

        appt = Appointment(
            patient_id=patient_profile.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            start_time=start,
            end_time=end,
            reason=form.reason.data,
            status=AppointmentStatus.CONFIRMED,
            consultation_fee=fee,
        )
        db.session.add(appt)
        db.session.flush()

        revenue = RevenueRecord(
            appointment_id=appt.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            amount_cents=fee * 100,
        )
        db.session.add(revenue)

        _create_notification(
            current_user.id,
            NotificationType.APPOINTMENT_CONFIRMATION,
            f"Your appointment with Dr. {doctor.user.full_name} on {start} is confirmed.",
        )

        if doctor.user:
            _create_notification(
                doctor.user.id,
                NotificationType.APPOINTMENT_CONFIRMATION,
                f"New appointment booked with {current_user.full_name} on {start}.",
            )

        db.session.commit()
        flash("Appointment booked successfully.", "success")
        return redirect(url_for("patient.dashboard"))

    return render_template("patient/book_appointment.html", form=form)


@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if not current_user.is_patient or appt.patient.user_id != current_user.id:
        flash("You cannot modify this appointment.", "danger")
        return redirect(url_for("patient.dashboard"))
    appt.status = AppointmentStatus.CANCELLED
    _create_notification(
        current_user.id,
        NotificationType.APPOINTMENT_CANCELLED,
        f"Your appointment on {appt.start_time} was cancelled.",
    )
    if appt.doctor.user:
        _create_notification(
            appt.doctor.user.id,
            NotificationType.APPOINTMENT_CANCELLED,
            f"Appointment with {current_user.full_name} on {appt.start_time} was cancelled.",
        )
    db.session.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("patient.dashboard"))

