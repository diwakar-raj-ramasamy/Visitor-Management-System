import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vms-super-secret-key-123456!')
    
    
    
    mysql_user = os.environ.get('DB_USER', 'root')
    mysql_password = os.environ.get('DB_PASSWORD', '')
    mysql_host = os.environ.get('DB_HOST', 'localhost')
    mysql_db = os.environ.get('DB_NAME', 'vms_db')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
    )
    
    FALLBACK_DATABASE_URI = f"sqlite:///{os.environ.get('SQLITE_DB_PATH', os.path.join(BASE_DIR, 'vms_local.db'))}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'vms-jwt-secret-key-987654!')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRY_HOURS = 24
    
    
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'app', 'static', 'uploads'))
    PHOTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'photos')
    IDS_FOLDER = os.path.join(UPLOAD_FOLDER, 'ids')
    QRCODES_FOLDER = os.path.join(UPLOAD_FOLDER, 'qrcodes')
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 
