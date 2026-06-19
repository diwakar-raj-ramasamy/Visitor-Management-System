import os
from bs4 import BeautifulSoup

local_file = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates\visitor_registration.html"
stitch_file = r"C:\Users\Dell\.gemini\antigravity-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\stitch_screens\Visitor_Registration.html"

def inspect(filepath, label):
    print(f"\n--- {label} ---")
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    for tag in soup.find_all(['input', 'select', 'textarea']):
        print(f"<{tag.name} id='{tag.get('id')}' name='{tag.get('name')}' type='{tag.get('type')}' placeholder='{tag.get('placeholder')}' value='{tag.get('value')}' />")

inspect(local_file, "Local Visitor Registration")
inspect(stitch_file, "Stitch Visitor Registration")
