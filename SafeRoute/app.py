"""SafeRoute — Community Safety Route Planner
CPU4106 Level 4 Computing Group Project

Flask application. Every query maps directly onto the MySQL tables created by
database/saferoute.sql:

    USERS   (UserID, FullName, Email, PasswordHash, DateCreated)
    REPORTS (ReportID, UserID, IncidentType, Description, Location, DateReported)
    ROUTES  (RouteID, UserID, StartPoint, EndPoint, SafetyScore, SearchDate)

Access rules: Home, Register and Login are public. Dashboard, Report Hazard,
View Reports, Safety Map and Route Search require a logged-in user."""

from datetime import date
from functools import wraps
from math import asin, cos, radians, sin, sqrt

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

INCIDENT_TYPES = [
    "Poor Lighting",
    "Pothole",
    "Flooding",
    "Road Damage",
    "Suspicious Activity",
    "Anti-Social Behaviour",
    "Unsafe Crossing",
]

# Coordinates for the prototype's sample geography (Wembley, London).
KNOWN_LOCATIONS = {
    "Wembley Park Station": (51.5634, -0.2796),
    "Wembley Central Station": (51.5527, -0.2965),
    "Wembley Stadium": (51.5560, -0.2794),
    "High Road Wembley": (51.5522, -0.2952),
    "Olympic Way": (51.5589, -0.2792),
    "College Road, Wembley": (51.5576, -0.2897),
    "North Circular Road (A406)": (51.5481, -0.2683),
    "Forty Lane": (51.5729, -0.2835),
    "Preston Road": (51.5722, -0.2948),
    "Alperton Station": (51.5407, -0.2995),
    "Ealing Road": (51.5470, -0.2980),
    "Kingsbury Road": (51.5750, -0.2660),
}
MAP_CENTER = (51.5565, -0.2865)


# ------------------------------------------------------------------ database
def get_connection():
    """Open a connection to the saferoute MySQL database."""
    return mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
    )


def fetch_all(sql, params=()):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# ------------------------------------------------------------ safety scoring
def location_coords(name):
    """Coordinates for a REPORTS.Location value (falls back to the map centre)."""
    return KNOWN_LOCATIONS.get(name, MAP_CENTER)


def distance_km(a, b):
    """Great-circle distance between two (lat, lng) points."""
    radius = 6371
    d_lat = radians(b[0] - a[0])
    d_lng = radians(b[1] - a[1])
    h = (
        sin(d_lat / 2) ** 2
        + cos(radians(a[0])) * cos(radians(b[0])) * sin(d_lng / 2) ** 2
    )
    return 2 * radius * asin(sqrt(h))


def distance_to_segment_km(a, point, b):
    """Shortest distance from a point to the straight line a -> b."""
    def to_xy(lat_lng):
        return (lat_lng[1] * 111.32 * cos(radians(lat_lng[0])), lat_lng[0] * 110.574)

    ax, ay = to_xy(a)
    bx, by = to_xy(b)
    px, py = to_xy(point)
    dx, dy = bx - ax, by - ay
    length_squared = dx * dx + dy * dy
    t = 0 if length_squared == 0 else ((px - ax) * dx + (py - ay) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    return sqrt((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2)


def safety_score(incident_count):
    """SAFETY SCORE MODEL: 100 - (Number of Incidents x 5), never below 0."""
    return max(0, min(100, 100 - incident_count * config.INCIDENTS_PER_POINT))


def safety_band(score):
    """Band label and colour used by the interface."""
    if score >= 90:
        return {"label": "SAFE", "css": "band-safe",
                "advice": "Low incident density on this corridor. Standard precautions apply."}
    if score >= 70:
        return {"label": "MODERATE RISK", "css": "band-moderate",
                "advice": "Several recent incidents nearby. Stay on lit main roads and travel in groups."}
    return {"label": "HIGH RISK", "css": "band-high",
            "advice": "High incident density reported. Consider an alternative route or travel in daylight."}


def incidents_on_corridor(start_point, end_point, reports):
    """Reports within the corridor radius of the straight line between two points."""
    start = location_coords(start_point)
    end = location_coords(end_point)
    return [
        r for r in reports
        if distance_to_segment_km(start, location_coords(r["Location"]), end)
        <= config.ROUTE_CORRIDOR_KM
    ]


# --------------------------------------------------------------------- auth
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if not session.get("user_id"):
        return None
    return fetch_one(
        "SELECT UserID, FullName, Email, DateCreated FROM users WHERE UserID = %s",
        (session["user_id"],),
    )


@app.context_processor
def inject_user():
    return {"current_user": current_user(), "incident_types": INCIDENT_TYPES}


@app.route("/")
def home():
    """Public landing page with community statistics."""
    stats = fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM reports) AS total_reports,
          (SELECT COUNT(*) FROM users)   AS total_users,
          (SELECT COUNT(*) FROM routes)  AS total_routes
        """
    )
    return render_template("home.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("fullName", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirmPassword", "")

        if len(full_name) < 2:
            flash("Please enter your full name.", "danger")
        elif "@" not in email:
            flash("Please enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Your password must be at least 8 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif fetch_one("SELECT UserID FROM users WHERE Email = %s", (email,)):
            flash("An account with that email already exists.", "danger")
        else:
            execute(
                "INSERT INTO users (FullName, Email, PasswordHash) VALUES (%s, %s, %s)",
                (full_name, email, generate_password_hash(password)),
            )
            flash("Account created successfully. You can now log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html", full_name=full_name, email=email)

    return render_template("register.html", full_name="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = fetch_one("SELECT * FROM users WHERE Email = %s", (email,))

        if user and check_password_hash(user["PasswordHash"], password):
            session["user_id"] = user["UserID"]
            session["full_name"] = user["FullName"]
            flash("Welcome back, {0}.".format(user["FullName"]), "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return render_template("login.html", email=email)

    return render_template("login.html", email="")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------- dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    counts = fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM reports WHERE UserID = %s) AS my_reports,
          (SELECT COUNT(*) FROM routes  WHERE UserID = %s) AS my_routes,
          (SELECT COUNT(*) FROM reports)                   AS community_reports
        """,
        (user_id, user_id),
    )
    recent = fetch_all(
        """
        SELECT IncidentType, Location, DateReported
        FROM reports ORDER BY DateReported DESC, ReportID DESC LIMIT 5
        """
    )
    latest_route = fetch_one(
        """
        SELECT StartPoint, EndPoint, SafetyScore, SearchDate
        FROM routes WHERE UserID = %s ORDER BY SearchDate DESC, RouteID DESC LIMIT 1
        """,
        (user_id,),
    )
    area_score = safety_score(counts["community_reports"])

    return render_template(
        "dashboard.html",
        counts=counts,
        recent=recent,
        latest_route=latest_route,
        area_score=area_score,
        area_band=safety_band(area_score),
    )


# ----------------------------------------------------------- report a hazard
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        incident_type = request.form.get("incidentType", "")
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        date_reported = request.form.get("dateReported", "")

        if incident_type not in INCIDENT_TYPES:
            flash("Please select an incident type.", "danger")
        elif len(description) < 10:
            flash("Please add a short description (at least 10 characters).", "danger")
        elif not location:
            flash("Please enter the location of the hazard.", "danger")
        elif not date_reported:
            flash("Please choose the date reported.", "danger")
        else:
            execute(
                """
                INSERT INTO reports
                    (UserID, IncidentType, Description, Location, DateReported)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session["user_id"], incident_type, description, location, date_reported),
            )
            flash("Report submitted successfully. Thank you for helping your community.", "success")
            return redirect(url_for("reports"))

    return render_template("report.html", today=date.today().isoformat(), locations=sorted(KNOWN_LOCATIONS))


# ------------------------------------------------------------ view reports
@app.route("/reports")
@login_required
def reports():
    search_term = request.args.get("q", "").strip()
    incident_type = request.args.get("type", "").strip()

    sql = """
        SELECT ReportID, IncidentType, Description, Location, DateReported
        FROM reports WHERE 1 = 1
    """
    params = []
    if incident_type:
        sql += " AND IncidentType = %s"
        params.append(incident_type)
    if search_term:
        sql += " AND (Description LIKE %s OR Location LIKE %s)"
        params.extend(["%" + search_term + "%", "%" + search_term + "%"])
    sql += " ORDER BY DateReported DESC, ReportID DESC"

    rows = fetch_all(sql, tuple(params))
    total = fetch_one("SELECT COUNT(*) AS total FROM reports")["total"]

    return render_template(
        "reports.html",
        reports=rows,
        total=total,
        search_term=search_term,
        selected_type=incident_type,
    )


# -------------------------------------------------------------- safety map
@app.route("/map")
@login_required
def map_view():
    rows = fetch_all(
        """
        SELECT ReportID, IncidentType, Description, Location, DateReported
        FROM reports ORDER BY DateReported DESC, ReportID DESC LIMIT 200
        """
    )
    reports_with_coords = []
    for row in rows:
        lat, lng = location_coords(row["Location"])
        reports_with_coords.append(
            {
                "id": row["ReportID"],
                "type": row["IncidentType"],
                "description": row["Description"],
                "location": row["Location"],
                "date": row["DateReported"].strftime("%d %b %Y"),
                "lat": lat,
                "lng": lng,
            }
        )
    return render_template(
        "map.html",
        reports=reports_with_coords,
        recent=rows[:8],
        center=MAP_CENTER,
    )


# ------------------------------------------------------------- route search
@app.route("/routes", methods=["GET", "POST"])
@login_required
def routes():
    result = None
    start_point = end_point = ""

    if request.method == "POST":
        start_point = request.form.get("startPoint", "").strip()
        end_point = request.form.get("endPoint", "").strip()

        if not start_point:
            flash("Please enter a start location.", "danger")
        elif not end_point:
            flash("Please enter a destination.", "danger")
        elif start_point == end_point:
            flash("The start and destination must be different.", "danger")
        else:
            all_reports = fetch_all("SELECT IncidentType, Location, DateReported FROM reports")
            nearby = incidents_on_corridor(start_point, end_point, all_reports)
            score = safety_score(len(nearby))
            band = safety_band(score)

            execute(
                """
                INSERT INTO routes
                    (UserID, StartPoint, EndPoint, SafetyScore, SearchDate)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session["user_id"], start_point, end_point, score, date.today().isoformat()),
            )

            result = {
                "start": start_point,
                "end": end_point,
                "score": score,
                "band": band,
                "incidents": nearby,
                "distance": round(distance_km(location_coords(start_point), location_coords(end_point)), 1),
                "start_coords": location_coords(start_point),
                "end_coords": location_coords(end_point),
            }

    history = fetch_all(
        """
        SELECT StartPoint, EndPoint, SafetyScore, SearchDate
        FROM routes WHERE UserID = %s ORDER BY SearchDate DESC, RouteID DESC LIMIT 5
        """,
        (session["user_id"],),
    )

    return render_template(
        "routes.html",
        result=result,
        history=history,
        start_point=start_point,
        end_point=end_point,
        locations=sorted(KNOWN_LOCATIONS),
        corridor_metres=int(config.ROUTE_CORRIDOR_KM * 1000),
    )


if __name__ == "__main__":
    app.run(debug=True)
