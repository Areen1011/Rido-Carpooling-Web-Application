import os
import requests as http_requests
from datetime import datetime, timedelta, date

from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection

app = Flask(__name__)
app.config.from_object("config.Config")


# ===== HOME ROUTE =====
@app.route("/")
def home():
    return render_template("home.html", rides=None)


# ===== REGISTER ROUTE =====
@app.route("/register", methods=["GET", "POST"])
def register():

    max_dob = date.today().replace(year=date.today().year - 18)

    if request.method == "POST":

        db = get_db_connection()
        cursor = db.cursor()

        try:

            # Check if email already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s", (request.form["email"],)
            )

            if cursor.fetchone():
                return render_template(
                    "register.html", error="Email already registered.", max_dob=max_dob
                )

            # Check Age (18+)
            dob = datetime.strptime(request.form["dob"], "%Y-%m-%d").date()

            today = date.today()

            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )

            if age < 18:
                return render_template(
                    "register.html",
                    error="You must be at least 18 years old to register.",
                    max_dob=max_dob,
                )

            # Hash password
            hashed_password = generate_password_hash(request.form["password"])

            # Insert new user
            cursor.execute(
                """
                INSERT INTO users
                (fname, lname, mobile, email, dob, password)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    request.form["fname"],
                    request.form["lname"],
                    request.form["mobile"],
                    request.form["email"],
                    request.form["dob"],
                    hashed_password,
                ),
            )

            db.commit()

            return redirect(url_for("login"))

        finally:
            cursor.close()
            db.close()

    return render_template("register.html", max_dob=max_dob)


# ===== LOGIN ROUTE =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, fname, email, mobile, password, role FROM users WHERE email = %s",
                (request.form["email"],),
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], request.form["password"]):
                session["user_id"] = user["id"]
                session["fname"] = user["fname"]
                session["email"] = user["email"]
                session["mobile"] = user["mobile"]
                session["role"] = user["role"]

                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))

                next_page = session.pop("next", None)
                return redirect(next_page or "/")

            return render_template("login.html", error="Invalid email or password.")

        finally:
            cursor.close()
            db.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin-dashboard")
def admin_dashboard():

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        # Total Users
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()["total"]

        # Total Rides
        cursor.execute("SELECT COUNT(*) AS total FROM rides")
        total_rides = cursor.fetchone()["total"]

        # Total Bookings
        cursor.execute("SELECT COUNT(*) AS total FROM bookings")
        total_bookings = cursor.fetchone()["total"]

        # Confirmed Bookings
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status='confirmed'
        """)
        confirmed_bookings = cursor.fetchone()["total"]

        # Pending Bookings
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status='pending'
        """)
        pending_bookings = cursor.fetchone()["total"]

        # Rejected Bookings
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE status='rejected'
        """)
        rejected_bookings = cursor.fetchone()["total"]

        # Recent Bookings
        cursor.execute("""
            SELECT
                u.fname,
                r.from_location,
                r.to_location,
                r.ride_date,
                b.status
            FROM bookings b
            JOIN users u
                ON b.user_id = u.id
            JOIN rides r
                ON b.ride_id = r.id
            ORDER BY b.booking_time DESC
            LIMIT 5
        """)

        recent_bookings = cursor.fetchall()

        return render_template(
            "admin_dashboard.html",
            total_users=total_users,
            total_rides=total_rides,
            total_bookings=total_bookings,
            confirmed_bookings=confirmed_bookings,
            pending_bookings=pending_bookings,
            rejected_bookings=rejected_bookings,
            recent_bookings=recent_bookings,
        )

    finally:
        cursor.close()
        db.close()


# ===== ADMIN USERS ROUTE =====
@app.route("/admin-users")
def admin_users():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        if search:
            cursor.execute(
                """
                SELECT
                    id,
                    fname,
                    lname,
                    email,
                    mobile,
                    role
                FROM users
                WHERE fname LIKE %s
                   OR lname LIKE %s
                   OR email LIKE %s
                ORDER BY id DESC
                """,
                (f"%{search}%", f"%{search}%", f"%{search}%"),
            )
        else:
            cursor.execute("""
                SELECT
                    id,
                    fname,
                    lname,
                    email,
                    mobile,
                    role
                FROM users
                ORDER BY id DESC
                """)

        users = cursor.fetchall()

        return render_template(
            "admin_users.html",
            users=users,
            search=search,
        )

    finally:
        cursor.close()
        db.close()


# ===== ADMIN USER DETAILS ROUTE =====
@app.route("/admin-user/<int:user_id>")
def admin_user_details(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                fname,
                lname,
                email,
                mobile,
                dob,
                role
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                from_location,
                to_location,
                ride_date,
                ride_time,
                seats,
                fare
            FROM rides
            WHERE driver_id = %s
            ORDER BY ride_date DESC
            """,
            (user_id,),
        )
        posted_rides = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                r.from_location,
                r.to_location,
                r.ride_date,
                r.ride_time,
                b.seats_booked,
                b.status
            FROM bookings b
            JOIN rides r ON b.ride_id = r.id
            WHERE b.user_id = %s
            ORDER BY b.id DESC
            """,
            (user_id,),
        )
        booked_rides = cursor.fetchall()

        return render_template(
            "admin_user_details.html",
            user=user,
            posted_rides=posted_rides,
            booked_rides=booked_rides,
        )

    finally:
        cursor.close()
        db.close()


# ===== ADMIN DELETE USER ROUTE =====
@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    # Prevent admin from deleting their own account
    if user_id == session["user_id"]:
        return "You cannot delete yourself.", 403

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()

        return redirect(url_for("admin_users"))

    finally:
        cursor.close()
        db.close()


# ===== ADMIN RIDES ROUTE =====
@app.route("/admin-rides")
def admin_rides():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                r.*,
                u.fname,
                u.lname
            FROM rides r
            JOIN users u
                ON r.driver_id = u.id
            ORDER BY r.id DESC
            """)

        rides = cursor.fetchall()

        return render_template(
            "admin_rides.html",
            rides=rides,
        )

    finally:
        cursor.close()
        db.close()


# ===== ADMIN CANCEL RIDE ROUTE =====
@app.route("/admin-cancel-ride/<int:ride_id>")
def admin_cancel_ride(ride_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "UPDATE rides SET status = %s WHERE id = %s",
            ("cancelled", ride_id),
        )
        db.commit()

        return redirect(url_for("admin_rides"))

    finally:
        cursor.close()
        db.close()


# ===== ADMIN BOOKINGS ROUTE =====
@app.route("/admin-bookings")
def admin_bookings():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                b.*,
                u.fname,
                r.from_location,
                r.to_location,
                r.ride_date,
                r.ride_time
            FROM bookings b
            JOIN users u
                ON b.user_id = u.id
            JOIN rides r
                ON b.ride_id = r.id
            ORDER BY b.id DESC
            """)

        bookings = cursor.fetchall()

        return render_template(
            "admin_bookings.html",
            bookings=bookings,
        )

    finally:
        cursor.close()
        db.close()


# ===== POST RIDE ROUTE =====
@app.route("/post_ride", methods=["GET", "POST"])
def post_ride():
    if "user_id" not in session:
        session["next"] = url_for("post_ride")
        return redirect(url_for("login"))

    today = date.today().strftime("%Y-%m-%d")

    if request.method == "POST":
        from_location = request.form["from_location"]
        to_location = request.form["to_location"]
        ride_date_str = request.form["ride_date"]
        ride_time_str = request.form["ride_time"]

        if from_location.strip().lower() == to_location.strip().lower():
            return render_template(
                "post_ride.html",
                error="From and To location cannot be the same!",
                today=today,
            )

        ride_date = datetime.strptime(ride_date_str, "%Y-%m-%d").date()
        if ride_date < date.today():
            return render_template(
                "post_ride.html",
                error="Ride date cannot be in the past!",
                today=today,
            )

        ride_time = datetime.strptime(ride_time_str, "%H:%M").time()
        if ride_date == date.today() and ride_time <= datetime.now().time():
            return render_template(
                "post_ride.html",
                error="Ride time must be in the future!",
                today=today,
            )

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Check for duplicate ride
            cursor.execute(
                """
                SELECT id
                FROM rides
                WHERE driver_id = %s
                  AND ride_date = %s
                  AND ride_time = %s
                  AND status != %s
                """,
                (session["user_id"], ride_date_str, ride_time_str, "cancelled"),
            )

            if cursor.fetchone():
                return render_template(
                    "post_ride.html",
                    error="You already have a ride scheduled at this date and time!",
                    today=today,
                )

            # Get driver's mobile number
            cursor.execute(
                "SELECT mobile FROM users WHERE id = %s",
                (session["user_id"],),
            )
            driver_phone = cursor.fetchone()["mobile"]

            fare = int(request.form["fare_amount"])

            cursor.execute(
                """
                INSERT INTO rides
                (
                    driver_id,
                    from_location,
                    to_location,
                    pickup_point,
                    drop_point,
                    ride_date,
                    ride_time,
                    seats,
                    car_number,
                    car_model,
                    fare,
                    driver_phone,
                    status
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["user_id"],
                    from_location,
                    to_location,
                    request.form["pickup_point"],
                    request.form["drop_point"],
                    ride_date_str,
                    ride_time_str,
                    request.form["seats"],
                    request.form["car_number"],
                    request.form["car_model"],
                    fare,
                    driver_phone,
                    "active",
                ),
            )

            db.commit()

            return render_template(
                "post_ride.html",
                message="Ride posted successfully!",
                today=today,
            )

        finally:
            cursor.close()
            db.close()

    return render_template("post_ride.html", today=today)


# ===== SEARCH RIDE ROUTE =====
@app.route("/search-ride")
def search_ride():
    from_location = request.args.get("from_location")
    to_location = request.args.get("to_location")
    rides = []

    if from_location and to_location:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    r.*,
                    u.fname,
                    u.lname
                FROM rides r
                JOIN users u
                    ON r.driver_id = u.id
                WHERE LOWER(r.from_location) LIKE LOWER(%s)
                  AND LOWER(r.to_location) LIKE LOWER(%s)
                  AND r.seats > 0
                  AND (r.status = %s OR r.status IS NULL)
                  AND (
                        r.ride_date > CURDATE()
                        OR (
                            r.ride_date = CURDATE()
                            AND r.ride_time > CURTIME()
                        )
                      )
                  AND (%s IS NULL OR r.driver_id != %s)
                ORDER BY r.ride_date, r.ride_time
                """,
                (
                    f"%{from_location}%",
                    f"%{to_location}%",
                    "active",
                    session.get("user_id"),
                    session.get("user_id"),
                ),
            )

            rides = cursor.fetchall()

        finally:
            cursor.close()
            db.close()

    return render_template("home.html", rides=rides)


# ===== BOOK RIDE ROUTE =====
@app.route("/book-ride")
def book_ride():
    ride_id = request.args.get("ride_id")

    if "user_id" not in session:
        session["next"] = url_for("book_ride", ride_id=ride_id)
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                r.*,
                u.fname,
                u.lname
            FROM rides r
            JOIN users u
                ON r.driver_id = u.id
            WHERE r.id = %s
            """,
            (ride_id,),
        )

        ride = cursor.fetchone()

        if not ride:
            return "Ride not found", 404

        return render_template(
            "book.html",
            ride=ride,
        )

    finally:
        cursor.close()
        db.close()


# ===== CONFIRM BOOKING ROUTE =====
@app.route("/confirm-booking", methods=["POST"])
def confirm_booking():
    if "user_id" not in session:
        return redirect(url_for("login"))

    ride_id = request.form["ride_id"]
    seats_booked = int(request.form["seats_booked"])

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get ride details
        cursor.execute(
            """
            SELECT
                from_location,
                pickup_point,
                to_location,
                drop_point,
                ride_date,
                ride_time,
                fare,
                seats,
                status
            FROM rides
            WHERE id = %s
            """,
            (ride_id,),
        )

        ride = cursor.fetchone()

        # Check ride availability
        if not ride or ride["status"] == "cancelled" or ride["seats"] < seats_booked:
            return "<script>alert('Ride is not available');history.back()</script>"

        total_amount = ride["fare"] * seats_booked

        # Create booking request (Pending)
        cursor.execute(
            """
            INSERT INTO bookings
            (
                ride_id,
                user_id,
                seats_booked,
                total_amount,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                ride_id,
                session["user_id"],
                seats_booked,
                total_amount,
                "pending",
            ),
        )

        db.commit()

    finally:
        cursor.close()
        db.close()

    # Send booking request email
    send_booking_email(
        to_email=session["email"],
        user_name=session["fname"],
        ride=ride,
        seats_booked=seats_booked,
    )

    return redirect(url_for("my_booked_rides"))


# ===== MY POSTED RIDES ROUTE =====
@app.route("/my-posted-rides")
def my_posted_rides():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                from_location,
                to_location,
                pickup_point,
                drop_point,
                ride_date,
                ride_time,
                seats,
                car_number,
                car_model,
                fare,
                driver_phone,
                status
            FROM rides
            WHERE driver_id = %s
              AND status != %s
            ORDER BY ride_date DESC
            """,
            (
                session["user_id"],
                "cancelled",
            ),
        )

        posted_rides = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                b.id AS booking_id,
                b.seats_booked,
                b.total_amount,
                b.status,

                u.fname,
                u.lname,
                u.mobile,

                r.id AS ride_id,
                r.from_location,
                r.to_location,
                r.ride_date,
                r.ride_time
            FROM bookings b
            JOIN users u
                ON b.user_id = u.id
            JOIN rides r
                ON b.ride_id = r.id
            WHERE r.driver_id = %s
            ORDER BY r.id DESC, b.status
            """,
            (session["user_id"],),
        )

        requests = cursor.fetchall()

        return render_template(
            "my_posted_rides.html",
            posted_rides=posted_rides,
            requests=requests,
        )

    finally:
        cursor.close()
        db.close()


# ===== MY BOOKED RIDES ROUTE =====
@app.route("/my-booked-rides")
def my_booked_rides():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                r.from_location,
                r.to_location,
                r.pickup_point,
                r.drop_point,
                r.ride_date,
                r.ride_time,
                r.car_model,
                r.car_number,
                r.fare,

                u.fname AS driver_fname,
                u.lname AS driver_lname,

                b.id AS booking_id,
                b.seats_booked,
                b.total_amount,
                b.status
            FROM bookings b
            JOIN rides r
                ON b.ride_id = r.id
            JOIN users u
                ON r.driver_id = u.id
            WHERE b.user_id = %s
            ORDER BY b.booking_time DESC
            """,
            (session["user_id"],),
        )

        booked_rides = cursor.fetchall()

        return render_template(
            "my_booked_rides.html",
            booked_rides=booked_rides,
        )

    finally:
        cursor.close()
        db.close()


# ===== UPDATE BOOKING STATUS ROUTE =====
@app.route("/update-booking/<int:booking_id>/<action>", methods=["POST"])
def update_booking(booking_id, action):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get booking details
        cursor.execute(
            """
            SELECT
                b.ride_id,
                b.seats_booked,
                b.status,
                r.seats
            FROM bookings b
            JOIN rides r
                ON b.ride_id = r.id
            WHERE b.id = %s
            """,
            (booking_id,),
        )

        booking = cursor.fetchone()

        if not booking:
            return redirect(request.referrer or url_for("my_posted_rides"))

        # Prevent processing an already handled request
        if booking["status"] != "pending":
            return redirect(request.referrer or url_for("my_posted_rides"))

        if action == "confirm":

            # Check seat availability
            if booking["seats"] < booking["seats_booked"]:
                return "<script>alert('Not enough seats available.');history.back();</script>"

            # Deduct seats
            cursor.execute(
                """
                UPDATE rides
                SET seats = seats - %s
                WHERE id = %s
                """,
                (
                    booking["seats_booked"],
                    booking["ride_id"],
                ),
            )

            status = "confirmed"

        elif action == "reject":
            status = "rejected"

        else:
            return redirect(request.referrer or url_for("my_posted_rides"))

        # Update booking status
        cursor.execute(
            """
            UPDATE bookings
            SET status = %s
            WHERE id = %s
            """,
            (
                status,
                booking_id,
            ),
        )

        db.commit()

    finally:
        cursor.close()
        db.close()

    return redirect(request.referrer or url_for("my_posted_rides"))


# ===== CANCEL POSTED RIDE ROUTE =====
@app.route("/cancel-posted-ride", methods=["POST"])
def cancel_posted_ride():
    if "user_id" not in session:
        return redirect(url_for("login"))

    ride_id = request.form["ride_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Restore seats only for confirmed bookings
        cursor.execute(
            """
            SELECT seats_booked
            FROM bookings
            WHERE ride_id = %s
              AND status = %s
            """,
            (ride_id, "confirmed"),
        )

        confirmed_bookings = cursor.fetchall()

        total_seats = sum(booking["seats_booked"] for booking in confirmed_bookings)

        if total_seats > 0:
            cursor.execute(
                """
                UPDATE rides
                SET seats = seats + %s
                WHERE id = %s
                  AND driver_id = %s
                """,
                (
                    total_seats,
                    ride_id,
                    session["user_id"],
                ),
            )

        # Cancel the ride
        cursor.execute(
            """
            UPDATE rides
            SET status = %s
            WHERE id = %s
              AND driver_id = %s
            """,
            (
                "cancelled",
                ride_id,
                session["user_id"],
            ),
        )

        # Cancel all pending and confirmed bookings
        cursor.execute(
            """
            UPDATE bookings
            SET status = %s
            WHERE ride_id = %s
              AND status IN (%s, %s)
            """,
            (
                "rejected",
                ride_id,
                "pending",
                "confirmed",
            ),
        )

        db.commit()

    finally:
        cursor.close()
        db.close()

    return redirect(request.referrer or url_for("my_posted_rides"))


# ===== CANCEL BOOKING ROUTE =====
@app.route("/cancel-booking", methods=["POST"])
def cancel_booking():
    if "user_id" not in session:
        return redirect(url_for("login"))

    booking_id = request.form["booking_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                ride_id,
                seats_booked,
                status
            FROM bookings
            WHERE id = %s
              AND user_id = %s
            """,
            (
                booking_id,
                session["user_id"],
            ),
        )

        booking = cursor.fetchone()

        if not booking:
            return redirect(request.referrer or url_for("my_booked_rides"))

        # Restore seats only if the booking was confirmed
        if booking["status"] == "confirmed":
            cursor.execute(
                """
                UPDATE rides
                SET seats = seats + %s
                WHERE id = %s
                """,
                (
                    booking["seats_booked"],
                    booking["ride_id"],
                ),
            )

        # Cancel the booking
        cursor.execute(
            """
            UPDATE bookings
            SET status = %s
            WHERE id = %s
            """,
            (
                "rejected",
                booking_id,
            ),
        )

        db.commit()

    finally:
        cursor.close()
        db.close()

    return redirect(request.referrer or url_for("my_booked_rides"))


# ===== ABOUT ROUTE =====
@app.route("/about-us")
def about_us():
    return render_template("about-us.html")


# ===== PROFILE ROUTE =====
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                fname,
                lname,
                email,
                mobile,
                dob,
                role
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],),
        )

        user = cursor.fetchone()

        return render_template(
            "profile.html",
            user=user,
        )

    finally:
        cursor.close()
        db.close()


# ===== CHATBOT ROUTE =====
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({"reply": "Please enter a message."}), 400

    msg = data["message"].strip().lower()

    if "search" in msg or "find ride" in msg:
        reply = "Go to the Find Ride page, enter your pickup and destination, then click Search."

    elif "post" in msg or "offer ride" in msg:
        reply = "Click on Post Ride, fill in the ride details, and submit the form."

    elif "book" in msg:
        reply = (
            "Search for a ride, select one that matches your trip, and click Book Ride."
        )

    elif "cancel" in msg:
        reply = "Open My Rides and choose the ride or booking you want to cancel."

    elif "profile" in msg:
        reply = "Open the Profile page from the navigation bar to view your account details."

    elif "login" in msg:
        reply = "Click the Login button in the navigation bar and enter your email and password."

    elif "register" in msg or "sign up" in msg:
        reply = (
            "Click Sign Up and complete the registration form to create a new account."
        )

    elif "hi" in msg or "hello" in msg:
        reply = "Hello! Welcome to Rido. How can I help you today?"

    else:
        reply = (
            "I can help you with searching rides, posting rides, "
            "booking rides, cancelling bookings, logging in, "
            "registering, and using your profile."
        )

    return jsonify({"reply": reply})


# ===== SEND BOOKING EMAIL FUNCTION =====
def send_booking_email(to_email, user_name, ride, seats_booked):
    total_fare = ride["fare"] * seats_booked

    body = f"""
Dear {user_name},

Your ride booking request has been submitted successfully.

Booking Details
----------------------------------------
From: {ride['from_location']}
To: {ride['to_location']}
Date: {ride['ride_date'].strftime('%d %B %Y')}
Time: {ride['ride_time']}
Seats Requested: {seats_booked}
Fare per Seat: ₹{ride['fare']}
Total Fare: ₹{total_fare}
Payment Mode: Pay at Pickup
Booking Status: Pending Driver Approval
----------------------------------------

Your booking request is currently waiting for the driver's approval.

You will be notified once the driver accepts or rejects your request.

Thank you for choosing Rido.

Best regards,
Team Rido
Rido Carpooling Services
"""

    try:
        response = http_requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": os.getenv("BREVO_API_KEY"),
                "Content-Type": "application/json",
            },
            json={
                "sender": {"email": app.config["EMAIL_ADDRESS"], "name": "Rido"},
                "to": [{"email": to_email}],
                "subject": "Rido | Ride Booking Request",
                "textContent": body,
            },
            timeout=10,
        )
        if response.status_code not in (200, 201):
            print("Brevo error:", response.status_code, response.text)
    except Exception as e:
        print("Email error:", e)


# ===== APPLICATION ENTRY POINT =====
if __name__ == "__main__":
    app.run(debug=True)
