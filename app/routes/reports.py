from flask import Blueprint, request, jsonify, render_template, current_app
from app.models import db, Visit, Visitor, VisitorRequest, Employee, User, Department
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def reports_page():
    login_required = current_app.login_required
    roles_required = current_app.roles_required
    
    @roles_required('admin', 'receptionist')
    def get_page():
        return render_template('reports.html')
        
    return get_page()

@reports_bp.route('/api/reports/data', methods=['GET'])
def get_reports_data():
    roles_required = current_app.roles_required
    
    @roles_required('admin', 'receptionist')
    def get_data():
        
        search = request.args.get('search', '')
        start_date_str = request.args.get('start_date', '')
        end_date_str = request.args.get('end_date', '')
        department_name = request.args.get('department', 'All Departments')
        visitor_type = request.args.get('visitor_type', 'All Visitors')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_by = request.args.get('sort_by', 'check_in_time')
        sort_dir = request.args.get('sort_dir', 'desc')
        
        
        query = Visit.query.join(Visitor).join(Employee).join(User)
        
        
        if search:
            query = query.filter(
                (Visitor.full_name.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%")) |
                (Visitor.company_name.ilike(f"%{search}%")) |
                (Visit.badge_number.ilike(f"%{search}%"))
            )
            
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                query = query.filter(Visit.check_in_time >= start_date)
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Visit.check_in_time < end_date)
            except ValueError:
                pass
                
        
        if department_name and department_name != 'All Departments':
            query = query.join(Department, Employee.department_id == Department.id).filter(Department.name.ilike(department_name))
            
        
        if visitor_type and visitor_type != 'All Visitors':
            query = query.join(VisitorRequest, Visit.request_id == VisitorRequest.id).filter(VisitorRequest.visitor_type.ilike(visitor_type))
            
        
        sort_col = Visit.check_in_time
        if sort_by == 'visitor_name':
            sort_col = Visitor.full_name
        elif sort_by == 'host_name':
            sort_col = User.full_name
        elif sort_by == 'badge_number':
            sort_col = Visit.badge_number
        elif sort_by == 'status':
            sort_col = Visit.status
            
        if sort_dir == 'asc':
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
            
        
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        visits = pagination.items
        
        return jsonify({
            'visits': [v.to_dict() for v in visits],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }), 200
        
    return get_data()
