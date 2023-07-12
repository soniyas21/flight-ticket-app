from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret_key'

def create_table():
    conn = sqlite3.connect('flight_booking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  flight_name TEXT NOT NULL,
                  timing TEXT NOT NULL,
                  starting TEXT NOT NULL,
                  destination TEXT NOT NULL,
                  price INTEGER NOT NULL,
                  available_seats INTEGER NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  age INTEGER NOT NULL,
                  phone_number TEXT NOT NULL,
                  password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  flight_id INTEGER NOT NULL,
                  num_tickets INTEGER NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (flight_id) REFERENCES flights (id))''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'soniya' and password == 'soniya@123':
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    conn = sqlite3.connect('flight_booking.db')
    c = conn.cursor()
    c.execute("SELECT * FROM flights")
    flights = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', flights=flights)

@app.route('/admin/add_flight', methods=['GET', 'POST'])
def add_flight():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    if request.method == 'POST':
        flight_name = request.form['flight_name']
        timing = request.form['timing']
        starting = request.form['starting']
        destination = request.form['destination']
        price = int(request.form['price'])
        available_seats = 60
        conn = sqlite3.connect('flight_booking.db')
        c = conn.cursor()
        c.execute("INSERT INTO flights (flight_name, timing, starting, destination, price, available_seats) "
                  "VALUES (?, ?, ?, ?, ?, ?)",
                  (flight_name, timing, starting, destination, price, available_seats))
        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')
    return render_template('add_flight.html')

@app.route('/admin/remove_flight/<int:flight_id>', methods=['POST'])
def remove_flight(flight_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    conn = sqlite3.connect('flight_booking.db')
    c = conn.cursor()
    c.execute("DELETE FROM flights WHERE id=?", (flight_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/dashboard')

@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        age = int(request.form['age'])
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('user_signup.html', error='Passwords do not match')

        conn = sqlite3.connect('flight_booking.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, age, phone_number, password) "
                  "VALUES (?, ?, ?, ?, ?)",
                  (name, email, age, phone_number, password))
        conn.commit()
        conn.close()
        return redirect('/user/login')

    return render_template('user_signup.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('flight_booking.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/user/dashboard')
        else:
            return render_template('index.html', error='Invalid email or password')

    return render_template('user_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if not session.get('user_id'):
        return redirect('/user/login')

    conn = sqlite3.connect('flight_booking.db')
    c = conn.cursor()

    c.execute("SELECT flights.flight_name, flights.timing, flights.starting, flights.destination "
              "FROM flights INNER JOIN bookings ON flights.id = bookings.flight_id "
              "WHERE bookings.user_id=?", (session['user_id'],))
    booked_flights = c.fetchall()

    conn.close()

    return render_template('user_dashboard.html', booked_flights=booked_flights)

@app.route('/user/search_flights', methods=['POST'])
def search_flights():
    if not session.get('user_id'):
        return redirect('/user/login')

    origin = request.form['origin']
    destination = request.form['destination']

    conn = sqlite3.connect('flight_booking.db')
    c = conn.cursor()

    c.execute("SELECT * FROM flights WHERE starting=? AND destination=?", (origin, destination))
    flights = c.fetchall()

    conn.close()

    if not flights:
        return render_template('user_dashboard.html', error='No flights found for the given origin and destination')

    return render_template('user_dashboard.html', flights=flights)

@app.route('/user/book_flight/<int:flight_id>', methods=['POST'])
def book_flight(flight_id):
    if not session.get('user_id'):
        return redirect('/user/login')

    num_tickets = int(request.form['num_tickets'])

    conn = sqlite3.connect('flight_booking.db')
    c = conn.cursor()

    c.execute("SELECT available_seats FROM flights WHERE id=?", (flight_id,))
    available_seats = c.fetchone()[0]

    if num_tickets > available_seats:
        conn.close()
        return redirect('/user/dashboard')

    updated_seats = available_seats - num_tickets
    c.execute("UPDATE flights SET available_seats=? WHERE id=?", (updated_seats, flight_id))
    c.execute("INSERT INTO bookings (user_id, flight_id, num_tickets) VALUES (?, ?, ?)",
              (session['user_id'], flight_id, num_tickets))

    conn.commit()
    conn.close()

    return redirect('/user/dashboard')

@app.route('/user/logout')
def user_logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    create_table()
    app.run()
