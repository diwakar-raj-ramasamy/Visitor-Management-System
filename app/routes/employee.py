import os
import secrets
import qrcode
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, current_app
from app.models import db, VisitorRequest, Employee, User, AuditLog

def generate_request_qr_code(request_id, one_time_code, folder):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    
    verification_url = f"http://localhost:5000/verify-pass/{one_time_code}"
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"req_qr_{request_id}.png"
    filepath = os.path.join(folder, filename)
    img.save(filepath)
    return filename

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/approvals')
def approvals_page():
    roles_required = current_app.roles_required
    
    @roles_required('employee', 'receptionist', 'admin')
    def get_page():
        return render_template('pending_approvals.html')
        
    return get_page()

@employee_bp.route('/api/approvals/pending', methods=['GET'])
def get_pending_requests():
    roles_required = current_app.roles_required
    
    @roles_required('employee', 'receptionist', 'admin')
    def get_data():
        user_id = request.user_id
        user_role = request.user_role
        
        
        if user_role == 'employee':
            emp = Employee.query.filter_by(user_id=user_id).first()
            if not emp:
                return jsonify({'requests': []}), 200
            requests_list = VisitorRequest.query.filter_by(employee_id=emp.id, status='pending').all()
        else:
            
            requests_list = VisitorRequest.query.filter_by(status='pending').all()
            
        return jsonify({
            'requests': [req.to_dict() for req in requests_list]
        }), 200
        
    return get_data()

@employee_bp.route('/api/approvals/action', methods=['POST'])
def approval_action():
    roles_required = current_app.roles_required
    
    @roles_required('employee', 'receptionist', 'admin')
    def do_action():
        data = request.get_json() or {}
        req_id = data.get('request_id')
        action = data.get('action') 
        remarks = data.get('remarks', '')
        
        if not req_id or not action:
            return jsonify({'error': 'Request ID and action are required.'}), 400
            
        req = VisitorRequest.query.get(req_id)
        if not req:
            return jsonify({'error': 'Request not found.'}), 404
            
        
        user_id = request.user_id
        user_role = request.user_role
        if user_role == 'employee':
            emp = Employee.query.filter_by(user_id=user_id).first()
            if not emp or req.employee_id != emp.id:
                return jsonify({'error': 'Unauthorized. You are not the host for this request.'}), 403
                
        if action == 'approve':
            req.status = 'approved'
            
            req.one_time_code = secrets.token_hex(16)
            req.pass_expiry = datetime.utcnow() + timedelta(hours=12)
            req.pass_used = False
            
            
            qr_filename = generate_request_qr_code(req.id, req.one_time_code, current_app.config['QRCODES_FOLDER'])
            req.qr_code_path = qr_filename
        elif action == 'reject':
            req.status = 'rejected'
        else:
            return jsonify({'error': 'Invalid action. Choose approve or reject.'}), 400
            
        req.remarks = remarks
        
        
        from app.database.nosql_db import get_nosql_user_by_id, write_nosql_audit_log
        user = get_nosql_user_by_id(user_id)
        write_nosql_audit_log(
            user_id=user_id,
            action=f"Request {action.capitalize()}",
            details=f"Visitor request for {req.visitor.full_name} was {action}d by {user.full_name if user else 'Unknown User'}. Remarks: {remarks}",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': f'Request has been {action}d successfully.',
            'request': req.to_dict()
        }), 200
        
    return do_action()
