from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    TextAreaField,
    BooleanField,
    DateTimeLocalField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
    )
    role = SelectField(
        "Role",
        choices=[
            ("patient", "Patient"),
            ("doctor", "Doctor"),
            ("staff", "Hospital Staff"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Create Account")


class AppointmentForm(FlaskForm):
    doctor_id = SelectField("Doctor", coerce=int, validators=[DataRequired()])
    start_time = DateTimeLocalField(
        "Appointment Date & Time",
        format="%Y-%m-%dT%H:%M",
        default=datetime.utcnow,
        validators=[DataRequired()],
    )
    reason = TextAreaField("Reason for Visit", validators=[DataRequired()])
    submit = SubmitField("Book Appointment")


class AvailabilityForm(FlaskForm):
    weekday = SelectField(
        "Weekday",
        coerce=int,
        choices=[
            (0, "Monday"),
            (1, "Tuesday"),
            (2, "Wednesday"),
            (3, "Thursday"),
            (4, "Friday"),
            (5, "Saturday"),
            (6, "Sunday"),
        ],
        validators=[DataRequired()],
    )
    start_time = StringField("Start Time (HH:MM)", validators=[DataRequired()])
    end_time = StringField("End Time (HH:MM)", validators=[DataRequired()])
    submit = SubmitField("Save Availability")

