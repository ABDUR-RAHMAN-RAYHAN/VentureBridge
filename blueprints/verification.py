from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import IdentityVerification, VerificationPhoto
from forms import VerificationForm
from utils import save_base64_image, log_action

bp = Blueprint("verification", __name__, url_prefix="/verification")


@bp.route("/", methods=["GET", "POST"])
@login_required
def upload():
    form = VerificationForm()
    if form.validate_on_submit():
        verification = IdentityVerification(user_id=current_user.id, doc_type=form.doc_type.data)
        db.session.add(verification)
        db.session.flush()
        try:
            for slot, field in enumerate([form.photo_1, form.photo_2, form.photo_3], start=1):
                fname = save_base64_image(field.data, "verification")
                db.session.add(VerificationPhoto(verification_id=verification.id, filename=fname,
                                                  slot=slot, captured_live=True))
        except ValueError as e:
            db.session.rollback()
            flash(f"Photo capture failed: {e}. Please retake the live photos.", "danger")
            return redirect(url_for("verification.upload"))
        db.session.commit()
        log_action("identity_verification_submitted", f"doc_type={form.doc_type.data}")
        flash("Your verification submission (with 3 live photos) has been sent for admin review.", "success")
        return redirect(url_for("verification.upload"))

    history = IdentityVerification.query.filter_by(user_id=current_user.id).order_by(
        IdentityVerification.submitted_at.desc()).all()
    return render_template("verification/upload.html", form=form, history=history)
