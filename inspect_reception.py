import os
from bs4 import BeautifulSoup

local_file = r"c:\Users\Dell\OneDrive\Documents\VMS\app\templates\reception_dashboard.html"
stitch_file = r"C:\Users\Dell\.gemini\antigravity-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\stitch_screens\Reception_Dashboard.html"

with open(local_file, 'r', encoding='utf-8') as f:
    local_soup = BeautifulSoup(f.read(), 'html.parser')
with open(stitch_file, 'r', encoding='utf-8') as f:
    stitch_soup = BeautifulSoup(f.read(), 'html.parser')

print("--- Local Reception Dashboard ---")
for sec in local_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
    print(sec.text.strip())

print("\n--- Stitch Reception Dashboard ---")
for sec in stitch_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
    print(sec.text.strip())
