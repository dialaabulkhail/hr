import xmlrpc.client

import werkzeug
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = '12837812793871293'


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        url = 'http://arab-engineering-company.odoo.com'
        db = 'arab-engineering-company'

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})

        if uid:
            # Authenticate the user
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
            user_id = models.execute_kw(db, uid, password, 'res.users', 'search', [[('login', '=', username)]])
            user = models.execute_kw(db, uid, password, 'res.users', 'read', [user_id], {'fields': ['name', 'email']})

            # Get employee's position and work email
            employee_id = models.execute_kw(db, uid, password, 'hr.employee', 'search', [[('user_id', '=', user_id)]])
            employee = models.execute_kw(db, uid, password, 'hr.employee', 'read', [employee_id],
                                         {'fields': ['id', 'job_id', 'work_email']})

            # Store the user's name in the session
            session['name'] = user[0]['name']
            session['user_id'] = user_id

            # Redirect to the dashboard page
            return redirect(url_for('dashboard'))
        else:
            # Show an error message
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'name' not in session:
        return redirect(url_for('login'))

    # Get user information from Odoo
    url = 'http://arab-engineering-company.odoo.com'
    db = 'arab-engineering-company'
    username = 'haymouni@arab-engco.com'
    password = 'Arab@2020'

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    user_id = session['user_id']
    user = models.execute_kw(db, uid, password, 'res.users', 'read', [user_id], {'fields': ['name', 'email']})

    # Get employee's position and work email
    employee_id = models.execute_kw(db, uid, password, 'hr.employee', 'search', [[('user_id', '=', user_id)]])
    employee = models.execute_kw(db, uid, password, 'hr.employee', 'read', [employee_id],
                                 {'fields': ['id', 'job_id', 'work_email']})

    return render_template('dashboard.html', name=user[0]['name'], position=employee[0]['job_id'][1],
                           work_email=employee[0]['work_email'], employee_id=employee[0]['id'])


@app.route('/submit_attendance', methods=['GET', 'POST'])
def attendance():
    url = "http://arab-engineering-company.odoo.com"
    db = "arab-engineering-company"
    username = "haymouni@arab-engco.com"
    password = "Arab@2020"

    attendance_model = "hr.attendance"
    employee_model = "hr.employee"

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    if request.method == 'POST':
        # Get form data
        employee_id = request.form['employee_id']
        check_in_str = request.form['datetime']
        location = request.form['location']

        # Check if employee exists
        employee = models.execute_kw(db, uid, password, employee_model, 'search_read', [[['id', '=', employee_id]]])
        if not employee:
            return "Employee not found"

        # Create attendance record
        check_in = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%H:%M')
        attendance = {
            'employee_id': employee_id,
            'check_in': check_in.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime object to string in the expected format
            'x_studio_location': location,
        }
        attendance_id = models.execute_kw(db, uid, password, attendance_model, 'create', [attendance])

        return f"Attendance recorded for employee {employee[0]['name']}"

    return render_template('attendance_form.html')


@app.route('/checkout/<int:attendance_id>', methods=['POST'])
def checkout(attendance_id):
    # Get attendance record
    attendance = models.execute_kw(db, uid, password, attendance_model, 'search_read', [[['id', '=', attendance_id]]])
    if not attendance:
        return "Attendance record not found"
    attendance = attendance[0]

    # Update attendance record with check-out and location
    check_out_str = request.form['datetime']
    location = request.form['location']
    check_out = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%H:%M')

    update = {
        'check_out': check_out.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime object to string in the expected format
        'x_studio_check_out_location': location,
    }
    models.execute_kw(db, uid, password, attendance_model, 'write', [[attendance_id], update])

    return "Attendance updated with check-out time and location"

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()

    # Redirect to the login page
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
