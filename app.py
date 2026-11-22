import os

from dotenv import load_dotenv
from flask import (Flask, abort, flash, make_response, redirect,
                   render_template, request)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import login_manager
from models import get_user_by_username
from utils.db import db
from utils.pdf import generate_pdf

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

login_manager.init_app(app)
setattr(login_manager, "login_view", "login")




# These are the constants. they are given in caps by convention as they are to remain untouched/unchanged
# These determine the table and column names so that the user can on modify the entries

SECTIONS = {
    "education": {
        "table": "education",
        "pk": "education_id",
        "template": "edit/edit_education.html",
        "fields": ["institution", "degree", "field_of_study",
                   "start_date", "end_date", "gpa"],
        "required": ["institution", "degree", "field_of_study", "gpa"],
    },
    "experience": {
        "table": "experience",
        "pk": "exp_id",
        "template": "edit/edit_experience.html",
        "fields": ["company", "role", "start_date", "end_date", "description"],
        "required": ["company", "role"],
    },
    "projects": {
        "table": "projects",
        "pk": "project_id",
        "template": "edit/edit_projects.html",
        "fields": ["title", "description", "link", "start_date", "end_date"],
        "required": ["title"],
    },
}

CONTACT_FIELDS = ["full_name", "phone", "location",
                  "linkedin", "github", "portfolio"]


# These are helping functions which gets the values from the forms which the user submits
def get_form_values(fields):
    
    values = {}
    for field in fields:
        value = request.form.get(field, "").strip()
        values[field] = value if value else None
    return values

# To get the different entries of the form such a education / projects, etc.
def get_entries(cfg):
    return db.execute(
        f"SELECT * FROM {cfg['table']} WHERE user_id = ? ORDER BY {cfg['pk']}",
        current_user.id,
    )

# To fetch the entries of a particular user
def get_entry(cfg, entry_id):
    """Fetch one entry, but only if it belongs to the logged-in user."""
    rows = db.execute(
        f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']} = ? AND user_id = ?",
        entry_id, current_user.id,
    )
    return rows[0] if rows else None


def get_resume_data(user_id):
    """Assemble everything the resume template needs. Used by preview and download."""
    contact_rows = db.execute("SELECT * FROM contact WHERE user_id = ?", user_id)
    summary_rows = db.execute("SELECT content FROM summary WHERE user_id = ?", user_id)

    return {
        "contact": contact_rows[0] if contact_rows else {},
        "email": current_user.email,
        "summary": (summary_rows[0]["content"] or "") if summary_rows else "",
        "education": db.execute(
            "SELECT * FROM education WHERE user_id = ? ORDER BY education_id", user_id),
        "experience": db.execute(
            "SELECT * FROM experience WHERE user_id = ? ORDER BY exp_id", user_id),
        "projects": db.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY project_id", user_id),
        "skills": db.execute(
            "SELECT * FROM skills WHERE user_id = ? ORDER BY skill_id", user_id),
    }


# This defines the route to the landing page 
@app.route("/")
def index():
    return render_template("index.html")


# This is the route to the register page
@app.route("/register", methods=["GET", "POST"])
def register_user():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "GET":
        return render_template("register.html")

    # This gets the various details which the user inputs 
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")

    # checks whether the field is empty or not 
    if not username or not email or not password or not confirmation:
        flash("Please fill in all fields")
        return render_template("register.html")

    # validates that the password matches the confirm password
    if password != confirmation:
        flash("Passwords do not match")
        return render_template("register.html")

    # validates the length of the password
    if len(password) < 8:
        flash("Password must be at least 8 characters")
        return render_template("register.html")

    # checks whether a username is available or taken
    if get_user_by_username(username):
        flash("Username already taken")
        return render_template("register.html")

    hashed = generate_password_hash(password)
    try:
        db.execute(
            "INSERT INTO users (username, email, pwd_hash) VALUES (?, ?, ?)",
            username, email, hashed,
        )
    except ValueError:
        flash("That email is already registered")
        return render_template("register.html")

    flash("Account created! Please log in.")
    return redirect("/login")

# route for login, in case account already exists
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Please enter username and password")
        return render_template("login.html")

    user = get_user_by_username(username)

    if user is None or not check_password_hash(user.hash, password):
        flash("Invalid username or password")
        return render_template("login.html")

    login_user(user)
    return redirect("/dashboard")

# to logout from an account
@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out")
    return redirect("/login")


# login route to the dashboard
@app.route("/dashboard")
# This line ensurs that the dashboard is displayed only when the user is logged in.
@login_required
def dashboard():
    uid = current_user.id

    status = {
        "contact": bool(db.execute("SELECT 1 FROM contact WHERE user_id = ?", uid)),
        "summary": bool(db.execute("SELECT 1 FROM summary WHERE user_id = ?", uid)),
    }

    for table in ("education", "experience", "skills", "projects"):
        rows = db.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE user_id = ?", uid)
        status[table] = rows[0]["n"]

    return render_template("dashboard.html", status=status)


# insert or update the details of the contact section
@app.route("/edit/contact", methods=["GET", "POST"])
@login_required
def edit_contact():
    contact = {}

    if request.method == "POST":
        values = get_form_values(CONTACT_FIELDS)

        if not values["full_name"]:
            flash("Full name is required")
            contact = values  # keep what the user typed
        else:
            columns = ", ".join(CONTACT_FIELDS)
            marks = ", ".join("?" for _ in CONTACT_FIELDS)
            updates = ", ".join(f"{f} = excluded.{f}" for f in CONTACT_FIELDS)
            db.execute(
                f"INSERT INTO contact (user_id, {columns}) VALUES (?, {marks}) "
                f"ON CONFLICT(user_id) DO UPDATE SET {updates}",
                current_user.id, *values.values(),
            )
            flash("Contact details saved")
            return redirect("/dashboard")

    if not contact:
        rows = db.execute("SELECT * FROM contact WHERE user_id = ?", current_user.id)
        contact = rows[0] if rows else {}

    return render_template("edit/edit_contact.html", contact=contact)

# insert or update the details of the summary section
@app.route("/edit/summary", methods=["GET", "POST"])
@login_required
def edit_summary():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        db.execute(
            "INSERT INTO summary (user_id, content) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET content = excluded.content",
            current_user.id, content,
        )
        flash("Summary saved")
        return redirect("/dashboard")

    rows = db.execute("SELECT content FROM summary WHERE user_id = ?", current_user.id)
    summary = (rows[0]["content"] or "") if rows else ""
    return render_template("edit/edit_summary.html", summary=summary)


# insert or update or delete the details of the skills section
@app.route("/edit/skills", methods=["GET", "POST"])
@login_required
def edit_skills():
    if request.method == "POST":
        skill_name = request.form.get("skill_name", "").strip()
        if not skill_name:
            flash("Please enter a skill")
        else:
            db.execute(
                "INSERT INTO skills (user_id, skill_name) VALUES (?, ?)",
                current_user.id, skill_name,
            )
            flash("Skill added")
        return redirect("/edit/skills")

    skills = db.execute(
        "SELECT * FROM skills WHERE user_id = ? ORDER BY skill_id", current_user.id)
    return render_template("edit/edit_skills.html", skills=skills)


@app.route("/edit/skills/<int:skill_id>/delete", methods=["POST"])
@login_required
def delete_skill(skill_id):
    # user_id in the WHERE clause is the ownership check
    db.execute(
        "DELETE FROM skills WHERE skill_id = ? AND user_id = ?",
        skill_id, current_user.id,
    )
    flash("Skill removed")
    return redirect("/edit/skills")


# ---------------------------------------------------------------
# Many-entry sections: education, experience, projects
# One set of routes serves all three, driven by the SECTIONS dict.
# ---------------------------------------------------------------
@app.route("/edit/<section>", methods=["GET", "POST"])
@login_required
def edit_section(section):
    cfg = SECTIONS.get(section)
    if cfg is None:
        abort(404)

    if request.method == "POST":
        values = get_form_values(cfg["fields"])

        if any(not values[f] for f in cfg["required"]):
            flash("Please fill in all required fields")
        else:
            columns = ", ".join(cfg["fields"])
            marks = ", ".join("?" for _ in cfg["fields"])
            db.execute(
                f"INSERT INTO {cfg['table']} (user_id, {columns}) VALUES (?, {marks})",
                current_user.id, *values.values(),
            )
            flash("Entry added")
            return redirect(f"/edit/{section}")

    return render_template(cfg["template"], entries=get_entries(cfg), entry=None)


@app.route("/edit/<section>/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(section, entry_id):
    cfg = SECTIONS.get(section)
    if cfg is None:
        abort(404)

    entry = get_entry(cfg, entry_id)
    if entry is None:
        abort(404)  # missing, or belongs to someone else

    if request.method == "POST":
        values = get_form_values(cfg["fields"])

        if any(not values[f] for f in cfg["required"]):
            flash("Please fill in all required fields")
        else:
            assignments = ", ".join(f"{f} = ?" for f in cfg["fields"])
            db.execute(
                f"UPDATE {cfg['table']} SET {assignments} "
                f"WHERE {cfg['pk']} = ? AND user_id = ?",
                *values.values(), entry_id, current_user.id,
            )
            flash("Entry updated")
            return redirect(f"/edit/{section}")

    return render_template(cfg["template"], entries=get_entries(cfg), entry=entry)


@app.route("/edit/<section>/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(section, entry_id):
    cfg = SECTIONS.get(section)
    if cfg is None:
        abort(404)

    db.execute(
        f"DELETE FROM {cfg['table']} WHERE {cfg['pk']} = ? AND user_id = ?",
        entry_id, current_user.id,
    )
    flash("Entry deleted")
    return redirect(f"/edit/{section}")


# this is the route to preview the resume 
@app.route("/preview")
@login_required
def preview():
    data = get_resume_data(current_user.id)
    return render_template("resume/resume_template.html", preview=True, **data)

# and this is to download it in a pdf format
@app.route("/download")
@login_required
def download():
    data = get_resume_data(current_user.id)
    html = render_template("resume/resume_template.html", **data)

    
    try:
        pdf = generate_pdf(html, base_url=request.url_root)
    except Exception as e:
        flash("Could not generate the PDF. "
              "Use your browser's Print > Save as PDF from the preview for now.")
        return redirect("/preview")

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=resume.pdf"
    return response


if __name__ == "__main__":
    app.run(debug=False)