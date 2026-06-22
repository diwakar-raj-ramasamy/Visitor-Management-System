import os
from bs4 import BeautifulSoup

local_file = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates\visitor_pass.html"
design_file = r"C:\Users\Dell\.host\open-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\design_screens\Digital_Visitor_Pass.html"

with open(local_file, 'r', encoding='utf-8') as f:
    local_soup = BeautifulSoup(f.read(), 'html.parser')
with open(design_file, 'r', encoding='utf-8') as f:
    design_soup = BeautifulSoup(f.read(), 'html.parser')

print("--- Local Visitor Pass ---")
for sec in local_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
    print(sec.text.strip())

print("\n--- Design Visitor Pass ---")
for sec in design_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
    print(sec.text.strip())
