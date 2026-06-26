from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, current_app
from app.models import db, User, AuditLog
from app.database.nosql_db import (
    get_nosql_user_by_username,
    get_nosql_user_by_email,
    nosql_db,
    sync_user_to_sql,
    write_nosql_audit_log,
    NoSQLUser
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    token = request.cookies.get('access_token')
    if token:
        decode_token = current_app.config['decode_token']
        payload = decode_token(token)
        if payload:
            role = payload.get('role')
            if role == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif role == 'receptionist':
                return redirect(url_for('reception.reception_dashboard'))
            elif role == 'employee':
                return redirect(url_for('employee.approvals_page'))
            elif role == 'host':
                return redirect(url_for('host.host_dashboard'))
            elif role == 'visitor':
                return redirect(url_for('visitor.visitor_dashboard'))
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/login')
def login_page():
    
    token = request.cookies.get('access_token')
    if token:
        decode_token = current_app.config['decode_token']
        if decode_token(token):
            return redirect(url_for('auth.index'))
    return render_template('login.html')

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role') 
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400
        
    user = get_nosql_user_by_username(username)
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials.'}), 401
        
    if role and user.role != role.lower():
        return jsonify({'error': f'Role mismatch. You are registered as {user.role.capitalize()}.'}), 403
        
    if user.status != 'active':
        return jsonify({'error': 'Your account has been deactivated. Please contact the Admin.'}), 403
        
    
    generate_token = current_app.config['generate_token']
    token = generate_token(user.id, user.role)
    
    
    write_nosql_audit_log(
        user_id=user.id,
        action="Login",
        details=f"User {user.username} successfully logged in as {user.role}.",
        ip_address=request.remote_addr
    )
    
    
    response_data = {
        'message': 'Login successful',
        'role': user.role,
        'redirect_url': url_for('auth.index')
    }
    resp = make_response(jsonify(response_data), 200)
    resp.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=False, 
        samesite='Lax',
        max_age=24 * 60 * 60 
    )
    return resp

@auth_bp.route('/signup')
def signup_page():
    
    token = request.cookies.get('access_token')
    if token:
        decode_token = current_app.config['decode_token']
        if decode_token(token):
            return redirect(url_for('auth.index'))
    return render_template('signup.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    full_name = data.get('full_name')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    
    if not full_name or not email or not username or not password:
        return jsonify({'error': 'All fields are required.'}), 400
        
    
    if get_nosql_user_by_username(username):
        return jsonify({'error': 'Username already exists.'}), 400
        
    if get_nosql_user_by_email(email):
        return jsonify({'error': 'Email address already registered.'}), 400
        
    
    from datetime import datetime
    new_user_doc = {
        'username': username,
        'role': 'visitor',
        'email': email,
        'full_name': full_name,
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    
    temp_user = NoSQLUser(new_user_doc)
    temp_user.set_password(password)
    
    
    inserted_user = nosql_db.get_collection('users').insert(temp_user._doc)
    user_id = inserted_user['id']
    
    
    sync_user_to_sql(inserted_user)
    
    
    write_nosql_audit_log(
        user_id=user_id,
        action="Visitor Account Creation",
        details=f"Visitor user {username} registered account successfully.",
        ip_address=request.remote_addr
    )
    
    return jsonify({'message': 'Account created successfully.'}), 201

@auth_bp.route('/logout')
@auth_bp.route('/api/auth/logout', methods=['GET', 'POST'])
def logout():
    
    token = request.cookies.get('access_token')
    if token:
        decode_token = current_app.config['decode_token']
        payload = decode_token(token)
        if payload:
            user_id = payload.get('sub')
            write_nosql_audit_log(
                user_id=user_id,
                action="Logout",
                details="User logged out.",
                ip_address=request.remote_addr
            )
            
    resp = make_response(redirect(url_for('auth.login_page')))
    resp.delete_cookie('access_token')
    return resp

@auth_bp.route('/profile')
def profile_page():
    login_required = current_app.login_required
    
    @login_required
    def get_page():
        from app.database.nosql_db import get_nosql_user_by_id, nosql_db
        user = get_nosql_user_by_id(request.user_id)
        if not user:
            return redirect(url_for('auth.login_page'))
            
        
        from app.models import Employee, VisitorRequest
        emp = Employee.query.filter_by(user_id=user.id).first()
        
        upcoming_visitors = []
        if emp:
            upcoming_visitors = VisitorRequest.query.filter(
                VisitorRequest.employee_id == emp.id,
                VisitorRequest.status.in_(['pending', 'approved'])
            ).order_by(VisitorRequest.visit_date.asc(), VisitorRequest.visit_time.asc()).limit(5).all()
        
        
        activities = nosql_db.get_collection('audit_logs').find({'user_id': user.id})
        
        activities = sorted(activities, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        return render_template('profile.html', user=user, emp=emp, activities=activities, upcoming_visitors=upcoming_visitors)
        
    return get_page()

@auth_bp.route('/api/profile/update', methods=['POST'])
def api_update_profile():
    login_required = current_app.login_required
    
    @login_required
    def do_update():
        data = request.get_json() or {}
        full_name = data.get('full_name')
        email = data.get('email')
        phone_number = data.get('phone_number')
        
        if not full_name or not email:
            return jsonify({'error': 'Name and Email are required.'}), 400
            
        from app.database.nosql_db import get_nosql_user_by_id, get_nosql_user_by_email, nosql_db, sync_user_to_sql, write_nosql_audit_log
        from datetime import datetime
        
        user = get_nosql_user_by_id(request.user_id)
        if not user:
            return jsonify({'error': 'User not found.'}), 404
            
        
        existing_email_user = get_nosql_user_by_email(email)
        if existing_email_user and existing_email_user.id != user.id:
            return jsonify({'error': 'Email address already in use by another account.'}), 400
            
        
        users_col = nosql_db.get_collection('users')
        users_col.update_one({'id': user.id}, {
            'full_name': full_name,
            'email': email,
            'updated_at': datetime.utcnow().isoformat()
        })
        
        
        updated_doc = users_col.find_one({'id': user.id})
        sync_user_to_sql(updated_doc)
        
        
        from app.models import db, Employee
        emp = Employee.query.filter_by(user_id=user.id).first()
        if emp:
            emp.phone_number = phone_number
            db.session.commit()
            
        
        write_nosql_audit_log(
            user_id=user.id,
            action="Profile Update",
            details="User updated personal profile details.",
            ip_address=request.remote_addr
        )
        
        return jsonify({'message': 'Profile updated successfully.'}), 200
        
    return do_update()

@auth_bp.route('/api/profile/change-password', methods=['POST'])
def api_change_password():
    login_required = current_app.login_required
    
    @login_required
    def do_change_password():
        data = request.get_json() or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required.'}), 400
            
        from app.database.nosql_db import get_nosql_user_by_id, nosql_db, sync_user_to_sql, write_nosql_audit_log
        from datetime import datetime
        
        user = get_nosql_user_by_id(request.user_id)
        if not user:
            return jsonify({'error': 'User not found.'}), 404
            
        if not user.check_password(current_password):
            return jsonify({'error': 'Incorrect current password.'}), 400
            
        
        user.set_password(new_password)
        
        
        users_col = nosql_db.get_collection('users')
        users_col.update_one({'id': user.id}, {
            'password': user.password,
            'updated_at': datetime.utcnow().isoformat()
        })
        
        
        updated_doc = users_col.find_one({'id': user.id})
        sync_user_to_sql(updated_doc)
        
        
        write_nosql_audit_log(
            user_id=user.id,
            action="Password Change",
            details="User successfully changed password.",
            ip_address=request.remote_addr
        )
        
        return jsonify({'message': 'Password updated successfully.'}), 200
        
    return do_change_password()
