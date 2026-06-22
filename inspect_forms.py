import os
from bs4 import BeautifulSoup

local_file = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates\visitor_registration.html"
design_file = r"C:\Users\Dell\.host\open-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\design_screens\Visitor_Registration.html"

def inspect(filepath, label):
    print(f"\n--- {label} ---")
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    for tag in soup.find_all(['input', 'select', 'textarea']):
        print(f"<{tag.name} id='{tag.get('id')}' name='{tag.get('name')}' type='{tag.get('type')}' placeholder='{tag.get('placeholder')}' value='{tag.get('value')}' />")

inspect(local_file, "Local Visitor Registration")
inspect(design_file, "Design Visitor Registration")
