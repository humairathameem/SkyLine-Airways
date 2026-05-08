from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'flight_secret_key_2024'

# ─── DATABASE CONNECTION ──────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',        # ← change to your MySQL password
        database='flight_db'
    )

# ─── DECORATORS ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────────────────────
#  AUTH ROUTES
# ─────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard') if session['role'] == 'admin' else url_for('search_flights'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close(); db.close()

        if user:
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['role']     = user['role']
            return redirect(url_for('admin_dashboard') if user['role'] == 'admin' else url_for('search_flights'))
        flash('Invalid credentials. Try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────────────────────
#  ADMIN ROUTES
# ─────────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db = get_db(); cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS cnt FROM Flights");    flights_count  = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM Bookings");   bookings_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM Users WHERE role='user'"); users_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COALESCE(SUM(amount),0) AS total FROM Payments WHERE status='Paid'"); revenue = cursor.fetchone()['total']

    cursor.close(); db.close()
    return render_template('admin_dashboard.html',
                           flights_count=flights_count,
                           bookings_count=bookings_count,
                           users_count=users_count,
                           revenue=revenue)


# ── FLIGHTS CRUD ─────────────────────────────────────────────
@app.route('/admin/flights')
@login_required
@admin_required
def manage_flights():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.*, 
               a1.city AS source_city, a1.name AS source_name,
               a2.city AS dest_city,   a2.name AS dest_name,
               ac.model AS aircraft_model
        FROM Flights f
        JOIN Airports a1  ON f.source_airport_id      = a1.airport_id
        JOIN Airports a2  ON f.destination_airport_id = a2.airport_id
        JOIN Aircraft ac  ON f.aircraft_id            = ac.aircraft_id
        ORDER BY f.departure_time
    """)
    flights = cursor.fetchall()

    cursor.execute("SELECT * FROM Airports ORDER BY city")
    airports = cursor.fetchall()
    cursor.execute("SELECT * FROM Aircraft")
    aircraft = cursor.fetchall()

    cursor.close(); db.close()
    return render_template('manage_flights.html', flights=flights, airports=airports, aircraft=aircraft)


@app.route('/admin/flights/add', methods=['POST'])
@login_required
@admin_required
def add_flight():
    db = get_db(); cursor = db.cursor()
    cursor.execute("""
        INSERT INTO Flights (source_airport_id, destination_airport_id, departure_time, arrival_time, aircraft_id, price)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (request.form['source'], request.form['destination'],
          request.form['departure'], request.form['arrival'],
          request.form['aircraft'], request.form['price']))
    db.commit(); cursor.close(); db.close()
    flash('Flight added successfully!', 'success')
    return redirect(url_for('manage_flights'))


@app.route('/admin/flights/edit/<int:fid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_flight(fid):
    db = get_db(); cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE Flights SET source_airport_id=%s, destination_airport_id=%s,
            departure_time=%s, arrival_time=%s, aircraft_id=%s, price=%s
            WHERE flight_id=%s
        """, (request.form['source'], request.form['destination'],
              request.form['departure'], request.form['arrival'],
              request.form['aircraft'], request.form['price'], fid))
        db.commit(); cursor.close(); db.close()
        flash('Flight updated!', 'success')
        return redirect(url_for('manage_flights'))

    cursor.execute("SELECT * FROM Flights WHERE flight_id=%s", (fid,))
    flight = cursor.fetchone()
    cursor.execute("SELECT * FROM Airports ORDER BY city"); airports = cursor.fetchall()
    cursor.execute("SELECT * FROM Aircraft");               aircraft = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('edit_flight.html', flight=flight, airports=airports, aircraft=aircraft)


@app.route('/admin/flights/delete/<int:fid>')
@login_required
@admin_required
def delete_flight(fid):
    db = get_db(); cursor = db.cursor()
    cursor.execute("DELETE FROM Flights WHERE flight_id=%s", (fid,))
    db.commit(); cursor.close(); db.close()
    flash('Flight deleted.', 'info')
    return redirect(url_for('manage_flights'))


# ── AIRPORTS CRUD ────────────────────────────────────────────
@app.route('/admin/airports')
@login_required
@admin_required
def manage_airports():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Airports ORDER BY city")
    airports = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('manage_airports.html', airports=airports)


@app.route('/admin/airports/add', methods=['POST'])
@login_required
@admin_required
def add_airport():
    db = get_db(); cursor = db.cursor()
    cursor.execute("INSERT INTO Airports (name, city) VALUES (%s,%s)",
                   (request.form['name'], request.form['city']))
    db.commit(); cursor.close(); db.close()
    flash('Airport added!', 'success')
    return redirect(url_for('manage_airports'))


@app.route('/admin/airports/edit/<int:aid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_airport(aid):
    db = get_db(); cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute("UPDATE Airports SET name=%s, city=%s WHERE airport_id=%s",
                       (request.form['name'], request.form['city'], aid))
        db.commit(); cursor.close(); db.close()
        flash('Airport updated!', 'success')
        return redirect(url_for('manage_airports'))
    cursor.execute("SELECT * FROM Airports WHERE airport_id=%s", (aid,))
    airport = cursor.fetchone()
    cursor.close(); db.close()
    return render_template('edit_airport.html', airport=airport)


@app.route('/admin/airports/delete/<int:aid>')
@login_required
@admin_required
def delete_airport(aid):
    db = get_db(); cursor = db.cursor()
    cursor.execute("DELETE FROM Airports WHERE airport_id=%s", (aid,))
    db.commit(); cursor.close(); db.close()
    flash('Airport deleted.', 'info')
    return redirect(url_for('manage_airports'))


# ── AIRCRAFT CRUD ────────────────────────────────────────────
@app.route('/admin/aircraft')
@login_required
@admin_required
def manage_aircraft():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Aircraft ORDER BY model")
    aircraft = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('manage_aircraft.html', aircraft=aircraft)


@app.route('/admin/aircraft/add', methods=['POST'])
@login_required
@admin_required
def add_aircraft():
    db = get_db(); cursor = db.cursor()
    cursor.execute("INSERT INTO Aircraft (model, capacity) VALUES (%s,%s)",
                   (request.form['model'], request.form['capacity']))
    db.commit(); cursor.close(); db.close()
    flash('Aircraft added!', 'success')
    return redirect(url_for('manage_aircraft'))


@app.route('/admin/aircraft/edit/<int:acid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_aircraft(acid):
    db = get_db(); cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute("UPDATE Aircraft SET model=%s, capacity=%s WHERE aircraft_id=%s",
                       (request.form['model'], request.form['capacity'], acid))
        db.commit(); cursor.close(); db.close()
        flash('Aircraft updated!', 'success')
        return redirect(url_for('manage_aircraft'))
    cursor.execute("SELECT * FROM Aircraft WHERE aircraft_id=%s", (acid,))
    ac = cursor.fetchone()
    cursor.close(); db.close()
    return render_template('edit_aircraft.html', aircraft=ac)


@app.route('/admin/aircraft/delete/<int:acid>')
@login_required
@admin_required
def delete_aircraft(acid):
    db = get_db(); cursor = db.cursor()
    cursor.execute("DELETE FROM Aircraft WHERE aircraft_id=%s", (acid,))
    db.commit(); cursor.close(); db.close()
    flash('Aircraft deleted.', 'info')
    return redirect(url_for('manage_aircraft'))


# ── ADMIN VIEW BOOKINGS & PAYMENTS ───────────────────────────
@app.route('/admin/bookings')
@login_required
@admin_required
def view_bookings():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id, u.username, 
               a1.city AS from_city, a2.city AS to_city,
               f.departure_time, b.seats,
               COALESCE(p.amount,0) AS amount, COALESCE(p.status,'Pending') AS pay_status
        FROM Bookings b
        JOIN Users u   ON b.user_id   = u.user_id
        JOIN Flights f ON b.flight_id = f.flight_id
        JOIN Airports a1 ON f.source_airport_id      = a1.airport_id
        JOIN Airports a2 ON f.destination_airport_id = a2.airport_id
        LEFT JOIN Payments p ON b.booking_id = p.booking_id
        ORDER BY b.booking_id DESC
    """)
    bookings = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('view_bookings.html', bookings=bookings)


@app.route('/admin/payments')
@login_required
@admin_required
def view_payments():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, b.seats, u.username,
               a1.city AS from_city, a2.city AS to_city
        FROM Payments p
        JOIN Bookings b ON p.booking_id = b.booking_id
        JOIN Users u    ON b.user_id    = u.user_id
        JOIN Flights f  ON b.flight_id  = f.flight_id
        JOIN Airports a1 ON f.source_airport_id      = a1.airport_id
        JOIN Airports a2 ON f.destination_airport_id = a2.airport_id
        ORDER BY p.payment_id DESC
    """)
    payments = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('view_payments.html', payments=payments)


# ─────────────────────────────────────────────────────────────
#  USER ROUTES
# ─────────────────────────────────────────────────────────────
@app.route('/flights/search', methods=['GET', 'POST'])
@login_required
def search_flights():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Airports ORDER BY city")
    airports = cursor.fetchall()
    searched = False
    flights  = []

    if request.method == 'POST':
        searched = True
        src  = request.form.get('source', '')
        dst  = request.form.get('destination', '')
        date = request.form.get('date', '')

        # Build dynamic query — allow partial filters
        query = """
            SELECT f.*,
                   a1.city AS source_city, a1.name AS source_name,
                   a2.city AS dest_city,   a2.name AS dest_name,
                   ac.model AS aircraft_model, ac.capacity
            FROM Flights f
            JOIN Airports a1  ON f.source_airport_id      = a1.airport_id
            JOIN Airports a2  ON f.destination_airport_id = a2.airport_id
            JOIN Aircraft ac  ON f.aircraft_id            = ac.aircraft_id
            WHERE 1=1
        """
        params = []
        if src:
            query += " AND f.source_airport_id = %s"; params.append(src)
        if dst:
            query += " AND f.destination_airport_id = %s"; params.append(dst)
        if date:
            query += " AND DATE(f.departure_time) = %s"; params.append(date)
        query += " ORDER BY f.departure_time"

        cursor.execute(query, params)
        flights = cursor.fetchall()
        if not flights:
            flash('No flights found for the selected filters.', 'warning')
    else:
        # GET — show ALL upcoming flights by default
        cursor.execute("""
            SELECT f.*,
                   a1.city AS source_city, a1.name AS source_name,
                   a2.city AS dest_city,   a2.name AS dest_name,
                   ac.model AS aircraft_model, ac.capacity
            FROM Flights f
            JOIN Airports a1  ON f.source_airport_id      = a1.airport_id
            JOIN Airports a2  ON f.destination_airport_id = a2.airport_id
            JOIN Aircraft ac  ON f.aircraft_id            = ac.aircraft_id
            ORDER BY f.departure_time
        """)
        flights = cursor.fetchall()

    cursor.close(); db.close()
    return render_template('search_flights.html',
                           airports=airports, flights=flights,
                           searched=searched, now=datetime.now())


@app.route('/flights/book/<int:fid>', methods=['GET', 'POST'])
@login_required
def book_flight(fid):
    db = get_db(); cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        seats = int(request.form['seats'])
        cursor.execute("SELECT price FROM Flights WHERE flight_id=%s", (fid,))
        flight = cursor.fetchone()
        total  = flight['price'] * seats

        cursor.execute("INSERT INTO Bookings (user_id, flight_id, seats) VALUES (%s,%s,%s)",
                       (session['user_id'], fid, seats))
        db.commit()
        booking_id = cursor.lastrowid

        cursor.execute("INSERT INTO Payments (booking_id, amount, status) VALUES (%s,%s,'Pending')",
                       (booking_id, total))
        db.commit(); cursor.close(); db.close()
        flash(f'Booking confirmed! Booking ID: {booking_id}. Please complete payment.', 'success')
        return redirect(url_for('my_bookings'))

    cursor.execute("""
        SELECT f.*,
               a1.city AS source_city, a1.name AS source_name,
               a2.city AS dest_city,   a2.name AS dest_name,
               ac.model AS aircraft_model, ac.capacity
        FROM Flights f
        JOIN Airports a1 ON f.source_airport_id      = a1.airport_id
        JOIN Airports a2 ON f.destination_airport_id = a2.airport_id
        JOIN Aircraft ac ON f.aircraft_id            = ac.aircraft_id
        WHERE f.flight_id=%s
    """, (fid,))
    flight = cursor.fetchone()
    cursor.close(); db.close()
    return render_template('book_flight.html', flight=flight)


@app.route('/my-bookings')
@login_required
def my_bookings():
    db = get_db(); cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id, b.seats,
               a1.city AS from_city, a2.city AS to_city,
               f.departure_time, f.arrival_time, f.price,
               COALESCE(p.amount,0) AS amount,
               COALESCE(p.status,'Pending') AS pay_status,
               p.payment_id
        FROM Bookings b
        JOIN Flights f ON b.flight_id = f.flight_id
        JOIN Airports a1 ON f.source_airport_id      = a1.airport_id
        JOIN Airports a2 ON f.destination_airport_id = a2.airport_id
        LEFT JOIN Payments p ON b.booking_id = p.booking_id
        WHERE b.user_id=%s
        ORDER BY b.booking_id DESC
    """, (session['user_id'],))
    bookings = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/payment/pay/<int:pid>')
@login_required
def make_payment(pid):
    db = get_db(); cursor = db.cursor()
    cursor.execute("UPDATE Payments SET status='Paid' WHERE payment_id=%s", (pid,))
    db.commit(); cursor.close(); db.close()
    flash('Payment successful! Your ticket is confirmed.', 'success')
    return redirect(url_for('my_bookings'))


# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
