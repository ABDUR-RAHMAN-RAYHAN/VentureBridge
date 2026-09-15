from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import (User, Startup, Job, JobApplication, InvestmentRequest,
                     IdentityVerification, StartupDocument, AuditLog, Connection)
from forms import ProfileForm, ContactForm
from utils import save_upload, log_action

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    stats = {
        "members": User.query.filter_by(is_active_account=True).count(),
        "startups": Startup.query.filter_by(is_active=True).count(),
        "jobs": Job.query.filter_by(status="open").count(),
        "verified_startups": Startup.query.filter_by(document_status="approved").count(),
    }
    featured = Startup.query.filter_by(is_active=True, document_status="approved").order_by(Startup.created_at.desc()).limit(3).all()
    return render_template("public/index.html", stats=stats, featured=featured)


@bp.route("/about")
def about():
    return render_template("public/about.html")


@bp.route("/privacy")
def privacy():
    return render_template("public/privacy.html")


@bp.route("/terms")
def terms():
    return render_template("public/terms.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        log_action("contact_form_submitted", f"from={form.email.data}")
        flash("Thanks for reaching out — we'll get back to you shortly.", "success")
        return redirect(url_for("main.contact"))
    return render_template("public/contact.html", form=form)


@bp.route("/dashboard")
@login_required
def dashboard():
    ctx = {}
    if current_user.role == "founder":
        startup_ids = [s.id for s in current_user.startups]
        ctx["startup_count"] = len(startup_ids)
        ctx["active_jobs"] = Job.query.filter(Job.startup_id.in_(startup_ids), Job.status == "open").count() if startup_ids else 0
        ctx["applications_received"] = JobApplication.query.join(Job).filter(Job.startup_id.in_(startup_ids)).count() if startup_ids else 0
        ctx["pending_requests"] = InvestmentRequest.query.filter(
            InvestmentRequest.startup_id.in_(startup_ids), InvestmentRequest.status == "pending").count() if startup_ids else 0
        ctx["startups"] = current_user.startups.all()
        # chart: application status breakdown
        rows = db.session.query(JobApplication.status, func.count(JobApplication.id)).join(Job).filter(
            Job.startup_id.in_(startup_ids)).group_by(JobApplication.status).all() if startup_ids else []
        ctx["chart_labels"] = [r[0] for r in rows]
        ctx["chart_data"] = [r[1] for r in rows]

    elif current_user.role == "investor":
        reqs = InvestmentRequest.query.filter_by(investor_id=current_user.id)
        ctx["sent"] = reqs.count()
        ctx["accepted"] = reqs.filter_by(status="accepted").count()
        ctx["connections"] = Connection.query.filter(
            (Connection.user_a_id == current_user.id) | (Connection.user_b_id == current_user.id)).count()
        ctx["requests"] = reqs.order_by(InvestmentRequest.created_at.desc()).all()
        rows = db.session.query(InvestmentRequest.status, func.count(InvestmentRequest.id)).filter_by(
            investor_id=current_user.id).group_by(InvestmentRequest.status).all()
        ctx["chart_labels"] = [r[0] for r in rows]
        ctx["chart_data"] = [r[1] for r in rows]

    elif current_user.role == "jobseeker":
        apps = JobApplication.query.filter_by(applicant_id=current_user.id)
        ctx["applications_sent"] = apps.count()
        ctx["shortlisted"] = apps.filter_by(status="shortlisted").count()
        ctx["applications"] = apps.order_by(JobApplication.applied_at.desc()).all()
        rows = db.session.query(JobApplication.status, func.count(JobApplication.id)).filter_by(
            applicant_id=current_user.id).group_by(JobApplication.status).all()
        ctx["chart_labels"] = [r[0] for r in rows]
        ctx["chart_data"] = [r[1] for r in rows]

    elif current_user.role == "admin":
        ctx["total_users"] = User.query.count()
        ctx["by_role"] = dict(db.session.query(User.role, func.count(User.id)).group_by(User.role).all())
        ctx["total_startups"] = Startup.query.count()
        ctx["pending_docs"] = StartupDocument.query.filter_by(status="pending").count()
        ctx["pending_verifications"] = IdentityVerification.query.filter_by(status="pending").count()
        rows = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        ctx["chart_labels"] = [r[0] for r in rows]
        ctx["chart_data"] = [r[1] for r in rows]

    return render_template("dashboard/dashboard.html", **ctx)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile = current_user.profile
    form = ProfileForm(obj=profile)
    if form.validate_on_submit():
        if form.photo.data:
            try:
                filename = save_upload(form.photo.data, "logos", {"png", "jpg", "jpeg"})
                profile.photo = filename
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("profile/edit.html", form=form, profile=profile)
        profile.phone = form.phone.data
        profile.bio = form.bio.data
        profile.location = form.location.data
        profile.education = form.education.data
        profile.experience = form.experience.data
        profile.industry = form.industry.data
        profile.skills = form.skills.data
        profile.interests = form.interests.data
        db.session.commit()
        log_action("profile_updated")
        flash("Profile updated successfully.", "success")
        return redirect(url_for("main.profile"))
    return render_template("profile/edit.html", form=form, profile=profile)
