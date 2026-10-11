"""Draw the Omi Buses app icon (a friendly bus) at the sizes iOS and Android want."""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")


def icon(size):
    s = 1024
    im = Image.new("RGB", (s, s), "#0b4f8a")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((150, 200, 874, 780), 90, fill="#ffc72c")                 # body
    d.rounded_rectangle((215, 270, 809, 520), 40, fill="#cfe8ff")                 # windscreen
    d.rectangle((505, 270, 519, 520), fill="#ffc72c")                             # window split
    d.rectangle((150, 600, 874, 630), fill="#e0a800")                             # trim
    for x in (250, 774):                                                          # headlights
        d.ellipse((x - 45, 650, x + 45, 740), fill="#fffbe6")
    d.rounded_rectangle((420, 660, 604, 720), 20, fill="#111")                    # grille
    for x in (300, 724):                                                          # wheels
        d.rounded_rectangle((x - 70, 760, x + 70, 870), 30, fill="#111")
    d.rectangle((120, 380, 150, 470), fill="#111"); d.rectangle((874, 380, 904, 470), fill="#111")  # mirrors
    return im.resize((size, size), Image.LANCZOS)


for n in (180, 192, 512):
    icon(n).save(os.path.join(OUT, f"icon-{n}.png"))
print("icons written")
