
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, index=True) 
    email = db.Column(db.String(150), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default='active', nullable=False)
    company_name = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    employee = db.relationship('Employee', backref='user', uselist=False, cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', backref='user')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'full_name': self.full_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    employees = db.relationship('Employee', backref='department')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description
        }

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False)
    employee_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    visitor_requests = db.relationship('VisitorRequest', backref='host_employee')
    visits = db.relationship('Visit', backref='host_employee')
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_code': self.employee_code,
            'phone_number': self.phone_number,
            'full_name': self.user.full_name if self.user else None,
            'email': self.user.email if self.user else None,
            'department': self.department.name if self.department else None,
            'department_code': self.department.code if self.department else None
        }

class Visitor(db.Model):
    __tablename__ = 'visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    gender = db.Column(db.String(20))
    company_name = db.Column(db.String(150))
    address = db.Column(db.Text)
    id_type = db.Column(db.String(50))
    id_proof_path = db.Column(db.String(255))
    photo_path = db.Column(db.String(255))
    vehicle_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    requests = db.relationship('VisitorRequest', backref='visitor', cascade="all, delete-orphan")
    visits = db.relationship('Visit', backref='visitor', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'mobile_number': self.mobile_number,
            'email': self.email,
            'gender': self.gender,
            'company_name': self.company_name,
            'address': self.address,
            'id_type': self.id_type,
            'id_proof_path': self.id_proof_path,
            'photo_path': self.photo_path,
            'vehicle_number': self.vehicle_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VisitorRequest(db.Model):
    __tablename__ = 'visitor_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitors.id', ondelete='CASCADE'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False, index=True)
    visit_time = db.Column(db.Time, nullable=False)
    purpose_of_visit = db.Column(db.String(255), nullable=False)
    visitor_type = db.Column(db.String(100), nullable=False) 
    status = db.Column(db.String(50), default='pending', index=True) 
    remarks = db.Column(db.Text)
    one_time_code = db.Column(db.String(100), unique=True, nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    pass_expiry = db.Column(db.DateTime, nullable=True)
    pass_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   
    visits = db.relationship('Visit', backref='visitor_request')
    
    def to_dict(self):
      
        time_str = self.visit_time.strftime('%H:%M:%S') if self.visit_time else None
        if hasattr(self.visit_time, 'strftime'):
            time_str = self.visit_time.strftime('%I:%M %p')
            
        return {
            'id': self.id,
            'visitor_id': self.visitor_id,
            'employee_id': self.employee_id,
            'visit_date': self.visit_date.strftime('%Y-%m-%d') if self.visit_date else None,
            'visit_time': time_str,
            'purpose_of_visit': self.purpose_of_visit,
            'visitor_type': self.visitor_type,
            'status': self.status,
            'remarks': self.remarks,
            'one_time_code': self.one_time_code,
            'qr_code_path': self.qr_code_path,
            'pass_expiry': self.pass_expiry.isoformat() if self.pass_expiry else None,
            'pass_used': self.pass_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'visitor': self.visitor.to_dict() if self.visitor else None,
            'host': self.host_employee.to_dict() if self.host_employee else None
        }

class Visit(db.Model):
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitors.id', ondelete='CASCADE'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('visitor_requests.id', ondelete='SET NULL'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=True, index=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    badge_number = db.Column(db.String(100), unique=True, nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='checked_in', index=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'visitor_id': self.visitor_id,
            'request_id': self.request_id,
            'employee_id': self.employee_id,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'badge_number': self.badge_number,
            'qr_code_path': self.qr_code_path,
            'status': self.status,
            'visitor': self.visitor.to_dict() if self.visitor else None,
            'host': self.host_employee.to_dict() if self.host_employee else None,
            'request': self.visitor_request.to_dict() if self.visitor_request else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'Guest System',
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
