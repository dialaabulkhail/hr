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

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    employee_id = request.form.get('employee_id')
    x_studio_location = request.form.get('x_studio_location')
    x_studio_check_out_location = request.form.get('x_studio_check_out_location')
    check_in = request.form.get('check_in')

    # Authenticate the user
    url = 'http://arab-engineering-company.odoo.com'
    db = 'arab-engineering-company'
    username = 'haymouni@arab-engco.com'
    password = 'Arab@2020'

    # Connect to the Odoo XML-RPC API
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    # Convert the check_in string to a datetime object and localize it to the timezone you need
    check_in_dt = datetime.fromisoformat(check_in).replace(tzinfo=pytz.timezone('Asia/Amman'))

    # Check if the employee has already checked in today
    today = datetime.now(pytz.timezone('Asia/Amman')).strftime('%Y-%m-%d')
    attendance_ids = models.execute_kw(db, uid, password, 'hr.attendance', 'search', [[
        ('employee_id', '=', employee_id),
        ('check_in', '>=', today),
        ('check_out', '=', False)
    ]])

    if attendance_ids:
        # The employee has already checked in today, update the corresponding record with check_out and check_out_location
        attendance_id = attendance_ids[0]
        try:
            check_out_dt = datetime.now(pytz.timezone('Asia/Amman'))
            models.execute_kw(db, uid, password, 'hr.attendance', 'write', [[attendance_id], {
                'check_out': check_out_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'x_studio_check_out_location': x_studio_check_out_location
            }])
            flash('Your attendance has been submitted.')
        except Exception as e:
            flash(f"Failed to submit attendance: {e}")
    else:
        # The employee has not checked in yet today, create a new record
        try:
            attendance_id = models.execute_kw(db, uid, password, 'hr.attendance', 'create', [{
                'employee_id': employee_id,
                'check_in': check_in_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'x_studio_location': x_studio_location,
            }])
            flash('Your attendance has been submitted.')
        except Exception as e:
            flash(f"Failed to submit attendance: {e}")

    return '''
        <script>
            alert("Your attendance has been submitted.");
            window.location.replace("/dashboard");
        </script>
    '''

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()

    # Redirect to the login page
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
