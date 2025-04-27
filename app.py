from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import os
import uuid


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["college_portal"]
users_collection = db["users"]
faculty_collection = db["faculty_logins"]

@app.route('/')
def home():
    return render_template('index.html')

# Student Registration Route
@app.route('/s-register.html', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not name or not email or not password:
            flash("All fields are required!", "error")
        elif users_collection.find_one({'email': email}):
            flash("Email is already registered!", "error")
        else:
            users_collection.insert_one({
                'name': name,
                'email': email,
                'password': password,
                'role': 'student',
                'clg': '',
                'clgid': '',
                'branch': '',
                'contact': '',
                'address': '',
                'photo_url': ''
            })
            flash("Student registered successfully! Please login.", "success")
            return redirect(url_for('student_login'))

    return render_template('s-register.html')

# Faculty Registration Route
@app.route('/f-register.html', methods=['GET', 'POST'])
def faculty_register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not name or not email or not password:
            flash("All fields are required!", "error")
        elif users_collection.find_one({'email': email}):
            flash("Email is already registered!", "error")
        else:
            users_collection.insert_one({
                'name': name,
                'email': email,
                'password': password,
                'role': 'faculty',
                'department': '',
                'contact': '',
                'photo_url': ''
            })
            flash("Faculty registered successfully! Please login.", "success")
            return redirect(url_for('faculty_login'))

    return render_template('f-register.html')

# Student Login Route
@app.route('/s-login.html', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        user = users_collection.find_one({'email': email})

        if user and user['password'] == password and user.get('role') == 'student':
            session['user'] = user['name']
            session['email'] = email
            session['role'] = 'student'
            return redirect(url_for('termscond'))
        
        else:
            flash("Invalid student email or password!", "error")

    return render_template('s-login.html')

# Faculty Login Route
@app.route('/f-login.html', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        user = users_collection.find_one({'email': email})

        if user and user['password'] == password and user.get('role') == 'faculty':
            session['user'] = user['name']
            session['email'] = email
            session['role'] = 'faculty'
            return redirect(url_for('termscond'))
        else:
            flash("Invalid faculty email or password!", "error")

    return render_template('f-login.html')

# Terms & Conditions Route
@app.route('/termscond.html', methods=['GET', 'POST'])
def termscond():
    if request.method == 'POST':
        user_role = session.get('role')
        if user_role == 'student':
            return redirect(url_for('s_editprofile'))
        elif user_role == 'faculty':
            return redirect(url_for('f_editprofile'))
    return render_template("termscond.html")

# Student Profile Edit Route
@app.route('/s-editprofile.html', methods=['GET', 'POST'])
def s_editprofile():
    if 'email' not in session:
        flash("Please login first.", "error")
        return redirect(url_for('student_login'))  # adjust route name if needed

    email = session['email']
    user = users_collection.find_one({'email': email})

    if request.method == 'POST':
        # Handle photo upload
        photo = request.files.get('photo')
        photo_url = user.get('photo_url', '')  # keep the old photo URL if no new photo is uploaded

        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            upload_folder = os.path.join('static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, filename)
            photo.save(upload_path)
            photo_url = '/' + upload_path.replace("\\", "/")  # for Windows compatibility

        # Update user details in MongoDB
        users_collection.update_one({'email': email}, {'$set': {
            'name': request.form.get('name'),
            'clg': request.form.get('clg'),
            'clgid': request.form.get('clgid'),
            'branch': request.form.get('branch'),
            'contact': request.form.get('contact'),
            'address': request.form.get('address'),
            'photo_url': photo_url  # Save the updated photo URL
        }})

        flash("Profile updated successfully.", "success")
        return redirect(url_for('s_dashboard'))

    return render_template('s-editprofile.html', user=user)
# Faculty Profile Edit Route
@app.route('/f-editprofile.html', methods=['GET', 'POST'])
def f_editprofile():
    if 'email' not in session:
        flash("Please login first.", "error")
        return redirect(url_for('faculty_login'))  # adjust route name if needed

    email = session['email']
    faculty = faculty_collection.find_one({'email': email})  # Assuming 'faculty_collection' for faculty data

    if request.method == 'POST':
        # Handle photo upload
        photo = request.files.get('photo')
        photo_url = faculty.get('photo_url', '')  # Keep old photo if no new one uploaded

        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"  # Ensure unique filenames
            upload_folder = os.path.join('static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, unique_filename)
            photo.save(upload_path)
            photo_url = '/' + upload_path.replace("\\", "/")  # Windows compatibility

        # Update faculty details in MongoDB
        faculty_collection.update_one({'email': email}, {'$set': {
            'name': request.form.get('name'),
            'department': request.form.get('department'),
            'faculty_id': request.form.get('faculty_id'),
            'contact': request.form.get('contact'),
            'address': request.form.get('address'),
            'photo_url': photo_url
        }})

        flash("Profile updated successfully.", "success")
        return redirect(url_for('f_dashboard'))  # Faculty dashboard route

    return render_template('f-editprofile.html', faculty=faculty)

# Student Dashboard Route
@app.route('/s-dashboard.html')
def s_dashboard():
    if 'email' not in session:
        flash("Please login first.", "error")
        return redirect(url_for('student_login'))

    user = users_collection.find_one({'email': session['email']})
    return render_template("s-dashboard.html", user=user)

# Faculty Dashboard Route
@app.route('/f-dashboard.html')
def f_dashboard():
    if 'email' not in session:
        flash("Please login first.", "error")
        return redirect(url_for('faculty_login'))

    faculty = users_collection.find_one({'email': session['email']})
    return render_template("f-dashboard.html", faculty=faculty)

# Student Attendance Route
@app.route('/s-attendence.html')
def s_attendance():
    return render_template("s-attendence.html")

# Faculty Attendance Route
@app.route('/f-attendance.html')
def f_attendance():
    return render_template("f-attendance.html")

# Student Alerts Route
@app.route('/s-alerts.html')
def s_alerts():
    return render_template("s-alerts.html")

# Other routes for different pages (you can add them as needed)
@app.route('/s-safezones.html')
def s_safezones():
    return render_template("s-safezones.html")
@app.route('/f-safezones.html')
def f_safezone():
    return render_template('f-safezones.html')

@app.route('/f-smoke.html')
def f_smoke():
    return render_template('f-smoke.html')
@app.route('/s-smoke.html')
def s_smoke():
    return render_template('s-smoke.html')
@app.route('/f-acknowledge.html')
def f_acknowledge():
    return render_template('f-acknowledge.html')
@app.route('/s-acknowledge.html')
def s_acknowledge():
    return render_template('s-acknowledge.html')

@app.route('/f-alerts.html')
def f_alerts():
    return render_template("f-alerts.html")

@app.route('/s-booking.html')
def s_booking():
    return render_template('s-booking.html')

@app.route('/f-booking.html')
def f_booking():
    return render_template('f-booking.html')

@app.route('/energy.html')
def f_energy():
    return render_template('energy.html')

@app.route('/edit-fee-structure.html')
def edit_fee_structure():
    return render_template('edit-fee-structure.html')

@app.route('/s-bhostel.html')
def s_bhostel():
    return render_template("s-bhostel.html")

@app.route('/student_profile.html')
def student_profile():
    return render_template("student_profile.html")

@app.route('/boys_hostel_fee_structure.html')
def boys_hostel_fee_structure():
    return render_template("boys_hostel_fee_structure.html")

@app.route('/f-bhostel.html')
def f_bhostel():
    return render_template("f-bhostel.html")

@app.route('/s-ghostel.html')
def s_ghostel():
    return render_template("s-ghostel.html")

@app.route('/f-ghostel.html')
def f_ghostel():
    return render_template("f-ghostel.html")

@app.route('/s-tranportation.html')
def s_transportation():
    return render_template("s-tranportation.html")

@app.route('/f-transportation.html')
def f_transportation():
    return render_template("f-transportation.html")

@app.route('/s-dashboardsettings.html')
def s_dashboardsettings():
    return render_template("s-dashboardsettings.html")


@app.route('/f-dashboardsettings.html')
def f_dashboardsettings():
    return render_template("f-dashboardsettings.html")


@app.route('/f-notification.html')
def f_notification():
    return render_template("f-notification.html")
@app.route('/s-notifications.html')
def s_notifications():
    return render_template("s-notifications.html")

@app.route('/usermanual.html')
def usermanual():
    return render_template("usermanual.html")

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('student_login'))

if __name__ == '__main__':
    app.run(debug=True)
