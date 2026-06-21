import os
import jwt
from flask import Flask, request, jsonify, redirect, url_for, make_response
from functools import wraps
from datetime import datetime, timedelta
from app.models import db, User

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    
    os.makedirs(app.config['PHOTOS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IDS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QRCODES_FOLDER'], exist_ok=True)
    
    
    import sqlalchemy
    try:
        test_engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with test_engine.connect() as conn:
            pass
        app.logger.info("Successfully connected to MySQL database!")
    except Exception as e:
        app.logger.warning(
            f"MySQL connection failed: {e}. Falling back to local SQLite database..."
        )
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['FALLBACK_DATABASE_URI']
        
    db.init_app(app)
    
    with app.app_context():
        
        db.create_all()
        
        
        try:
            import sqlalchemy
            inspector = sqlalchemy.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('visitor_requests')]
            
            if 'one_time_code' not in columns:
                with db.engine.begin() as conn:
                    conn.execute(sqlalchemy.text("ALTER TABLE visitor_requests ADD COLUMN one_time_code VARCHAR(100)"))
                    conn.execute(sqlalchemy.text("ALTER TABLE visitor_requests ADD COLUMN qr_code_path VARCHAR(255)"))
                    conn.execute(sqlalchemy.text("ALTER TABLE visitor_requests ADD COLUMN pass_expiry DATETIME"))
                    conn.execute(sqlalchemy.text("ALTER TABLE visitor_requests ADD COLUMN pass_used BOOLEAN DEFAULT 0"))
                app.logger.info("Successfully added columns for one-time code to visitor_requests table.")
                
            user_columns = [c['name'] for c in inspector.get_columns('users')]
            if 'status' not in user_columns:
                with db.engine.begin() as conn:
                    conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN status VARCHAR(50) DEFAULT 'active' NOT NULL"))
                app.logger.info("Successfully added status column to users table.")
        except Exception as e:
            app.logger.error(f"Error updating database schema: {e}")
        
    
    def generate_token(user_id, role, expiry_hours=24):
        payload = {
            'sub': user_id,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expiry_hours)
        }
        return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])
        
    def decode_token(token):
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=[app.config['JWT_ALGORITHM']])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
            
    
    app.config['generate_token'] = generate_token
    app.config['decode_token'] = decode_token
    
    
    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.cookies.get('access_token')
            
            
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
            if not token:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized. Please login.'}), 401
                return redirect(url_for('auth.login_page'))
                
            payload = decode_token(token)
            if not payload:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Session expired. Please login again.'}), 401
                resp = make_response(redirect(url_for('auth.login_page')))
                resp.delete_cookie('access_token')
                return resp
                
            from app.database.nosql_db import get_nosql_user_by_id
            user = get_nosql_user_by_id(payload['sub'])
            if not user or user.status != 'active':
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Your account has been deactivated. Please contact the Admin.'}), 403
                resp = make_response(redirect(url_for('auth.login_page')))
                resp.delete_cookie('access_token')
                return resp
                
            request.user_id = payload['sub']
            request.user_role = payload['role']
            return f(*args, **kwargs)
        return decorated
        
    def roles_required(*allowed_roles):
        def decorator(f):
            @wraps(f)
            @login_required
            def decorated(*args, **kwargs):
                if request.user_role not in allowed_roles:
                    if request.path.startswith('/api/'):
                        return jsonify({'error': 'Forbidden. Access Denied.'}), 403
                    return "Forbidden. Access Denied.", 403
                return f(*args, **kwargs)
            return decorated
        return decorator
        
    
    app.login_required = login_required
    app.roles_required = roles_required
    
    
    @app.context_processor
    def inject_user():
        token = request.cookies.get('access_token')
        if token:
            payload = decode_token(token)
            if payload:
                from app.database.nosql_db import get_nosql_user_by_id
                user = get_nosql_user_by_id(payload['sub'])
                if user:
                    return {'current_user': user}
        return {'current_user': None}
        
    
    from app.routes.auth import auth_bp
    from app.routes.visitor import visitor_bp
    from app.routes.employee import employee_bp
    from app.routes.reception import reception_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(visitor_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(reception_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    
    return app
