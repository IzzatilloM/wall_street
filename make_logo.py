"""Wall Street uchun vaqtinchalik logo yaratadi (teal doira + oltin 'WS').
Keyin assets/images/logo.png ni o'zingizning aniq logongiz bilan almashtiring.
"""
from PIL import Image, ImageDraw, ImageFont
import os

SIZE = 1024
TEAL = (14, 92, 96, 255)       # #0E5C60
GOLD = (201, 162, 39, 255)     # oltin
GOLD2 = (230, 198, 90, 255)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Teal doira
m = 20
d.ellipse([m, m, SIZE - m, SIZE - m], fill=TEAL)

# Oltin halqa
d.ellipse([m, m, SIZE - m, SIZE - m], outline=GOLD, width=14)

# "WS" monogramm
def load_font(sz):
    for name in ["arialbd.ttf", "Arial_Bold.ttf", "ariblk.ttf", "segoeui.ttf"]:
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            continue
    return ImageFont.load_default()

font = load_font(440)
text = "WS"
bbox = d.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
x = (SIZE - tw) / 2 - bbox[0]
y = (SIZE - th) / 2 - bbox[1]
d.text((x, y), text, font=font, fill=GOLD2)

out_dirs = [
    r"C:\Users\Izzatillo\Desktop\Wall Street Mobile\assets\images",
]
for od in out_dirs:
    os.makedirs(od, exist_ok=True)
    img.save(os.path.join(od, "logo.png"))
    print("saqlandi:", os.path.join(od, "logo.png"))
