import base64
import os
import sys
import io

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'])
    from PIL import Image, ImageDraw, ImageFont

artifact_dir = r"c:\Users\MTN\.gemini\antigravity\brain\63350aa0-7607-4e03-b472-066bc63f9d0e"
b64_path = r"c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\base64_logo.txt"

with open(b64_path, 'r') as f:
    b64_str = f.read().strip()

if b64_str.startswith('data:image'):
    b64_str = b64_str.split(',', 1)[1]

img_data = base64.b64decode(b64_str)
img = Image.open(io.BytesIO(img_data)).convert("RGBA")

logo_size = 100
img = img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

canvas = Image.new('RGB', (800, 100), (255, 255, 255))
canvas.paste(img.convert('RGB'), (0, 0))

draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 55)
except:
    try:
        font = ImageFont.truetype("arialbd.ttf", 55)
    except:
        font = ImageFont.load_default()

text = "Optiflow Aqua Systems"
draw.text((120, 15), text, fill="#0066cc", font=font)

out_path = os.path.join(artifact_dir, "Optiflow_App_Logo.png")
canvas.save(out_path)
print("Saved to", out_path)