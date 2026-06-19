import os
from bs4 import BeautifulSoup

local_dir = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates"
stitch_dir = r"C:\Users\Dell\.gemini\antigravity-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\stitch_screens"

mappings = {
    "login.html": ["Login_Page.html", "Login_Page_-_Desktop.html"],
    "admin_dashboard.html": ["Admin_Dashboard.html", "Admin_Dashboard_-_Desktop.html"],
    "pending_approvals.html": ["Pending_Approvals.html", "Pending_Approvals_-_Desktop.html"],
    "profile.html": ["Employee_Profile.html", "Employee_Profile_-_Desktop.html", "Visitor_Profile.html", "Visitor_Profile_-_Desktop.html", "Admin_Profile.html", "Admin_Profile_-_Desktop.html", "Receptionist_Profile.html", "Receptionist_Profile_-_Desktop.html", "Unified_User_Profile_-_Desktop.html", "Unified_User_Profile_-_Mobile.html"],
    "reception_dashboard.html": ["Reception_Dashboard.html", "Reception_Dashboard_-_Desktop.html"],
    "reports.html": ["Reports___Analytics.html", "Reports___Analytics_-_Desktop.html"],
    "visitor_pass.html": ["Digital_Visitor_Pass.html", "Digital_Visitor_Pass_-_Desktop.html"],
    "visitor_registration.html": ["Visitor_Registration.html", "Visitor_Registration_-_Desktop.html"],
    "signup.html": ["Visitor_Account_Registration.html", "Staff_Registration_-_Admin_Only.html"],
}

for local_name, stitch_names in mappings.items():
    local_path = os.path.join(local_dir, local_name)
    if not os.path.exists(local_path):
        print(f"Local file {local_name} not found!")
        continue
        
    print(f"\n=========================================\nComparing local {local_name}...")
    with open(local_path, 'r', encoding='utf-8') as f:
        local_soup = BeautifulSoup(f.read(), 'html.parser')
        
    local_inputs = [i.get('name') or i.get('id') for i in local_soup.find_all('input') if i.get('name') or i.get('id')]
    local_selects = [s.get('name') or s.get('id') for s in local_soup.find_all('select') if s.get('name') or s.get('id')]
    local_buttons = [b.text.strip() for b in local_soup.find_all('button')]
    
    print(f"Local inputs/selects: {local_inputs + local_selects}")
    
    for s_name in stitch_names:
        s_path = os.path.join(stitch_dir, s_name)
        if not os.path.exists(s_path):
            continue
            
        print(f"  vs Stitch {s_name}:")
        with open(s_path, 'r', encoding='utf-8') as f:
            s_soup = BeautifulSoup(f.read(), 'html.parser')
            
        s_inputs = [i.get('name') or i.get('id') for i in s_soup.find_all('input') if i.get('name') or i.get('id')]
        s_selects = [sel.get('name') or sel.get('id') for sel in s_soup.find_all('select') if sel.get('name') or sel.get('id')]
        s_buttons = [b.text.strip() for b in s_soup.find_all('button')]
        
        
        missing_in_local = set(s_inputs + s_selects) - set(local_inputs + local_selects)
        if missing_in_local:
            print(f"    WARNING: Missing inputs in local template: {missing_in_local}")
        else:
            print(f"    Inputs match / no missing inputs in local.")
            
        
        local_headers = [h.text.strip() for h in local_soup.find_all(['h1', 'h2', 'h3'])]
        s_headers = [h.text.strip() for h in s_soup.find_all(['h1', 'h2', 'h3'])]
        print(f"    Local headers: {local_headers[:5]}")
        print(f"    Stitch headers: {s_headers[:5]}")
