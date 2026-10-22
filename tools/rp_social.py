#!/usr/bin/env python3
"""Generatore grafiche social Ristrutturare Pro.

Uso: python3 rp_social.py spec.json OUTDIR LOGODIR
spec.json = {"name": "post", "theme": "dark"|"light", "formats": ["ig","story"],
             "slides": [{"kicker": "", "title": "", "highlight": "", "body": "",
                          "badge": "", "cta": "", "note": ""}]}
- ig = 1080x1350 (Instagram/LinkedIn), story = 1080x1920 (TikTok/Reels/Storie)
- LOGODIR deve contenere rp-logo-bianco.png (trasparente) e rp-logo-colori.png
Produce OUTDIR/<name>_<format>_<n>.png
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

NAVY = (0, 36, 80)
GREEN = (47, 119, 48)
GOLD = (201, 162, 74)
BLACK = (11, 11, 13)
WHITE = (255, 255, 255)
GREY = (190, 196, 206)

FONT_DIR = "/usr/share/fonts/truetype/google-fonts"


def font(weight, size):
    alias = {"ExtraBold": "Bold", "Black": "Bold", "SemiBold": "Medium"}
    for name in (f"Poppins-{weight}.ttf", f"Poppins-{alias.get(weight, weight)}.ttf", "Poppins-Regular.ttf"):
        p = os.path.join(FONT_DIR, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=fnt) <= width:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def block(draw, xy, text, fnt, fill, width, spacing=1.18, align="left"):
    x, y = xy
    lh = int(fnt.size * spacing)
    for line in wrap(draw, text, fnt, width):
        if align == "center":
            lx = x + (width - draw.textlength(line, font=fnt)) / 2
        else:
            lx = x
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += lh
    return y


def fit_font(draw, text, weight, start, minsize, width, max_lines):
    size = start
    while size > minsize:
        f = font(weight, size)
        ls = wrap(draw, text, f, width)
        if len(ls) <= max_lines and all(draw.textlength(l, font=f) <= width for l in ls):
            return f
        size -= 4
    return font(weight, minsize)


def background(w, h, theme):
    if theme == "dark":
        img = Image.new("RGB", (w, h), BLACK)
        glow = Image.new("RGB", (w, h), BLACK)
        g = ImageDraw.Draw(glow)
        g.ellipse((-w * 0.4, -h * 0.25, w * 0.9, h * 0.55), fill=(0, 30, 70))
        g.ellipse((w * 0.45, h * 0.6, w * 1.5, h * 1.3), fill=(14, 48, 20))
        img = glow.filter(ImageFilter.GaussianBlur(220))
    else:
        img = Image.new("RGB", (w, h), WHITE)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, w, 14), fill=NAVY)
        d.rectangle((0, 14, w, 22), fill=GREEN)
    return img


def paste_logo(img, logodir, theme, box_w, center_y):
    path = os.path.join(logodir, "rp-logo-bianco.png" if theme == "dark" else "rp-logo-colori.png")
    logo = Image.open(path).convert("RGBA")
    if theme != "dark":  # rende trasparente il fondo bianco del logo a colori
        px = logo.getdata()
        logo.putdata([(r, g, b, 0) if r > 245 and g > 245 and b > 245 else (r, g, b, a) for r, g, b, a in px])
        logo = logo.crop(logo.getbbox())
    ratio = box_w / logo.width
    logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)), Image.LANCZOS)
    x = (img.width - logo.width) // 2
    img.paste(logo, (x, int(center_y - logo.height / 2)), logo)
    return logo.height


def render(slide, theme, size, logodir, idx, total):
    w, h = size
    img = background(w, h, theme)
    d = ImageDraw.Draw(img)
    fg = WHITE if theme == "dark" else NAVY
    sub = GREY if theme == "dark" else (60, 70, 90)
    accent = GOLD if theme == "dark" else GREEN
    m = 90
    inner = w - 2 * m
    story = h > 1500

    if theme == "dark":
        d.rectangle((40, 40, w - 40, h - 40), outline=GOLD, width=3)
    else:
        d.rectangle((0, h - 22, w, h - 14), fill=GREEN)
        d.rectangle((0, h - 14, w, h), fill=NAVY)

    # logo in alto
    top = 170 if story else 130
    lh = paste_logo(img, logodir, theme, 380 if story else 320, top + 70)
    content_top = top + 70 + lh / 2 + 50

    # area CTA / note in basso
    bottom = h - (130 if story else 100)
    cta_top = bottom - 120 if slide.get("cta") else bottom
    nf = font("Regular", 26)
    note_lines = wrap(d, slide["note"], nf, inner) if slide.get("note") else []
    content_bottom = cta_top - 30 - len(note_lines) * 34 - (20 if note_lines else 0)

    # numero grande decorativo
    num = slide.get("number")
    if num:
        big = font("ExtraBold", 520 if story else 420)
        col = (233, 240, 233) if theme != "dark" else (24, 40, 60)
        d.text((w - m - d.textlength(str(num), font=big) + 30, content_top - 60), str(num), font=big, fill=col)

    # misura blocchi
    items = []
    if slide.get("kicker"):
        items.append(("kicker", 64 + 46))
    tf = hf = bf = None
    if slide.get("title"):
        tf = fit_font(d, slide["title"], "Bold", 104 if story else 92, 56, inner, 4)
        items.append(("title", len(wrap(d, slide["title"], tf, inner)) * int(tf.size * 1.12) + 44))
    if slide.get("highlight"):
        hf = fit_font(d, slide["highlight"], "ExtraBold", 140 if story else 124, 64, inner, 2)
        items.append(("highlight", len(wrap(d, slide["highlight"], hf, inner)) * int(hf.size * 1.06) + 44))
    if slide.get("badge"):
        items.append(("badge", 130))
    if slide.get("body"):
        bf = font("Regular", 46 if story else 40)
        items.append(("body", len(wrap(d, slide["body"], bf, inner)) * int(bf.size * 1.35) + 10))
    total_h = sum(hh for _, hh in items)
    y = content_top + max(0, (content_bottom - content_top - total_h) / 2)

    for kind, hh in items:
        if kind == "kicker":
            kf = font("SemiBold", 34)
            kt = slide["kicker"].upper()
            tw = d.textlength(kt, font=kf)
            d.rounded_rectangle((m, y, m + tw + 56, y + 64), radius=32, fill=accent)
            d.text((m + 28, y + 11), kt, font=kf, fill=BLACK if theme == "dark" else WHITE)
        elif kind == "title":
            block(d, (m, y), slide["title"], tf, fg, inner, 1.12)
        elif kind == "highlight":
            block(d, (m, y), slide["highlight"], hf, accent, inner, 1.06)
        elif kind == "badge":
            bft = font("Bold", 46)
            bt = slide["badge"]
            tw = d.textlength(bt, font=bft)
            d.rounded_rectangle((m, y, m + tw + 64, y + 92), radius=16, outline=accent, width=4)
            d.text((m + 32, y + 16), bt, font=bft, fill=fg)
        elif kind == "body":
            block(d, (m, y), slide["body"], bf, sub, inner, 1.35)
        y += hh

    ny = content_bottom + 10
    for ln in note_lines:
        d.text((m, ny), ln, font=nf, fill=sub)
        ny += 34
    if slide.get("cta"):
        cf = font("Bold", 42)
        ct = slide["cta"]
        d.rounded_rectangle((m, cta_top, w - m, cta_top + 104), radius=52, fill=GREEN)
        d.text(((w - d.textlength(ct, font=cf)) / 2, cta_top + 24), ct, font=cf, fill=WHITE)

    if total > 1:
        pf = font("Medium", 28)
        pt = f"{idx}/{total}"
        d.text((w - m - d.textlength(pt, font=pf), 70 if theme == "dark" else 50), pt, font=pf, fill=sub)
    return img


def main():
    spec_path, outdir, logodir = sys.argv[1:4]
    spec = json.load(open(spec_path))
    os.makedirs(outdir, exist_ok=True)
    sizes = {"ig": (1080, 1350), "story": (1080, 1920)}
    out = []
    slides = spec["slides"]
    for fmt in spec.get("formats", ["ig", "story"]):
        for i, s in enumerate(slides, 1):
            img = render(s, spec.get("theme", "dark"), sizes[fmt], logodir, i, len(slides))
            p = os.path.join(outdir, f"{spec['name']}_{fmt}_{i}.png")
            img.save(p, optimize=True)
            out.append(p)
    story = [p for p in out if "_story_" in p]
    if spec.get("video", True) and story:
        import subprocess
        mp4 = os.path.join(outdir, f"{spec['name']}_reel.mp4")
        secs = spec.get("seconds_per_slide", 3.5)
        inputs, filters = [], []
        for i, p in enumerate(story):
            inputs += ["-loop", "1", "-t", str(secs), "-i", p]
            filters.append(f"[{i}:v]scale=1080:1920,format=yuv420p,fade=t=in:st=0:d=0.3,fade=t=out:st={secs-0.3}:d=0.3[v{i}]")
        concat = "".join(f"[v{i}]" for i in range(len(story))) + f"concat=n={len(story)}:v=1:a=0[out]"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
               "-f", "lavfi", "-t", str(secs * len(story)), "-i", "anullsrc=r=44100:cl=stereo",
               "-filter_complex", ";".join(filters) + ";" + concat,
               "-map", "[out]", "-map", f"{len(story)}:a", "-c:v", "libx264", "-r", "30",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", mp4]
        subprocess.run(cmd, check=True)
        out.append(mp4)
    print("\n".join(out))


if __name__ == "__main__":
    main()
