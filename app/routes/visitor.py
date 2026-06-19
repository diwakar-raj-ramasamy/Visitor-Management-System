import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for
from werkzeug.utils import secure_filename
from app.models import db, Visitor, VisitorRequest, Employee, User, Visit, Department

visitor_bp = Blueprint('visitor', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file.save(os.path.join(folder, unique_name))
        return unique_name
    return None

@visitor_bp.route('/visitor/dashboard')
def visitor_dashboard():
    login_required = current_app.login_required
    roles_required = current_app.roles_required
    
    @roles_required('visitor')
    def get_page():
        
        token = request.cookies.get('access_token')
        decode_token = current_app.config['decode_token']
        payload = decode_token(token)
        from app.database.nosql_db import get_nosql_user_by_id
        user = get_nosql_user_by_id(payload['sub'])
        
        
        visitor_records = Visitor.query.filter_by(email=user.email).all()
        visitor_ids = [v.id for v in visitor_records]
        
        meetings = []
        if visitor_ids:
            meetings = VisitorRequest.query.filter(VisitorRequest.visitor_id.in_(visitor_ids))\
                .order_by(VisitorRequest.created_at.desc()).all()
                
        return render_template('visitor_dashboard.html', meetings=meetings, user=user)
        
    return get_page()

@visitor_bp.route('/visitor/register')
def register_page():
    login_required = current_app.login_required
    roles_required = current_app.roles_required
    
    @roles_required('visitor', 'receptionist', 'admin')
    def get_page():
        
        employees = Employee.query.join(User).all()
        departments = Department.query.all()
        
        
        token = request.cookies.get('access_token')
        decode_token = current_app.config['decode_token']
        payload = decode_token(token)
        from app.database.nosql_db import get_nosql_user_by_id
        user = get_nosql_user_by_id(payload['sub'])
        
        return render_template('visitor_registration.html', employees=employees, departments=departments, current_user=user)
        
    return get_page()

@visitor_bp.route('/api/visitors/register', methods=['POST'])
def api_register_visitor():
    login_required = current_app.login_required
    
    @login_required
    def do_register():
        try:
            
            full_name = request.form.get('full_name')
            mobile_number = request.form.get('mobile_number')
            email = request.form.get('email')
            gender = request.form.get('gender', 'Male')
            company_name = request.form.get('company_name')
            address = request.form.get('address')
            id_type = request.form.get('id_type', 'Driver License')
            vehicle_number = request.form.get('vehicle_number')
            
            
            visitor_type = request.form.get('visitor_type', 'General')
            purpose_of_visit = request.form.get('purpose_of_visit', 'Meeting')
            host_employee_name = request.form.get('host_employee')
            visit_date_str = request.form.get('visit_date')
            visit_time_str = request.form.get('visit_time')
            
            if not full_name or not mobile_number or not email or not host_employee_name:
                return jsonify({'error': 'Name, email, mobile, and host employee are required.'}), 400
                
            
            try:
                visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date() if visit_date_str else datetime.utcnow().date()
            except ValueError:
                visit_date = datetime.utcnow().date()
                
            try:
                visit_time = datetime.strptime(visit_time_str, '%H:%M').time() if visit_time_str else datetime.utcnow().time()
            except ValueError:
                visit_time = datetime.utcnow().time()
                
            
            photo_file = request.files.get('photo')
            id_proof_file = request.files.get('id_proof')
            
            photo_name = save_uploaded_file(photo_file, current_app.config['PHOTOS_FOLDER'])
            id_proof_name = save_uploaded_file(id_proof_file, current_app.config['IDS_FOLDER'])
            
            
            
            host = Employee.query.join(User).filter(User.full_name.ilike(f"%{host_employee_name}%")).first()
            if not host:
                
                host = Employee.query.first()
                if not host:
                    return jsonify({'error': 'No host employees found in system. Setup database first.'}), 400
                    
            
            visitor = Visitor(
                full_name=full_name,
                mobile_number=mobile_number,
                email=email,
                gender=gender,
                company_name=company_name,
                address=address,
                id_type=id_type,
                id_proof_path=id_proof_name,
                photo_path=photo_name,
                vehicle_number=vehicle_number
            )
            db.session.add(visitor)
            db.session.flush() 
            
            
            req = VisitorRequest(
                visitor_id=visitor.id,
                employee_id=host.id,
                visit_date=visit_date,
                visit_time=visit_time,
                purpose_of_visit=purpose_of_visit,
                visitor_type=visitor_type,
                status='pending' 
            )
            db.session.add(req)
            db.session.commit()
            
            return jsonify({
                'message': 'Visitor registered successfully. Pending host approval.',
                'visitor_id': visitor.id,
                'request_id': req.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
            
    return do_register()

@visitor_bp.route('/pass/<int:visit_id>')
def pass_page(visit_id):
    
    visit = Visit.query.get_or_404(visit_id)
    return render_template('visitor_pass.html', visit=visit)

@visitor_bp.route('/request-pass/<int:request_id>')
def request_pass_page(request_id):
    req = VisitorRequest.query.get_or_404(request_id)
    if req.status != 'approved':
        return "This visitor request is not approved yet.", 403
    return render_template('request_pass.html', req=req)

@visitor_bp.route('/visitor/employees')
def visitor_employees():
    login_required = current_app.login_required
    roles_required = current_app.roles_required
    
    @roles_required('visitor')
    def get_page():
        
        token = request.cookies.get('access_token')
        decode_token = current_app.config['decode_token']
        payload = decode_token(token)
        from app.database.nosql_db import get_nosql_user_by_id
        user = get_nosql_user_by_id(payload['sub'])
        
        
        employees = Employee.query.join(User).all()
        return render_template('employee_directory.html', employees=employees, user=user)
        
    return get_page()

