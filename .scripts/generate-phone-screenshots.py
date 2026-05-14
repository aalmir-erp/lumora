#!/usr/bin/env python3
"""Generate 5 polished 1080×1920 phone screenshots for the Play Store.

Each screenshot shows a key Servia feature in mobile-first layout.
Output: web/brand/play-assets/phone/ss-01.png … ss-05.png

Usage:
    python3 .scripts/generate-phone-screenshots.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT   = Path(__file__).resolve().parent.parent
BRAND  = ROOT / "web" / "brand"
OUT    = BRAND / "play-assets" / "phone"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920

# Brand palette
TEAL      = (15,  118, 110)
TEAL_MID  = (20,  184, 166)
TEAL_LT   = (153, 246, 228)
NAVY      = (15,  23,  42)
YELLOW    = (251, 191, 36)
WHITE     = (255, 255, 255)
GREY_BG   = (248, 250, 252)
GREY_CARD = (241, 245, 249)
GREY_TEXT = (100, 116, 139)
DARK_TEXT = (15,  23,  42)
GREEN_OK  = (5,   150, 105)
RED_WARN  = (239, 68,  68)

# Fonts
def F(size, bold=False):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try: return ImageFont.truetype(p, size)
    except: return ImageFont.load_default()

def Fe(size):
    """Emoji-capable font."""
    try: return ImageFont.truetype("/usr/share/fonts/opentype/unifont/unifont_upper.otf", size)
    except: return F(size)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def vgrad(img, top, bot):
    d = ImageDraw.Draw(img)
    for y in range(img.height):
        t = y / img.height
        r = int(top[0] + (bot[0]-top[0])*t)
        g = int(top[1] + (bot[1]-top[1])*t)
        b = int(top[2] + (bot[2]-top[2])*t)
        d.line([(0,y),(img.width,y)], fill=(r,g,b))

def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def status_bar(d, y=0):
    """Draw a phone status bar (time + icons)."""
    d.rectangle([(0,y),(W,y+56)], fill=TEAL)
    d.text((40, y+14), "9:41", font=F(28, True), fill=WHITE)
    d.text((W-50, y+14), "●●●", font=F(18), fill=WHITE)

def nav_bar(d, y):
    """Bottom nav: Home · Book · Chat · Account."""
    d.rectangle([(0,y),(W,y+110)], fill=WHITE)
    d.line([(0,y),(W,y)], fill=(226,232,240), width=1)
    items = [("⌂","Home",200), ("📅","Book",420), ("💬","Chat",660), ("👤","Account",880)]
    for icon, label, x in items:
        d.text((x, y+10), icon, font=Fe(36), fill=GREY_TEXT, anchor="mt")
        d.text((x, y+60), label, font=F(22), fill=GREY_TEXT, anchor="mt")

def header(d, title, subtitle=None):
    d.rectangle([(0,56),(W,180)], fill=TEAL)
    d.text((W//2, 105), title, font=F(44, True), fill=WHITE, anchor="mm")
    if subtitle:
        d.text((W//2, 148), subtitle, font=F(26), fill=TEAL_LT, anchor="mm")

def chip(d, x, y, w, h, text, bg=TEAL, fg=WHITE, r=12, bold=False):
    rr(d, [x,y,x+w,y+h], r, fill=bg)
    d.text((x+w//2, y+h//2), text, font=F(24, bold), fill=fg, anchor="mm")

def card(d, x, y, w, h, r=20, fill=WHITE, outline=(226,232,240), ow=1):
    rr(d, [x,y,x+w,y+h], r, fill=fill, outline=outline, width=ow)

def mascot_ball(bg, size=200, pos=(W//2, 400)):
    try:
        m = Image.open(BRAND / "servia-icon-1024x1024.png").convert("RGBA")
        m = m.resize((size, size), Image.LANCZOS)
        bg.paste(m, (pos[0]-size//2, pos[1]-size//2), m)
    except:
        pass

def save(img, name):
    img.convert("RGB").save(OUT / name, optimize=True, quality=92)
    print(f"  ✓ {OUT/name}  ({(OUT/name).stat().st_size//1024} KB)")


# ===========================================================================
# Screenshot 1 — Home / Services grid
# ===========================================================================
def make_home():
    img = Image.new("RGB", (W, H), GREY_BG)
    vgrad(img, TEAL, TEAL_MID)
    d = ImageDraw.Draw(img)
    status_bar(d)

    # Hero section
    d.rectangle([(0,56),(W,520)], fill=TEAL)
    mascot_ball(img, size=180, pos=(W//2, 270))
    d.text((W//2, 390), "Servia", font=F(72, True), fill=WHITE, anchor="mm")
    d.text((W//2, 450), "UAE Home Services", font=F(30), fill=TEAL_LT, anchor="mm")
    d.text((W//2, 495), "Book in 60 seconds", font=F(24), fill=YELLOW, anchor="mm")

    # Services grid
    img_bg = Image.new("RGB", (W, H-520), GREY_BG)
    d2 = ImageDraw.Draw(img)
    # Draw white rounded rect area
    d2.rectangle([(0,510),(W,H-110)], fill=GREY_BG)

    services = [
        ("🧹", "Deep Cleaning",    "from AED 290",  TEAL),
        ("🔧", "Plumber & AC",     "24/7 booking",  (37,99,235)),
        ("🐛", "Pest Control",     "from AED 199",  (124,58,237)),
        ("🔌", "Electrician",      "60-min arrival",(234,88,12)),
        ("🚿", "Bathroom Fix",     "from AED 149",  (5,150,105)),
        ("📦", "Moving Help",      "same-day book", (190,18,60)),
    ]
    cw, ch = 460, 170
    for i, (icon, name, price, col) in enumerate(services):
        row, col_n = i // 2, i % 2
        x = 40 + col_n * (cw + 60)
        y = 560 + row * (ch + 24)
        card(d2, x, y, cw, ch, r=18, fill=WHITE)
        # colour accent left bar
        d2.rounded_rectangle([x,y,x+8,y+ch], radius=4, fill=col)
        d2.text((x+36, y+ch//2-14), icon, font=Fe(48), fill=col, anchor="lm")
        d2.text((x+110, y+40), name, font=F(26, True), fill=DARK_TEXT)
        d2.text((x+110, y+82), price, font=F(22), fill=GREY_TEXT)
        chip(d2, x+110, y+ch-50, 150, 36, "Book →", bg=col, r=18)

    nav_bar(d, H-110)
    save(img, "ss-01-home.png")


# ===========================================================================
# Screenshot 2 — Chat with bot (instant quote)
# ===========================================================================
def make_chat():
    img = Image.new("RGB", (W, H), GREY_BG)
    d = ImageDraw.Draw(img)
    status_bar(d)
    header(d, "Servia AI Assistant", "Book any service instantly")

    # Chat bubbles
    msgs = [
        ("right", "Hi! I need a deep clean for my 2BR flat in JVC.",
         None, TEAL, WHITE),
        ("left",  "Great choice! 2BR deep clean in JVC — AED 290.\nIncludes kitchen, bathrooms,\nall rooms. When works for you?",
         "🤖 Servia Bot", (226,232,240), DARK_TEXT),
        ("right", "Tomorrow at 10am please.",
         None, TEAL, WHITE),
        ("left",  "✅ Tomorrow, 10:00 AM confirmed.\nTeam of 2, ~3 hours.\n\nShall I send your payment link?",
         "🤖 Servia Bot", (226,232,240), DARK_TEXT),
        ("right", "Yes please!",
         None, TEAL, WHITE),
        ("left",  "💳 Payment link sent!\nQ-284810 · AED 290\nTap to pay securely.",
         "🤖 Servia Bot", (226,232,240), DARK_TEXT),
    ]

    y = 210
    for side, text, sender, bg, fg in msgs:
        lines = text.split("\n")
        max_w = max(d.textlength(l, font=F(24)) for l in lines) + 60
        bw = min(int(max_w), 760)
        bh = len(lines)*36 + 40 + (28 if sender else 0)
        x = (W - 60 - bw) if side == "right" else 60
        rr(d, [x,y,x+bw,y+bh], 20,
           fill=bg,
           outline=(TEAL if side=="right" else (203,213,225)),
           width=1)
        ty = y + 14
        if sender:
            d.text((x+20, ty), sender, font=F(20, True), fill=GREY_TEXT)
            ty += 28
        for line in lines:
            d.text((x+20, ty), line, font=F(24), fill=fg)
            ty += 36
        y += bh + 18
        if y > H - 300: break

    # Input bar
    d.rectangle([(0, H-220),(W, H-110)], fill=WHITE)
    d.line([(0, H-220),(W, H-220)], fill=(226,232,240))
    rr(d, [30, H-200, W-150, H-130], 36, fill=GREY_CARD, outline=(203,213,225))
    d.text((60, H-170), "Type a message…", font=F(26), fill=GREY_TEXT, anchor="lm")
    rr(d, [W-140, H-200, W-30, H-130], 36, fill=TEAL)
    d.text((W-85, H-165), "▶", font=F(36, True), fill=WHITE, anchor="mm")

    nav_bar(d, H-110)
    save(img, "ss-02-chat.png")


# ===========================================================================
# Screenshot 3 — Booking screen (date + time picker)
# ===========================================================================
def make_booking():
    img = Image.new("RGB", (W, H), GREY_BG)
    d = ImageDraw.Draw(img)
    status_bar(d)
    header(d, "Book Deep Cleaning", "2BR · JVC · AED 290")

    y = 210
    # Progress bar
    steps = ["Service", "Address", "Date", "Review", "Pay"]
    sw = (W - 80) // len(steps)
    for i, step in enumerate(steps):
        active = i == 2
        done   = i < 2
        col = TEAL if (active or done) else (203,213,225)
        rr(d, [40+i*sw, y, 40+(i+1)*sw-8, y+8], 4, fill=col)
        d.text((40+i*sw+sw//2, y+28), step, font=F(20, True if active else False),
               fill=TEAL if active else (GREY_TEXT if not done else TEAL), anchor="mt")
    y += 80

    # Date picker strip
    d.text((60, y+10), "📅  Choose a date", font=F(30, True), fill=DARK_TEXT)
    y += 60
    days = [("Mon","12"), ("Tue","13"), ("Wed","14"), ("Thu","15"), ("Fri","16"), ("Sat","17")]
    dw = (W - 80) // len(days)
    for i, (day_name, day_num) in enumerate(days):
        active = i == 2
        bx = 40 + i*dw
        card(d, bx, y, dw-8, 110, r=14, fill=TEAL if active else WHITE,
             outline=(TEAL if active else (226,232,240)))
        d.text((bx+dw//2, y+28), day_name, font=F(22), fill=(WHITE if active else GREY_TEXT), anchor="mt")
        d.text((bx+dw//2, y+70), day_num, font=F(36, True), fill=(WHITE if active else DARK_TEXT), anchor="mt")
    y += 140

    # Time slots
    d.text((60, y+10), "⏰  Choose a time", font=F(30, True), fill=DARK_TEXT)
    y += 60
    slots = ["8:00 AM","9:00 AM","10:00 AM","11:00 AM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"]
    tw = (W - 80) // 3
    for i, slot in enumerate(slots):
        active = i == 2
        col_n  = i % 3
        row_n  = i // 3
        bx = 40 + col_n * (tw + 8)
        by = y + row_n * 100
        card(d, bx, by, tw, 80, r=12, fill=TEAL if active else WHITE,
             outline=(TEAL if active else (226,232,240)))
        d.text((bx+tw//2, by+40), slot, font=F(26, True if active else False),
               fill=(WHITE if active else DARK_TEXT), anchor="mm")
    y += 440

    # Summary card
    card(d, 40, y, W-80, 160, r=20, fill=WHITE)
    d.text((80, y+24), "Summary", font=F(28, True), fill=DARK_TEXT)
    d.text((80, y+70), "Wed 14 May · 10:00 AM · 2BR Deep Clean", font=F(24), fill=GREY_TEXT)
    d.text((80, y+112), "AED 290  ·  ~3 hours  ·  Team of 2", font=F(24), fill=GREY_TEXT)
    y += 180

    # CTA
    rr(d, [40, y, W-40, y+100], 28, fill=TEAL)
    d.text((W//2, y+50), "Continue to Address →", font=F(32, True), fill=WHITE, anchor="mm")

    nav_bar(d, H-110)
    save(img, "ss-03-booking.png")


# ===========================================================================
# Screenshot 4 — NFC / One-tap booking
# ===========================================================================
def make_nfc():
    img = Image.new("RGB", (W, H), NAVY)
    vgrad(img, NAVY, (30, 41, 59))
    d = ImageDraw.Draw(img)
    status_bar(d)
    d.rectangle([(0,56),(W,180)], fill=NAVY)
    d.text((W//2, 120), "One-Tap Booking", font=F(44, True), fill=WHITE, anchor="mm")

    # Big NFC ring illustration
    cx, cy, R = W//2, 520, 220
    for i, (r_off, alpha) in enumerate([(0,255),(30,140),(60,80),(90,40)]):
        col = (*TEAL_MID, alpha)
        ov = Image.new("RGBA", (W, H), (0,0,0,0))
        ImageDraw.Draw(ov).ellipse(
            [cx-R+r_off, cy-R+r_off, cx+R-r_off, cy+R-r_off],
            outline=(*TEAL_MID, alpha), width=4)
        if img.mode == "RGB":
            img = img.convert("RGBA")
        img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img)

    # NFC icon
    d.ellipse([cx-80, cy-80, cx+80, cy+80], fill=TEAL)
    d.text((cx, cy-8), "📲", font=Fe(72), fill=WHITE, anchor="mm")
    d.text((cx, cy+60), "NFC", font=F(28, True), fill=WHITE, anchor="mm")

    # Features list
    feats = [
        ("📲", "Tap NFC tag on your door or car",    "Trigger instant re-booking"),
        ("⌚", "Wear OS one-tap from wrist",         "No phone needed"),
        ("🔁", "Smart repeat booking",               "Remembers last service"),
        ("⚡", "Confirmed in 3 seconds",             "Instant team dispatch"),
    ]
    fy = 790
    for icon, title, sub in feats:
        d.text((80, fy), icon, font=Fe(44), fill=YELLOW, anchor="lm")
        d.text((160, fy-16), title, font=F(28, True), fill=WHITE)
        d.text((160, fy+22), sub,   font=F(22), fill=(148,163,184))
        fy += 90

    # Yellow badge
    rr(d, [60, fy+20, W-60, fy+120], 30, fill=YELLOW)
    d.text((W//2, fy+70), "Get your NFC tag — free with first booking!", font=F(28, True), fill=NAVY, anchor="mm")

    nav_bar(d, H-110)
    img.convert("RGB").save(OUT / "ss-04-nfc.png", optimize=True, quality=92)
    print(f"  ✓ {OUT/'ss-04-nfc.png'}  ({(OUT/'ss-04-nfc.png').stat().st_size//1024} KB)")


# ===========================================================================
# Screenshot 5 — Account / Wallet / Booking history
# ===========================================================================
def make_account():
    img = Image.new("RGB", (W, H), GREY_BG)
    d = ImageDraw.Draw(img)
    status_bar(d)

    # Header with avatar
    d.rectangle([(0,56),(W,320)], fill=TEAL)
    d.ellipse([W//2-70, 110, W//2+70, 250], fill=TEAL_LT)
    d.text((W//2, 180), "👤", font=Fe(90), fill=TEAL, anchor="mm")
    d.text((W//2, 268), "Sara Al Hashimi", font=F(36, True), fill=WHITE, anchor="mm")
    d.text((W//2, 308), "sara@email.com · +971 50 ···· ·342", font=F(22), fill=TEAL_LT, anchor="mm")

    # Wallet card
    y = 360
    rr(d, [40,y,W-40,y+200], 24, fill=TEAL)
    d.text((80, y+30), "Servia Wallet", font=F(26, True), fill=TEAL_LT)
    d.text((80, y+80), "AED 850.00", font=F(64, True), fill=WHITE)
    d.text((80, y+155), "12 top-ups · Last used 3 days ago", font=F(22), fill=TEAL_LT)
    rr(d, [W-200, y+140, W-60, y+190], 24, fill=WHITE)
    d.text((W-130, y+165), "Top-up", font=F(24, True), fill=TEAL, anchor="mm")
    y += 230

    # Recent bookings
    d.text((60, y+10), "Recent Bookings", font=F(30, True), fill=DARK_TEXT)
    y += 60
    bookings = [
        ("🧹", "Deep Cleaning · 2BR",   "12 May 2025",  "Completed", GREEN_OK),
        ("🔧", "AC Service · 1 unit",   "5 May 2025",   "Completed", GREEN_OK),
        ("🐛", "Pest Control · Villa",  "28 Apr 2025",  "Completed", GREEN_OK),
    ]
    for icon, name, date, status, scol in bookings:
        card(d, 40, y, W-80, 130, r=18, fill=WHITE)
        d.text((80, y+45), icon, font=Fe(44), fill=TEAL, anchor="lm")
        d.text((160, y+28), name,  font=F(28, True), fill=DARK_TEXT)
        d.text((160, y+68), date,  font=F(22), fill=GREY_TEXT)
        rr(d, [W-200, y+40, W-60, y+90], 20, fill=(*scol, 30))
        d.text((W-130, y+65), status, font=F(20, True), fill=scol, anchor="mm")
        y += 148

    # Rebook button
    rr(d, [40, y+10, W-40, y+110], 28, fill=TEAL)
    d.text((W//2, y+60), "🔁  Book Again", font=F(34, True), fill=WHITE, anchor="mm")

    nav_bar(d, H-110)
    save(img, "ss-05-account.png")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating Play Store phone screenshots…")
    make_home()
    make_chat()
    make_booking()
    make_nfc()
    make_account()
    print("\nDone! Upload files in:", OUT)
