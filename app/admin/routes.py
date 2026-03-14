from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from .. import db
from ..models import (
    User,
    RoleEnum,
    Department,
    DoctorProfile,
    StaffProfile,
    HospitalConfig,
    SubscriptionPlan,
)

admin_bp = Blueprint("admin", __name__)


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("Administrator access required.", "danger")
        return False
    return True


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    user_count = User.query.count()
    doctor_count = User.query.filter_by(role=RoleEnum.DOCTOR).count()
    staff_count = User.query.filter_by(role=RoleEnum.STAFF).count()
    patient_count = User.query.filter_by(role=RoleEnum.PATIENT).count()
    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        doctor_count=doctor_count,
        staff_count=staff_count,
        patient_count=patient_count,
    )


@admin_bp.route("/doctors", methods=["GET", "POST"])
@login_required
def manage_doctors():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        user_id = int(request.form.get("user_id"))
        department_id = request.form.get("department_id")
        user = User.query.get_or_404(user_id)
        user.role = RoleEnum.DOCTOR
        if not user.doctor_profile:
            user.doctor_profile = DoctorProfile()
        if department_id:
            user.doctor_profile.department_id = int(department_id)
        db.session.commit()
        flash("Doctor updated.", "success")
        return redirect(url_for("admin.manage_doctors"))
    doctors = DoctorProfile.query.all()
    departments = Department.query.all()
    return render_template(
        "admin/manage_doctors.html", doctors=doctors, departments=departments
    )


@admin_bp.route("/departments", methods=["GET", "POST"])
@login_required
def manage_departments():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        if name:
            dept = Department(name=name, description=description)
            db.session.add(dept)
            db.session.commit()
            flash("Department added.", "success")
    departments = Department.query.all()
    return render_template("admin/manage_departments.html", departments=departments)


@admin_bp.route("/staff", methods=["GET", "POST"])
@login_required
def manage_staff():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        staff_id = int(request.form.get("staff_id"))
        action = request.form.get("action")
        staff = StaffProfile.query.get_or_404(staff_id)
        if action == "approve":
            staff.approved = True
        elif action == "revoke":
            staff.approved = False
        db.session.commit()
        flash("Staff status updated.", "success")
        return redirect(url_for("admin.manage_staff"))
    staff_members = StaffProfile.query.all()
    return render_template("admin/manage_staff.html", staff_members=staff_members)


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
def manage_users():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        user_id = int(request.form.get("user_id"))
        action = request.form.get("action")
        user = User.query.get_or_404(user_id)
        if action == "suspend":
            user.is_active_account = False
        elif action == "activate":
            user.is_active_account = True
        elif action == "delete":
            db.session.delete(user)
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.manage_users"))
    users = User.query.all()
    return render_template("admin/manage_users.html", users=users)


@admin_bp.route("/config", methods=["GET", "POST"])
@login_required
def config():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    config = HospitalConfig.query.first()
    if not config:
        config = HospitalConfig()
        db.session.add(config)
        db.session.commit()
    if request.method == "POST":
        config.name = request.form.get("name") or config.name
        config.description = request.form.get("description") or config.description
        config.ceo_name = request.form.get("ceo_name") or config.ceo_name
        config.ceo_bio = request.form.get("ceo_bio") or config.ceo_bio
        config.homepage_content = (
            request.form.get("homepage_content") or config.homepage_content
        )
        config.pricing_page_content = (
            request.form.get("pricing_page_content") or config.pricing_page_content
        )
        config.default_consultation_fee = int(
            request.form.get("default_consultation_fee")
            or config.default_consultation_fee
        )
        config.online_booking_enabled = (
            request.form.get("online_booking_enabled") == "on"
        )
        db.session.commit()
        flash("Configuration updated.", "success")
        return redirect(url_for("admin.config"))
    return render_template("admin/config.html", config=config)


@admin_bp.route("/pricing", methods=["GET", "POST"])
@login_required
def pricing():
    if not admin_required():
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        monthly_price = request.form.get("monthly_price")
        per_appointment_fee = request.form.get("per_appointment_fee")
        if name and monthly_price and per_appointment_fee:
            plan = SubscriptionPlan(
                name=name,
                description=description,
                monthly_price=int(monthly_price),
                per_appointment_fee=int(per_appointment_fee),
            )
            db.session.add(plan)
            db.session.commit()
            flash("Subscription plan saved.", "success")
    plans = SubscriptionPlan.query.all()
    return render_template("admin/pricing.html", plans=plans)

