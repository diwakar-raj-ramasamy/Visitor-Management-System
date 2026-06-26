import os
import json
import uuid
import threading
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class NoSQLDocumentDatabase:
    """
    A lightweight, thread-safe, local JSON-based NoSQL document database.
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.lock = threading.Lock()
        self._data = {}
        self._load_db()

    def _load_db(self):
        with self.lock:
            
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            if not os.path.exists(self.filepath):
                self._data = {}
                self._save_db_unlocked()
            else:
                try:
                    with open(self.filepath, 'r') as f:
                        self._data = json.load(f)
                except Exception:
                    
                    self._data = {}
                    self._save_db_unlocked()

    def _save_db_unlocked(self):
        
        temp_filepath = f"{self.filepath}.tmp"
        try:
            with open(temp_filepath, 'w') as f:
                json.dump(self._data, f, indent=4, default=str)
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
            os.rename(temp_filepath, self.filepath)
        except Exception as e:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception:
                    pass
            raise e

    def get_collection(self, name):
        return NoSQLCollection(self, name)

class NoSQLCollection:
    """
    Represents a collection of documents within the NoSQL database.
    """
    def __init__(self, db, name):
        self.db = db
        self.name = name

    def _get_collection_data(self):
        if self.name not in self.db._data:
            self.db._data[self.name] = []
        return self.db._data[self.name]

    def _get_next_id(self):
        data = self._get_collection_data()
        if not data:
            return 1
        ids = [doc.get('id') for doc in data if isinstance(doc.get('id'), int)]
        return max(ids) + 1 if ids else 1

    def insert(self, document):
        with self.db.lock:
            data = self._get_collection_data()
            doc_copy = document.copy()
            
            
            if 'id' not in doc_copy or doc_copy['id'] is None:
                doc_copy['id'] = self._get_next_id()
                
            
            if '_id' not in doc_copy:
                doc_copy['_id'] = str(uuid.uuid4())
                
            
            for k, v in list(doc_copy.items()):
                if isinstance(v, datetime):
                    doc_copy[k] = v.isoformat()
            
            data.append(doc_copy)
            self.db._save_db_unlocked()
            return doc_copy

    def find_one(self, query):
        with self.db.lock:
            data = self._get_collection_data()
            for doc in data:
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    return doc.copy()
            return None

    def find(self, query=None):
        with self.db.lock:
            data = self._get_collection_data()
            if query is None or not query:
                return [doc.copy() for doc in data]
            results = []
            for doc in data:
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    results.append(doc.copy())
            return results

    def update_one(self, query, update_fields):
        with self.db.lock:
            data = self._get_collection_data()
            for doc in data:
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    for k, v in update_fields.items():
                        if isinstance(v, datetime):
                            doc[k] = v.isoformat()
                        else:
                            doc[k] = v
                    self.db._save_db_unlocked()
                    return doc.copy()
            return None

    def delete_one(self, query):
        with self.db.lock:
            data = self._get_collection_data()
            for i, doc in enumerate(data):
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    removed = data.pop(i)
                    self.db._save_db_unlocked()
                    return removed.copy()
            return None


class NoSQLUser:
    """
    A model wrapper that wraps a NoSQL user document and mimics the Flask-SQLAlchemy User model API.
    """
    def __init__(self, doc):
        if not doc:
            raise ValueError("Cannot initialize NoSQLUser with empty document.")
        self._doc = doc
        self.id = doc.get('id')
        self.username = doc.get('username')
        self.password = doc.get('password')
        self.role = doc.get('role')
        self.email = doc.get('email')
        self.full_name = doc.get('full_name')
        self.status = doc.get('status', 'active')
        
        
        created_at_val = doc.get('created_at')
        if isinstance(created_at_val, str):
            try:
                self.created_at = datetime.fromisoformat(created_at_val)
            except ValueError:
                self.created_at = datetime.utcnow()
        else:
            self.created_at = created_at_val or datetime.utcnow()
            
        updated_at_val = doc.get('updated_at')
        if isinstance(updated_at_val, str):
            try:
                self.updated_at = datetime.fromisoformat(updated_at_val)
            except ValueError:
                self.updated_at = datetime.utcnow()
        else:
            self.updated_at = updated_at_val or datetime.utcnow()

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)
        self._doc['password'] = self.password

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'full_name': self.full_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at
        }



db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'vms_nosql.json'))
nosql_db = NoSQLDocumentDatabase(db_path)


def get_nosql_user_by_id(user_id):
    """Retrieves a user by id and returns a NoSQLUser instance or None."""
    if user_id is None:
        return None
    try:
        user_id = int(user_id)
    except ValueError:
        return None
    doc = nosql_db.get_collection('users').find_one({'id': user_id})
    return NoSQLUser(doc) if doc else None


def get_nosql_user_by_username(username):
    """Retrieves a user by username and returns a NoSQLUser instance or None."""
    if not username:
        return None
    doc = nosql_db.get_collection('users').find_one({'username': username})
    return NoSQLUser(doc) if doc else None


def get_nosql_user_by_email(email):
    """Retrieves a user by email and returns a NoSQLUser instance or None."""
    if not email:
        return None
    doc = nosql_db.get_collection('users').find_one({'email': email})
    return NoSQLUser(doc) if doc else None


def sync_user_to_sql(user_doc_or_obj):
    """
    Synchronizes a user record to the SQL database User model.
    This maintains database consistency for existing SQL queries and joins.
    """
    from app.models import db, User
    
    if isinstance(user_doc_or_obj, NoSQLUser):
        doc = user_doc_or_obj._doc
    else:
        doc = user_doc_or_obj
        
    try:
        sql_user = User.query.get(doc['id'])
        if not sql_user:
            sql_user = User(
                id=doc['id'],
                username=doc['username'],
                password=doc['password'],
                role=doc['role'],
                email=doc['email'],
                full_name=doc['full_name'],
                status=doc.get('status', 'active'),
                company_name=doc.get('company_name')
            )
            db.session.add(sql_user)
        else:
            sql_user.username = doc['username']
            sql_user.password = doc['password']
            sql_user.role = doc['role']
            sql_user.email = doc['email']
            sql_user.full_name = doc['full_name']
            sql_user.status = doc.get('status', 'active')
            sql_user.company_name = doc.get('company_name')
            
        
        created_at_val = doc.get('created_at')
        if isinstance(created_at_val, str):
            try:
                sql_user.created_at = datetime.fromisoformat(created_at_val)
            except ValueError:
                pass
                
        db.session.commit()
    except Exception as e:
        
        db.session.rollback()
        print(f"Error synchronizing NoSQL user to SQL: {e}")


def write_nosql_audit_log(user_id, action, details, ip_address):
    """Writes an audit log to the NoSQL database and syncs it to the SQL database."""
    log_doc = {
        'user_id': user_id,
        'action': action,
        'details': details,
        'ip_address': ip_address,
        'created_at': datetime.utcnow().isoformat()
    }
    inserted_log = nosql_db.get_collection('audit_logs').insert(log_doc)
    
    
    from app.models import db, AuditLog
    try:
        sql_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.session.add(sql_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error synchronizing NoSQL audit log to SQL: {e}")
