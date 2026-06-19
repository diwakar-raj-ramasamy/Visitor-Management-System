import os
from bs4 import BeautifulSoup

local_dir = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates"
stitch_dir = r"C:\Users\Dell\.gemini\antigravity-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\stitch_screens"

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

for local_name, stitch_name in mappings.items():
    local_path = os.path.join(local_dir, local_name)
    stitch_path = os.path.join(stitch_dir, stitch_name)
    if not os.path.exists(local_path) or not os.path.exists(stitch_path):
        continue
        
    print(f"\n=========================================\nComparing {local_name} vs {stitch_name}")
    with open(local_path, 'r', encoding='utf-8') as f:
        l_soup = BeautifulSoup(f.read(), 'html.parser')
    with open(stitch_path, 'r', encoding='utf-8') as f:
        s_soup = BeautifulSoup(f.read(), 'html.parser')
        
    
    l_texts = [t.strip() for t in l_soup.find_all(text=True) if t.strip()]
    s_texts = [t.strip() for t in s_soup.find_all(text=True) if t.strip()]
    
    
    new_in_stitch = [t for t in s_texts if t not in l_texts]
    print(f"Texts in Stitch but not in Local (count {len(new_in_stitch)}):")
    for t in new_in_stitch[:15]:
        print(f"  - {t}")
        
    
    l_inputs = [i.get('id') or i.get('name') for i in l_soup.find_all(['input', 'select', 'textarea'])]
    s_inputs = [i.get('id') or i.get('name') for i in s_soup.find_all(['input', 'select', 'textarea'])]
    l_inputs = [i for i in l_inputs if i]
    s_inputs = [i for i in s_inputs if i]
    
    missing_inputs = set(s_inputs) - set(l_inputs)
    if missing_inputs:
        print(f"Inputs in Stitch but not in Local: {missing_inputs}")
