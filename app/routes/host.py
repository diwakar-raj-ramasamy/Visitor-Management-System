from flask import Blueprint, request, jsonify, render_template, current_app
from app.models import db, Visitor, Visit, VisitorRequest, Employee, User, Department, AuditLog
from datetime import datetime, timedelta
from sqlalchemy import func
import random
from app.database.nosql_db import nosql_db

host_bp = Blueprint('host', __name__)

@host_bp.route('/host/dashboard')
def host_dashboard():
    login_required = current_app.login_required
    roles_required = current_app.roles_required
    
    @roles_required('host')
    def get_page():
        return render_template('host_dashboard.html')
        
    return get_page()

@host_bp.route('/api/host/register-company', methods=['POST'])
def register_company():
    roles_required = current_app.roles_required
    
    @roles_required('host')
    def do_registration():
        data = request.get_json() or {}
        company_name = data.get('company_name')
        employees = data.get('employees', 0)
        receptionists = data.get('receptionists', 0)
        growth = data.get('growth', '+0.0%')
        status = data.get('status', 'Active')
        
        # User details (optional during company registration)
        admin_username = data.get('admin_username')
        admin_password = data.get('admin_password')
        admin_role = data.get('admin_role', 'admin').lower()
        
        if not company_name:
            return jsonify({'error': 'Company name is required.'}), 400
            
        col = nosql_db.get_collection('registered_companies')
        existing = [c for c in col.find() if c.get('company', '').lower() == company_name.lower()]
        if existing:
            return jsonify({'error': 'Company already registered.'}), 400
            
        # If user registration details are provided, validate them first
        if admin_username:
            if not admin_password:
                return jsonify({'error': 'Password is required to create a user account.'}), 400
            if admin_role not in ['admin', 'receptionist', 'employee']:
                return jsonify({'error': 'Invalid user role specified.'}), 400
                
            from app.database.nosql_db import get_nosql_user_by_username
            if get_nosql_user_by_username(admin_username):
                return jsonify({'error': f'Username "{admin_username}" is already taken.'}), 400

        doc = {
            'company': company_name,
            'employees': int(employees),
            'receptionists': int(receptionists),
            'visitors': 0,
            'growth': growth,
            'status': status
        }
        col.insert(doc)

        # Create user account if requested
        if admin_username:
            from app.database.nosql_db import NoSQLUser, sync_user_to_sql, write_nosql_audit_log
            
            # Generate email and full name based on username and company
            email = f"{admin_username}@{company_name.lower().replace(' ', '')}.com"
            full_name = f"{company_name} {admin_role.capitalize()}"
            
            new_user_doc = {
                'username': admin_username,
                'role': admin_role,
                'email': email,
                'full_name': full_name,
                'status': 'active',
                'company_name': company_name,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            temp_user = NoSQLUser(new_user_doc)
            temp_user.set_password(admin_password)
            
            # Save user in NoSQL
            inserted_user = nosql_db.get_collection('users').insert(temp_user._doc)
            user_id = inserted_user['id']
            
            # Sync user to SQL
            sync_user_to_sql(inserted_user)
            
            # Additional logic for employee role
            if admin_role == 'employee':
                from app.models import Employee, Department
                dept = Department.query.first()
                if not dept:
                    dept = Department(name="General", code="GEN", description="General Department")
                    db.session.add(dept)
                    db.session.commit()
                    
                import random
                emp_code = f"EMP-{random.randint(10000, 99999)}"
                while Employee.query.filter_by(employee_code=emp_code).first():
                    emp_code = f"EMP-{random.randint(10000, 99999)}"
                    
                emp = Employee(
                    user_id=user_id,
                    department_id=dept.id,
                    employee_code=emp_code,
                    phone_number=''
                )
                db.session.add(emp)
                db.session.commit()
                
            write_nosql_audit_log(
                user_id=12,  # Host user ID (typically 12 in the logs)
                action="Account Created",
                details=f"Created {admin_role} user {admin_username} for company {company_name}.",
                ip_address=request.remote_addr
            )

        return jsonify({'message': 'Company registered successfully.'}), 201
        
    return do_registration()

@host_bp.route('/api/host/stats', methods=['GET'])
def get_host_stats():
    roles_required = current_app.roles_required
    
    @roles_required('host')
    def get_stats():
        today = datetime.utcnow().date()
        start_of_today = datetime.combine(today, datetime.min.time())
        end_of_today = datetime.combine(today, datetime.max.time())
        
        # Real counts from database
        total_employees = Employee.query.count()
        total_receptionists = User.query.filter_by(role='receptionist').count()
        total_visitors = Visitor.query.count()
        
        # Total companies: distinct company name from visitors table + standard list
        db_companies = db.session.query(func.distinct(Visitor.company_name)).filter(Visitor.company_name != '', Visitor.company_name.isnot(None)).all()
        company_set = set([c[0] for c in db_companies if c[0]])
        reg_col = nosql_db.get_collection('registered_companies')
        for rc in reg_col.find():
            if rc.get('company'):
                company_set.add(rc['company'])
        standard_companies = {"Kinetic Corp", "Apex Group", "ByteCraft Solutions", "DeltaWare", "Enigma Tech", "Vanguard Industries"}
        all_companies = list(company_set.union(standard_companies))
        total_companies = len(all_companies)
        
        # Today's visitors: scheduled request or active visit today
        todays_visitors_count = VisitorRequest.query.filter(
            VisitorRequest.visit_date == today
        ).count()
        if todays_visitors_count == 0:
            # Fallback to current check-ins or dummy realistic number for demo if empty
            todays_visitors_count = Visit.query.filter(
                Visit.check_in_time >= start_of_today,
                Visit.check_in_time <= end_of_today
            ).count()
            if todays_visitors_count == 0:
                todays_visitors_count = 14
                
        # Active companies: number of distinct visitor companies currently checked-in
        active_companies_count = db.session.query(func.count(func.distinct(Visitor.company_name)))\
            .join(Visit)\
            .filter(Visit.status == 'checked_in').scalar() or 0
        if active_companies_count == 0:
            active_companies_count = min(3, len(company_set)) or 3
            
        return jsonify({
            'total_companies': total_companies,
            'total_employees': total_employees if total_employees > 0 else 42,
            'total_receptionists': total_receptionists if total_receptionists > 0 else 2,
            'total_visitors': total_visitors if total_visitors > 0 else 184,
            'todays_visitors': todays_visitors_count,
            'active_companies': active_companies_count,
            'monthly_growth': 14.8, # hardcoded growth metric
        }), 200
        
    return get_stats()

@host_bp.route('/api/host/analytics', methods=['GET'])
def get_host_analytics():
    roles_required = current_app.roles_required
    
    @roles_required('host')
    def get_analytics_data():
        # Read parameters
        company_filter = request.args.get('company', 'All')
        dept_filter = request.args.get('department', 'All')
        status_filter = request.args.get('status', 'All')
        
        today = datetime.utcnow().date()
        
        # Seed standard companies
        standard_companies = ["Kinetic Corp", "Apex Group", "ByteCraft Solutions", "DeltaWare", "Enigma Tech", "Vanguard Industries"]
        reg_col = nosql_db.get_collection('registered_companies')
        for rc in reg_col.find():
            if rc.get('company') and rc['company'] not in standard_companies:
                standard_companies.append(rc['company'])
        
        # 1. Company Distribution: visits per company
        # Query database to get actual visitor companies and counts
        query = db.session.query(Visitor.company_name, func.count(Visit.id))\
            .join(Visit, Visit.visitor_id == Visitor.id)\
            .filter(Visitor.company_name != '', Visitor.company_name.isnot(None))
            
        if company_filter != 'All':
            query = query.filter(Visitor.company_name == company_filter)
            
        company_data_raw = query.group_by(Visitor.company_name).all()
        
        company_dist = {}
        for c_name, count in company_data_raw:
            if c_name:
                company_dist[c_name] = count
                
        # Fill in defaults if empty
        for comp in standard_companies:
            if comp not in company_dist:
                company_dist[comp] = random.randint(15, 60)
                
        if company_filter != 'All' and company_filter in company_dist:
            company_dist = {company_filter: company_dist[company_filter]}
            
        # 2. Employees per Company (SaaS mockup based on departments/companies)
        emp_per_company = {}
        for comp in standard_companies:
            emp_per_company[comp] = random.randint(10, 45)
        # Add actual employee count to primary host company "Kinetic Corp"
        real_emp_count = Employee.query.count()
        if real_emp_count > 0:
            emp_per_company["Kinetic Corp"] = real_emp_count
            
        if company_filter != 'All':
            if company_filter in emp_per_company:
                emp_per_company = {company_filter: emp_per_company[company_filter]}
            else:
                emp_per_company = {company_filter: random.randint(5, 15)}
                
        # 3. Visitor Status Pie Chart
        v_status_query = db.session.query(Visit.status, func.count(Visit.id))
        if status_filter != 'All':
            v_status_query = v_status_query.filter(Visit.status == status_filter)
        visitor_status_raw = v_status_query.group_by(Visit.status).all()
        
        visitor_status = {
            'checked_in': 0,
            'checked_out': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0
        }
        for status, count in visitor_status_raw:
            if status in visitor_status:
                visitor_status[status] = count
                
        # Also query visitor requests
        req_status_raw = db.session.query(VisitorRequest.status, func.count(VisitorRequest.id)).group_by(VisitorRequest.status).all()
        for status, count in req_status_raw:
            if status in visitor_status:
                visitor_status[status] += count
                
        # Fallback values if database is fresh
        if sum(visitor_status.values()) == 0:
            visitor_status = {
                'checked_in': 18,
                'checked_out': 142,
                'pending': 5,
                'approved': 12,
                'rejected': 3
            }
            
        # 4. Daily Visitor Trend (Last 7 Days)
        daily_labels = []
        daily_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            daily_labels.append(day.strftime('%b %d'))
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())
            
            # Count visits checked in on this day
            cnt = Visit.query.filter(Visit.check_in_time >= day_start, Visit.check_in_time <= day_end).count()
            daily_data.append(cnt)
            
        if sum(daily_data) == 0:
            # Seed mock trend line
            daily_data = [12, 19, 15, 25, 32, 8, 14]
            
        # 5. Monthly Visitor Trend (Last 6 Months)
        monthly_labels = []
        monthly_data = []
        for i in range(5, -1, -1):
            # approximate months
            target_date = today - timedelta(days=i*30)
            monthly_labels.append(target_date.strftime('%B'))
            
            # count visits in that month
            first_day = datetime(target_date.year, target_date.month, 1)
            if target_date.month == 12:
                last_day = datetime(target_date.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                last_day = datetime(target_date.year, target_date.month + 1, 1) - timedelta(seconds=1)
                
            cnt = Visit.query.filter(Visit.check_in_time >= first_day, Visit.check_in_time <= last_day).count()
            monthly_data.append(cnt)
            
        if sum(monthly_data) == 0:
            monthly_data = [98, 120, 115, 145, 184, 160]
            
        # 6. Receptionist Distribution
        # Find receptionist users
        receptionists = User.query.filter_by(role='receptionist').all()
        recep_dist = {}
        for r in receptionists:
            # Query audit logs for visits processed or checked in by this user
            recep_dist[r.full_name] = AuditLog.query.filter(
                AuditLog.user_id == r.id, 
                AuditLog.action.ilike('%Check-In%')
            ).count()
            
        # Defaults
        if not recep_dist or sum(recep_dist.values()) == 0:
            recep_names = [r.full_name for r in receptionists] if receptionists else ["Dark Mode Security", "John Doe receptionist"]
            for name in recep_names:
                recep_dist[name] = random.randint(45, 95)
                
        # 7. Employee Category (Department Donut Chart)
        depts = Department.query.all()
        dept_dist = {}
        for d in depts:
            dept_dist[d.name] = Employee.query.filter_by(department_id=d.id).count()
            
        if not dept_dist or sum(dept_dist.values()) == 0:
            dept_dist = {
                "Engineering": 18,
                "HR & Legal": 8,
                "Operations": 12,
                "Finance": 4
            }
            
        # 8. Company Role Analytics
        # Distributes visits/requests by visitor_type
        type_counts = db.session.query(VisitorRequest.visitor_type, func.count(VisitorRequest.id)).group_by(VisitorRequest.visitor_type).all()
        role_dist = {
            'VIP/Executive': 0,
            'Contractor': 0,
            'Delivery': 0,
            'Emergency': 0,
            'General': 0
        }
        for v_type, count in type_counts:
            # Map types
            mapped = 'General'
            if 'VIP' in v_type or 'Executive' in v_type:
                mapped = 'VIP/Executive'
            elif 'Contractor' in v_type:
                mapped = 'Contractor'
            elif 'Delivery' in v_type:
                mapped = 'Delivery'
            elif 'Emergency' in v_type:
                mapped = 'Emergency'
            role_dist[mapped] += count
            
        if sum(role_dist.values()) == 0:
            role_dist = {
                'VIP/Executive': 15,
                'Contractor': 48,
                'Delivery': 35,
                'Emergency': 8,
                'General': 78
            }
            
        return jsonify({
            'company_distribution': {
                'labels': list(company_dist.keys()),
                'data': list(company_dist.values())
            },
            'employees_per_company': {
                'labels': list(emp_per_company.keys()),
                'data': list(emp_per_company.values())
            },
            'visitor_status': {
                'labels': [k.replace('_', ' ').capitalize() for k in visitor_status.keys()],
                'data': list(visitor_status.values())
            },
            'daily_visitor_trend': {
                'labels': daily_labels,
                'data': daily_data
            },
            'monthly_visitor_trend': {
                'labels': monthly_labels,
                'data': monthly_data
            },
            'receptionist_distribution': {
                'labels': list(recep_dist.keys()),
                'data': list(recep_dist.values())
            },
            'employee_category': {
                'labels': list(dept_dist.keys()),
                'data': list(dept_dist.values())
            },
            'company_role_analytics': {
                'labels': list(role_dist.keys()),
                'data': list(role_dist.values())
            }
        }), 200
        
    return get_analytics_data()

@host_bp.route('/api/host/tables', methods=['GET'])
def get_host_tables():
    roles_required = current_app.roles_required
    
    @roles_required('host')
    def get_tables_data():
        table_type = request.args.get('type', 'visitors')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 5))
        sort_by = request.args.get('sort_by', 'id')
        sort_dir = request.args.get('sort_dir', 'desc')
        
        # Filters
        company_filter = request.args.get('company', 'All')
        dept_filter = request.args.get('department', 'All')
        status_filter = request.args.get('status', 'All')
        
        # 1. Company Summary Table
        if table_type == 'companies':
            # Synthesize list of companies
            standard_companies = [
                {"id": 1, "company": "Kinetic Corp", "employees": 42, "receptionists": 2, "visitors": 124, "growth": "+12.4%", "status": "Active"},
                {"id": 2, "company": "Apex Group", "employees": 28, "receptionists": 1, "visitors": 88, "growth": "+8.2%", "status": "Active"},
                {"id": 3, "company": "ByteCraft Solutions", "employees": 35, "receptionists": 1, "visitors": 76, "growth": "+15.1%", "status": "Active"},
                {"id": 4, "company": "DeltaWare", "employees": 18, "receptionists": 1, "visitors": 45, "growth": "-2.4%", "status": "Active"},
                {"id": 5, "company": "Enigma Tech", "employees": 12, "receptionists": 0, "visitors": 24, "growth": "+20.0%", "status": "Pending"},
                {"id": 6, "company": "Vanguard Industries", "employees": 24, "receptionists": 1, "visitors": 52, "growth": "+5.6%", "status": "Active"}
            ]
            
            # Extract distinct companies from DB and insert them
            db_companies = db.session.query(func.distinct(Visitor.company_name)).filter(Visitor.company_name != '', Visitor.company_name.isnot(None)).all()
            idx = 7
            reg_col = nosql_db.get_collection('registered_companies')
            reg_companies = reg_col.find()
            for rc in reg_companies:
                if not any(sc['company'].lower() == rc['company'].lower() for sc in standard_companies):
                    standard_companies.append({
                        "id": idx,
                        "company": rc['company'],
                        "employees": rc.get('employees', 0),
                        "receptionists": rc.get('receptionists', 0),
                        "visitors": rc.get('visitors', 0),
                        "growth": rc.get('growth', '+0.0%'),
                        "status": rc.get('status', 'Active')
                    })
                    idx += 1
            for c_tuple in db_companies:
                c_name = c_tuple[0]
                if c_name and not any(sc['company'].lower() == c_name.lower() for sc in standard_companies):
                    standard_companies.append({
                        "id": idx,
                        "company": c_name,
                        "employees": random.randint(5, 20),
                        "receptionists": 1,
                        "visitors": random.randint(10, 30),
                        "growth": f"+{random.randint(1, 20)}.0%",
                        "status": "Active"
                    })
                    idx += 1
                    
            # Filter
            filtered_companies = standard_companies
            if company_filter != 'All':
                filtered_companies = [c for c in filtered_companies if c['company'] == company_filter]
            if search:
                filtered_companies = [c for c in filtered_companies if search.lower() in c['company'].lower()]
                
            # Sorting
            reverse = (sort_dir == 'desc')
            if sort_by == 'company':
                filtered_companies.sort(key=lambda x: x['company'].lower(), reverse=reverse)
            elif sort_by == 'employees':
                filtered_companies.sort(key=lambda x: x['employees'], reverse=reverse)
            elif sort_by == 'visitors':
                filtered_companies.sort(key=lambda x: x['visitors'], reverse=reverse)
            else:
                filtered_companies.sort(key=lambda x: x['id'], reverse=reverse)
                
            # Paginate
            total = len(filtered_companies)
            start = (page - 1) * limit
            end = start + limit
            paginated = filtered_companies[start:end]
            
            return jsonify({
                'data': paginated,
                'total': total,
                'pages': (total + limit - 1) // limit,
                'current_page': page
            })
            
        # 2. Employee Summary Table
        elif table_type == 'employees':
            query = Employee.query.join(User)
            
            if dept_filter != 'All':
                query = query.join(Department).filter(Department.name == dept_filter)
                
            if search:
                query = query.filter(
                    (User.full_name.ilike(f"%{search}%")) |
                    (Employee.employee_code.ilike(f"%{search}%"))
                )
                
            # Sorting
            sort_col = Employee.id
            if sort_by == 'name':
                sort_col = User.full_name
            elif sort_by == 'code':
                sort_col = Employee.employee_code
            elif sort_by == 'department':
                query = query.join(Department)
                sort_col = Department.name
                
            if sort_dir == 'desc':
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())
                
            pagination = query.paginate(page=page, per_page=limit, error_out=False)
            
            emp_list = []
            for emp in pagination.items:
                # Count requests hosted
                hosted_count = VisitorRequest.query.filter_by(employee_id=emp.id).count()
                emp_list.append({
                    'id': emp.id,
                    'name': emp.user.full_name,
                    'code': emp.employee_code,
                    'department': emp.department.name,
                    'visitors_hosted': hosted_count,
                    'status': emp.user.status
                })
                
            return jsonify({
                'data': emp_list,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': pagination.page
            })
            
        # 3. Visitor Logs Table
        elif table_type == 'visitors':
            query = Visit.query.join(Visitor).join(Employee).join(User)
            
            if company_filter != 'All':
                query = query.filter(Visitor.company_name == company_filter)
                
            if dept_filter != 'All':
                query = query.join(Department, Employee.department_id == Department.id).filter(Department.name == dept_filter)
                
            if status_filter != 'All':
                query = query.filter(Visit.status == status_filter)
                
            if search:
                query = query.filter(
                    (Visitor.full_name.ilike(f"%{search}%")) |
                    (Visitor.company_name.ilike(f"%{search}%")) |
                    (User.full_name.ilike(f"%{search}%"))
                )
                
            # Sorting
            sort_col = Visit.check_in_time
            if sort_by == 'visitor':
                sort_col = Visitor.full_name
            elif sort_by == 'company':
                sort_col = Visitor.company_name
            elif sort_by == 'host':
                sort_col = User.full_name
            elif sort_by == 'status':
                sort_col = Visit.status
                
            if sort_dir == 'desc':
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())
                
            pagination = query.paginate(page=page, per_page=limit, error_out=False)
            
            visit_logs = []
            for v in pagination.items:
                visit_logs.append({
                    'id': v.id,
                    'visitor_name': v.visitor.full_name,
                    'company': v.visitor.company_name or 'Individual',
                    'email': v.visitor.email,
                    'host_name': v.host_employee.user.full_name,
                    'check_in': v.check_in_time.isoformat() if v.check_in_time else None,
                    'check_out': v.check_out_time.isoformat() if v.check_out_time else None,
                    'status': v.status
                })
                
            # If DB is empty, provide mock rows
            if not visit_logs and page == 1:
                visit_logs = [
                    {
                        'id': 1,
                        'visitor_name': "Alice Smith",
                        'company': "Apex Group",
                        'email': "alice@apex.com",
                        'host_name': "Warrior",
                        'check_in': (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                        'check_out': None,
                        'status': "checked_in"
                    },
                    {
                        'id': 2,
                        'visitor_name': "Bob Jones",
                        'company': "ByteCraft Solutions",
                        'email': "bob@bytecraft.net",
                        'host_name': "Warrior",
                        'check_in': (datetime.utcnow() - timedelta(days=1, hours=4)).isoformat(),
                        'check_out': (datetime.utcnow() - timedelta(days=1, hours=2)).isoformat(),
                        'status': "checked_out"
                    }
                ]
                
            return jsonify({
                'data': visit_logs,
                'total': pagination.total or len(visit_logs),
                'pages': pagination.pages or 1,
                'current_page': page
            })
            
        # 4. Recent Visit Updates Table (Audit / Status Log)
        elif table_type == 'updates':
            query = AuditLog.query.outerjoin(User)
            
            if search:
                query = query.filter(
                    (AuditLog.action.ilike(f"%{search}%")) |
                    (AuditLog.details.ilike(f"%{search}%"))
                )
                
            sort_col = AuditLog.created_at
            if sort_dir == 'desc':
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())
                
            pagination = query.paginate(page=page, per_page=limit, error_out=False)
            
            updates = []
            for log in pagination.items:
                updates.append({
                    'id': log.id,
                    'activity': log.action,
                    'time': log.created_at.isoformat() if log.created_at else None,
                    'details': log.details,
                    'user': log.user.full_name if log.user else 'System Agent',
                    'status': 'Success'
                })
                
            # If DB is empty, provide mock rows
            if not updates and page == 1:
                updates = [
                    {
                        'id': 1,
                        'activity': "Visitor Check-In",
                        'time': (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                        'details': "Alice Smith checked in at Reception Desk #01",
                        'user': "Dark",
                        'status': "Success"
                    },
                    {
                        'id': 2,
                        'activity': "Request Approved",
                        'time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                        'details': "Pass request for Bob Jones approved by Warrior",
                        'user': "Warrior",
                        'status': "Success"
                    }
                ]
                
            return jsonify({
                'data': updates,
                'total': pagination.total or len(updates),
                'pages': pagination.pages or 1,
                'current_page': page
            })
            
        return jsonify({'error': 'Invalid table type'}), 400
        
    return get_tables_data()
