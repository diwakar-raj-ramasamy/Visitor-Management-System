from app import create_app
from app.models import db, User, Department, Employee
import os

app = create_app()

def seed_database():
    with app.app_context():
        
        from app.database.nosql_db import nosql_db, NoSQLUser, sync_user_to_sql
        users_col = nosql_db.get_collection('users')
        
        if User.query.first() is not None or users_col.find_one({'username': 'admin'}) is not None:
            
            if not users_col.find():
                print("Seeding NoSQL from existing SQL users...")
                sql_users = User.query.all()
                for u in sql_users:
                    users_col.insert({
                        'id': u.id,
                        'username': u.username,
                        'password': u.password,
                        'role': u.role,
                        'email': u.email,
                        'full_name': u.full_name,
                        'status': u.status if hasattr(u, 'status') else 'active',
                        'created_at': u.created_at.isoformat() if u.created_at else None,
                        'updated_at': u.updated_at.isoformat() if u.updated_at else None
                    })
            print("Database already seeded. Skipping...")
            return
            
        print("Seeding NoSQL and SQL databases with default departments, users, and employees...")
        
        
        depts = [
            Department(name="Engineering", code="ENG", description="Software, Hardware, and Infrastructure teams"),
            Department(name="HR & Legal", code="HRL", description="Human Resources and Legal Compliance"),
            Department(name="Operations", code="OPS", description="Office Management and Security Operations")
        ]
        db.session.add_all(depts)
        db.session.flush() 
        
        
        from datetime import datetime
        
        admin_doc = {
            'username': "admin",
            'role': "admin",
            'email': "admin@kinetic-corp.com",
            'full_name': "Priya Dharshini",
            'status': "active",
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        admin_nosql = NoSQLUser(admin_doc)
        admin_nosql.set_password("admin123")
        inserted_admin = users_col.insert(admin_nosql._doc)
        
        receptionist_doc = {
            'username': "receptionist",
            'role': "receptionist",
            'email': "reception@kinetic-corp.com",
            'full_name': "Dark",
            'status': "active",
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        receptionist_nosql = NoSQLUser(receptionist_doc)
        receptionist_nosql.set_password("receptionist123")
        inserted_receptionist = users_col.insert(receptionist_nosql._doc)
        
        employee_doc = {
            'username': "employee",
            'role': "employee",
            'email': "employee@kinetic-corp.com",
            'full_name': "Warrior",
            'status': "active",
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        employee_nosql = NoSQLUser(employee_doc)
        employee_nosql.set_password("employee123")
        inserted_employee = users_col.insert(employee_nosql._doc)
        
        
        sync_user_to_sql(inserted_admin)
        sync_user_to_sql(inserted_receptionist)
        sync_user_to_sql(inserted_employee)
        
        
        emp_record = Employee(
            user_id=inserted_employee['id'],
            department_id=depts[0].id, 
            employee_code="EMP-2026-0042",
            phone_number="+1 (555) 456-7890"
        )
        db.session.add(emp_record)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    
    seed_database()
    
    
    app.run(host='0.0.0.0', port=5000, debug=True)
