import json
import urllib.request
import ssl
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

output_txt_path = r"C:\Users\Dell\.host\open-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\.system_generated\steps\17\output.txt"
dest_dir = r"C:\Users\Dell\.host\open-ide\brain\ea09bf43-8a2c-4ff0-b238-b6244f8558a5\scratch\design_screens"
os.makedirs(dest_dir, exist_ok=True)

with open(output_txt_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

screens = data.get('screens', [])
print(f"Found {len(screens)} screens. Downloading...")

for screen in screens:
    title = screen.get('title', 'untitled')
    url = screen.get('htmlCode', {}).get('downloadUrl')
    if not url:
        print(f"Skipping {title}: no HTML download URL")
        continue
    
    
    safe_title = "".join([c if c.isalnum() or c in "._- " else "_" for c in title])
    safe_title = safe_title.replace(" ", "_")
    filename = f"{safe_title}.html"
    filepath = os.path.join(dest_dir, filename)
    
    print(f"Downloading {title} to {filename}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            with open(filepath, 'w', encoding='utf-8') as out_f:
                out_f.write(html)
    except Exception as e:
        print(f"Failed to download {title}: {e}")

print("Done downloading all screens.")
