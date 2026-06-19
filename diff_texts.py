import os
from bs4 import BeautifulSoup
import difflib

local_dir = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates"
stitch_dir = r"C:\Users\Dell\.gemini\antigravity-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\stitch_screens"

files = [
    ("login.html", "Login_Page.html"),
    ("signup.html", "Visitor_Account_Registration.html"),
    ("visitor_registration.html", "Visitor_Registration.html"),
    ("admin_dashboard.html", "Admin_Dashboard.html"),
]

for local_name, stitch_name in files:
    local_path = os.path.join(local_dir, local_name)
    stitch_path = os.path.join(stitch_dir, stitch_name)
    
    with open(local_path, 'r', encoding='utf-8') as f:
        l_soup = BeautifulSoup(f.read(), 'html.parser')
    with open(stitch_path, 'r', encoding='utf-8') as f:
        s_soup = BeautifulSoup(f.read(), 'html.parser')
        
    l_text = "\n".join([t.strip() for t in l_soup.find_all(text=True) if t.strip() and not t.strip().startswith('{')])
    s_text = "\n".join([t.strip() for t in s_soup.find_all(text=True) if t.strip() and not t.strip().startswith('{')])
    
    print(f"\n=========================================\nText diff for {local_name} vs {stitch_name}")
    diff = list(difflib.unified_diff(l_text.splitlines(), s_text.splitlines(), n=2))
    for line in diff[:30]:
        print(line)
