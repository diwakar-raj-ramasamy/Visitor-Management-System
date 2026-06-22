import os
import difflib

local_dir = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates"
design_dir = r"C:\Users\Dell\.host\open-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\design_screens"

mappings = {
    "login.html": "Login_Page.html",
    "admin_dashboard.html": "Admin_Dashboard.html",
    "pending_approvals.html": "Pending_Approvals.html",
    "profile.html": "Unified_User_Profile_-_Desktop.html", 
    "reception_dashboard.html": "Reception_Dashboard.html",
    "reports.html": "Reports___Analytics.html",
    "visitor_pass.html": "Digital_Visitor_Pass.html",
    "visitor_registration.html": "Visitor_Registration.html",
    "signup.html": "Visitor_Account_Registration.html",
}

for local_name, design_name in mappings.items():
    local_path = os.path.join(local_dir, local_name)
    design_path = os.path.join(design_dir, design_name)
    if not os.path.exists(local_path) or not os.path.exists(design_path):
        print(f"Skipping {local_name} or {design_name} (not found)")
        continue
        
    print(f"\n=========================================\nDiff for {local_name} vs {design_name}:")
    with open(local_path, 'r', encoding='utf-8') as f:
        local_lines = f.readlines()
    with open(design_path, 'r', encoding='utf-8') as f:
        design_lines = f.readlines()
        
    
    diff = list(difflib.unified_diff(local_lines, design_lines, fromfile=local_name, tofile=design_name, n=0))
    print(f"Total diff lines: {len(diff)}")
    if len(diff) > 0:
        
        print("Sample diffs:")
        for line in diff[:15]:
            print(line.strip())
