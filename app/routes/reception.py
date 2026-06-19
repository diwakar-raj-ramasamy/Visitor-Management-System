import os
import qrcode
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app
from app.models import db, Visit, VisitorRequest, Visitor, Employee, AuditLog

reception_bp = Blueprint('reception', __name__)

def generate_qr_code(visit_id, folder):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    
    verification_url = f"http://localhost:5000/pass/{visit_id}"
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qr_{visit_id}.png"
    filepath = os.path.join(folder, filename)
    img.save(filepath)
    return filename

@reception_bp.route('/reception')
def reception_dashboard():
    login_required = current_app.login_required
    roles_required = current_app.roles_required
    
    @roles_required('receptionist', 'admin')
    def get_page():
        return render_template('reception_dashboard.html')
        
    return get_page()

@reception_bp.route('/api/reception/active', methods=['GET'])
def get_active_visits():
    roles_required = current_app.roles_required
    
    @roles_required('receptionist', 'admin')
    def get_data():
        
        visits = Visit.query.filter_by(status='checked_in').all()
        
        approved_requests = VisitorRequest.query.filter_by(status='approved').all()
        
        return jsonify({
            'active_visits': [v.to_dict() for v in visits],
            'approved_requests': [r.to_dict() for r in approved_requests]
        }), 200
        
    return get_data()

@reception_bp.route('/api/reception/check-in', methods=['POST'])
def check_in():
    roles_required = current_app.roles_required
    
    @roles_required('receptionist', 'admin')
    def do_check_in():
        data = request.get_json() or {}
        req_id = data.get('request_id')
        
        if not req_id:
            return jsonify({'error': 'Request ID is required for check-in.'}), 400
            
        req = VisitorRequest.query.get(req_id)
        if not req:
            return jsonify({'error': 'Visitor request not found.'}), 404
            
        if req.status != 'approved':
            return jsonify({'error': f'Cannot check in. Request status is {req.status}. Must be approved.'}), 400
            
        
        existing_visit = Visit.query.filter_by(request_id=req.id, status='checked_in').first()
        if existing_visit:
            return jsonify({'error': 'Visitor is already checked in.', 'visit': existing_visit.to_dict()}), 400
            
        
        year = datetime.utcnow().year
        badge_number = f"VP-{year}-{req.id:04d}"
        
        
        visit = Visit(
            visitor_id=req.visitor_id,
            request_id=req.id,
            employee_id=req.employee_id,
            check_in_time=datetime.utcnow(),
            badge_number=badge_number,
            status='checked_in'
        )
        db.session.add(visit)
        db.session.flush() 
        
        
        qr_filename = generate_qr_code(visit.id, current_app.config['QRCODES_FOLDER'])
        visit.qr_code_path = qr_filename
        
        
        
        req.pass_used = True
        
        
        user_id = request.user_id
        log = AuditLog(
            user_id=user_id,
            action="Check-In",
            details=f"Visitor {req.visitor.full_name} checked in. Badge: {badge_number}.",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Check-in completed successfully.',
            'visit': visit.to_dict()
        }), 201
        
    return do_check_in()

@reception_bp.route('/api/reception/check-out', methods=['POST'])
def check_out():
    roles_required = current_app.roles_required
    
    @roles_required('receptionist', 'admin')
    def do_check_out():
        data = request.get_json() or {}
        visit_id = data.get('visit_id')
        
        if not visit_id:
            return jsonify({'error': 'Visit ID is required for check-out.'}), 400
            
        visit = Visit.query.get(visit_id)
        if not visit:
            return jsonify({'error': 'Visit record not found.'}), 404
            
        if visit.status == 'checked_out':
            return jsonify({'error': 'Visitor is already checked out.'}), 400
            
        
        visit.check_out_time = datetime.utcnow()
        visit.status = 'checked_out'
        
        
        user_id = request.user_id
        log = AuditLog(
            user_id=user_id,
            action="Check-Out",
            details=f"Visitor {visit.visitor.full_name} checked out. Badge: {visit.badge_number}.",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Check-out completed successfully.',
            'visit': visit.to_dict()
        }), 200
        
    return do_check_out()

@reception_bp.route('/verify-pass/<one_time_code>')
def verify_pass(one_time_code):
    req = VisitorRequest.query.filter_by(one_time_code=one_time_code).first_or_404()
    
    
    if req.pass_used:
        return render_template('verification_result.html', 
                               success=False, 
                               title="Access Denied: Already Used",
                               message=f"This entry pass for {req.visitor.full_name} has already been used and is invalid for further check-ins.")
                               
    
    if datetime.utcnow() > req.pass_expiry:
        return render_template('verification_result.html', 
                               success=False, 
                               title="Access Denied: Pass Expired",
                               message=f"This entry pass for {req.visitor.full_name} has expired. Entry passes are only valid for 12 hours from approval.")
                               
    
    existing_visit = Visit.query.filter_by(request_id=req.id, status='checked_in').first()
    if existing_visit:
        return render_template('verification_result.html', 
                               success=False, 
                               title="Access Denied: Already Checked In",
                               message=f"Visitor {req.visitor.full_name} is already checked in.")
                               
    
    
    year = datetime.utcnow().year
    badge_number = f"VP-{year}-{req.id:04d}"
    
    visit = Visit(
        visitor_id=req.visitor_id,
        request_id=req.id,
        employee_id=req.employee_id,
        check_in_time=datetime.utcnow(),
        badge_number=badge_number,
        status='checked_in'
    )
    db.session.add(visit)
    db.session.flush() 
    
    
    qr_filename = generate_qr_code(visit.id, current_app.config['QRCODES_FOLDER'])
    visit.qr_code_path = qr_filename
    
    
    req.pass_used = True
    
    
    log = AuditLog(
        user_id=None,
        action="QR Pass Scan Check-In",
        details=f"Visitor {req.visitor.full_name} checked in via QR pass scan. Badge: {badge_number}.",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return render_template('verification_result.html', 
                           success=True, 
                           title="Access Granted",
                           visitor_name=req.visitor.full_name,
                           host_name=req.host_employee.user.full_name,
                           department=req.host_employee.department.name,
                           badge_number=badge_number,
                           check_in_time=visit.check_in_time.strftime('%I:%M %p'))
