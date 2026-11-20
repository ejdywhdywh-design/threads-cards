"""4컷 육아툰(1080x1350 PNG) 생성기.

사용:
  python make_comic.py <spec.json> <out.png>   스펙 JSON 으로 4컷 만화를 그린다
  python make_comic.py --sheet <out.png>       캐릭터 시트(표정 목록)를 그린다

spec.json 형식은 examples/cream-bun.json 참고.
  characters: {"dad": {"shirt": "#4F7CAC", ...}}  캐릭터 모양 덮어쓰기(선택)
  panels[4]:  caption(상단 자막), bg(색 이름 또는 #hex), sfx(바닥 띠 글자),
              chars[]: who(dad|hyung|dongsaeng), expr, arms, props[왼손,오른손], x(0~1), scale, sit
              bubbles[]: who, text(\\n 으로 줄바꿈)
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 2  # 안티앨리어싱용 배율
W, H = 1080, 1350
FONT_DIR = Path(__file__).resolve().parent / "fonts"
INK = "#3B2A20"
SKIN = "#FFDBB8"
PANTS = "#5B6B8C"
FOOTER = "아산 사는 부산 남자  ·  @asan_busan_namja"

CHARS = {
    "dad": {"shirt": "#4F7CAC", "hair": "#2B2B2B", "style": "dad", "glasses": True, "stubble": True, "k": 1.0},
    "hyung": {"shirt": "#E5533C", "hair": "#2B2B2B", "style": "spiky", "glasses": False, "stubble": False, "k": 0.85},
    "dongsaeng": {"shirt": "#F2B632", "hair": "#7A4A2B", "style": "pig", "glasses": False, "stubble": False, "k": 0.72},
}
BG = {"warm": "#FFF3D6", "pink": "#FFE6E6", "blue": "#E3F0FF", "green": "#E8F6DF", "lavender": "#EEE6FA", "night": "#C9D3F2"}
ARMS = {
    "down": ((-45, 30), (45, 30)),
    "up": ((-74, -36), (74, -36)),
    "hold": ((-30, 34), (30, 34)),
    "point_right": ((-40, 34), (78, -14)),
    "point_left": ((-78, -14), (40, 34)),
    "shrug": ((-60, 10), (60, 10)),
    "lap": ((-36, 52), (40, 54)),
}
EXPRS = ["smile", "happy", "yum", "surprised", "sleepy", "sweat", "sad", "cry", "angry"]
EXPR_KO = {"smile": "웃음", "happy": "활짝", "yum": "냠냠", "surprised": "깜짝", "sleepy": "졸림", "sweat": "당황", "sad": "시무룩", "cry": "엉엉", "angry": "화남"}
PROPS = ["bun", "phone", "bowl", "ball", "book", "icecream", "crumbs"]

d = None
IMG = None


def begin(w, h, bg="#FFFDF7"):
    global d, IMG
    IMG = Image.new("RGB", (w * S, h * S), bg)
    d = ImageDraw.Draw(IMG)


def P(v):
    return [c * S for c in v]


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), max(1, int(size * S)))


def ell(box, fill, w=4):
    d.ellipse(P(box), fill=fill, outline=INK if w else None, width=max(1, int(w * S)))


def rrect(box, r, fill, w=4):
    d.rounded_rectangle(P(box), radius=int(r * S), fill=fill, outline=INK if w else None, width=max(1, int(w * S)))


def line(pts, w=5, fill=INK):
    d.line(P([c for p in pts for c in p]), fill=fill, width=max(1, int(w * S)), joint="curve")


def limb(pts, w, color):
    line(pts, w + 5, INK)
    line(pts, w, color)


def arc(box, a0, a1, w=3):
    d.arc(P(box), a0, a1, fill=INK, width=max(1, int(w * S)))


def poly(pts, fill):
    d.polygon(P([c for p in pts for c in p]), fill=fill)


def person(cx, top, k, c, expr, arms, sit=False):
    """캐릭터 한 명. 반환: (손 좌표 2개, 머리 맨 위 y)"""
    hy = top + 56 * k
    r = 50 * k
    shirt, hair, style = c["shirt"], c["hair"], c["style"]
    for sx in (-1, 1):
        if sit:
            limb([(cx + sx * 14 * k, top + 168 * k), (cx + sx * 58 * k, top + 188 * k)], 9 * k, PANTS)
            ell((cx + sx * 58 * k - 8 * k, top + 180 * k, cx + sx * 58 * k + 12 * k, top + 196 * k), "#FFFFFF", 3)
        else:
            limb([(cx + sx * 14 * k, top + 168 * k), (cx + sx * 14 * k, top + 198 * k)], 9 * k, PANTS)
            ell((cx + sx * 14 * k - 12 * k, top + 194 * k, cx + sx * 14 * k + 12 * k, top + 207 * k), "#FFFFFF", 3)
    if style == "pig":
        for sx in (-1, 1):
            ell((cx + sx * (r + 3 * k) - 17 * k, hy - r * 0.1 - 17 * k, cx + sx * (r + 3 * k) + 17 * k, hy - r * 0.1 + 17 * k), hair, 4)
    rrect((cx - 32 * k, top + 104 * k, cx + 32 * k, top + 172 * k), 14 * k, shirt, 4)
    hands = []
    for sx, (dx, dy) in zip((-1, 1), arms):
        sh = (cx + sx * 30 * k, top + 118 * k)
        hd = (sh[0] + dx * k, sh[1] + dy * k)
        limb([sh, hd], 8 * k, shirt)
        ell((hd[0] - 8 * k, hd[1] - 8 * k, hd[0] + 8 * k, hd[1] + 8 * k), SKIN, 3)
        hands.append(hd)
    ell((cx - r - 3 * k, hy - r - 6 * k, cx + r + 3 * k, hy + r * 0.2), hair, 4)
    if style == "spiky":
        for a in (-30, 0, 30):
            bx = cx + a * k
            pts = [(bx - 12 * k, hy - r - 2 * k), (bx, hy - r - 26 * k), (bx + 12 * k, hy - r - 2 * k)]
            poly(pts, hair)
            line(pts, 4)
    ell((cx - r, hy - r + 16 * k, cx + r, hy + r), SKIN, 4)
    ey, my = hy + 4 * k, hy + 28 * k
    ex = [cx - 18 * k, cx + 18 * k]
    for sx in (-1, 1):
        d.ellipse(P([cx + sx * 31 * k - 9 * k, hy + 16 * k, cx + sx * 31 * k + 9 * k, hy + 27 * k]), fill="#FFB8B8")
    if expr in ("smile", "sweat", "angry", "sad"):
        for x in ex:
            d.ellipse(P([x - 4 * k, ey - 5 * k, x + 4 * k, ey + 5 * k]), fill=INK)
    if expr in ("happy", "yum"):
        for x in ex:
            arc((x - 9 * k, ey - 6 * k, x + 9 * k, ey + 10 * k), 200, 340, 3.5 * k)
    if expr == "cry":
        line([(ex[0] - 8 * k, ey - 6 * k), (ex[0] + 5 * k, ey), (ex[0] - 8 * k, ey + 6 * k)], 3.5 * k)
        line([(ex[1] + 8 * k, ey - 6 * k), (ex[1] - 5 * k, ey), (ex[1] + 8 * k, ey + 6 * k)], 3.5 * k)
        for x in ex:
            ell((x - 4 * k, ey + 8 * k, x + 4 * k, ey + 26 * k), "#8FD0FF", 2)
    if expr == "surprised":
        for x in ex:
            ell((x - 7 * k, ey - 8 * k, x + 7 * k, ey + 8 * k), "#FFFFFF", 3)
            d.ellipse(P([x - 2.5 * k, ey - 2.5 * k, x + 2.5 * k, ey + 2.5 * k]), fill=INK)
    if expr == "sleepy":
        for x in ex:
            line([(x - 8 * k, ey + k), (x + 8 * k, ey + k)], 3.5 * k)
    if expr in ("smile", "happy", "sleepy"):
        arc((cx - 11 * k, my - 10 * k, cx + 11 * k, my + 8 * k), 20, 160, 3 * k)
    if expr == "sleepy":
        d.text(P((cx + r * 0.95, hy - r * 0.85)), "z", font=font("NanumGothicBold.ttf", 12 + 22 * k), fill=INK, anchor="mm")
    elif expr == "sweat":
        line([(cx - 10 * k, my), (cx - 5 * k, my - 3 * k), (cx, my), (cx + 5 * k, my - 3 * k), (cx + 10 * k, my)], 3 * k)
        ell((cx + r * 0.75, hy - r * 0.85, cx + r * 0.75 + 14 * k, hy - r * 0.85 + 22 * k), "#8FD0FF", 3)
    elif expr in ("angry", "sad"):
        arc((cx - 9 * k, my, cx + 9 * k, my + 14 * k), 200, 340, 3 * k)
        if expr == "angry":
            line([(ex[0] - 11 * k, ey - 13 * k), (ex[0] + 7 * k, ey - 7 * k)], 3.5 * k)
            line([(ex[1] + 11 * k, ey - 13 * k), (ex[1] - 7 * k, ey - 7 * k)], 3.5 * k)
    elif expr == "cry":
        ell((cx - 10 * k, my - 6 * k, cx + 10 * k, my + 12 * k), "#B8413A", 3)
    elif expr == "surprised":
        ell((cx - 6 * k, my - 4 * k, cx + 6 * k, my + 10 * k), "#B8413A", 3)
    elif expr == "yum":
        ell((cx - 10 * k, my - 6 * k, cx + 10 * k, my + 12 * k), "#B8413A", 3)
        d.ellipse(P([cx - 5 * k, my + 4 * k, cx + 5 * k, my + 11 * k]), fill="#FF9FA8")
    if c.get("glasses"):
        for x in ex:
            ell((x - 12 * k, ey - 11 * k, x + 12 * k, ey + 11 * k), None, 3)
        line([(ex[0] + 12 * k, ey), (ex[1] - 12 * k, ey)], 3)
    if c.get("stubble"):
        for i in range(-3, 4):
            d.ellipse(P([cx + i * 7 * k - 1.5 * k, hy + 40 * k - abs(i) * 1.6 * k, cx + i * 7 * k + 1.5 * k, hy + 43 * k - abs(i) * 1.6 * k]), fill=INK)
    return hands, top - (24 * k if style == "spiky" else 0)


def bun(cx, cy, k=1.0, cut="right"):
    ell((cx - 30 * k, cy - 20 * k, cx + 30 * k, cy + 20 * k), "#E8B66B", 4)
    if cut == "right":
        ell((cx + 12 * k, cy - 17 * k, cx + 32 * k, cy + 17 * k), "#FFFBEA", 3)
    else:
        ell((cx - 32 * k, cy - 17 * k, cx - 12 * k, cy + 17 * k), "#FFFBEA", 3)


def draw_prop(kind, hand, k, side):
    x, y = hand[0], hand[1] - 16 * k
    if kind == "bun":
        bun(x, y, 0.75 * k, "right" if side < 0 else "left")
    elif kind == "phone":
        rrect((x - 10 * k, y - 18 * k, x + 10 * k, y + 18 * k), 4 * k, "#2F3A4A", 3)
        rrect((x - 7 * k, y - 14 * k, x + 7 * k, y + 10 * k), 2 * k, "#BFE3FF", 0)
    elif kind == "bowl":
        d.pieslice(P([x - 20 * k, y - 10 * k, x + 20 * k, y + 22 * k]), 0, 180, fill="#FFFFFF", outline=INK, width=int(3 * S))
        line([(x - 20 * k, y + 6 * k), (x + 20 * k, y + 6 * k)], 3)
        for sx in (-6, 6):
            line([(x + sx * k, y - 4 * k), (x + (sx + 3) * k, y - 12 * k), (x + sx * k, y - 20 * k)], 2.5)
    elif kind == "ball":
        ell((x - 13 * k, y - 13 * k, x + 13 * k, y + 13 * k), "#E5533C", 3)
        line([(x - 12 * k, y), (x + 12 * k, y)], 2.5, "#FFFFFF")
    elif kind == "book":
        rrect((x - 16 * k, y - 12 * k, x + 16 * k, y + 12 * k), 2 * k, "#5B8DEF", 3)
        line([(x - 8 * k, y - 12 * k), (x - 8 * k, y + 12 * k)], 2.5)
    elif kind == "icecream":
        poly([(x - 9 * k, y), (x + 9 * k, y), (x, y + 26 * k)], "#E8B66B")
        line([(x - 9 * k, y), (x, y + 26 * k), (x + 9 * k, y)], 3)
        ell((x - 13 * k, y - 24 * k, x + 13 * k, y + 2 * k), "#FFB8D0", 3)
    elif kind == "crumbs":
        for dx, dy in ((-6, 6), (8, 10), (0, 18), (-14, 14)):
            d.ellipse(P([x + 24 * k + dx * k, y + 14 * k + dy * k, x + 24 * k + (dx + 8) * k, y + 14 * k + (dy + 6) * k]), fill="#C98B4A")


def bubble(cx, cy, w, h, text, tail_to, size=34):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    tx, ty = tail_to
    bx = min(max(tx, x0 + 34), x1 - 34)
    rrect((x0, y0, x1, y1), 20, "#FFFFFF", 4)
    tail = [(bx - 14, y1 - 2), (bx + 14, y1 - 2), (tx, ty)]
    poly(tail, "#FFFFFF")
    line([tail[0], tail[2], tail[1]], 4)
    d.line(P([bx - 12, y1 - 1.5, bx + 12, y1 - 1.5]), fill="#FFFFFF", width=int(5 * S))
    d.multiline_text(P((cx, cy)), text, font=font("NanumGothicBold.ttf", size), fill=INK, anchor="mm", align="center", spacing=int(6 * S))


def panel_frame(box, color, label):
    x0, y0, x1, y1 = box
    rrect(box, 22, color, 6)
    d.line(P([x0 + 8, y1 - 70, x1 - 8, y1 - 70]), fill="#CDB892", width=int(4 * S))
    if label:
        f = font("NanumGothicBold.ttf", 26)
        tw = d.textlength(label, font=f) / S
        rrect((x0 + 16, y0 + 16, x0 + 44 + tw, y0 + 62), 10, "#FFE27A", 3)
        d.text(P((x0 + 30, y0 + 39)), label, font=f, fill=INK, anchor="lm")
    return y1 - 70


def draw_panel(box, p, chars):
    x0, y0, x1, y1 = box
    color = BG.get(p.get("bg", "warm"), p.get("bg", "#FFF3D6"))
    floor = panel_frame(box, color, p.get("caption", ""))
    items = p.get("chars", [])
    n = len(items)
    factor = {1: 1.25, 2: 1.1}.get(n, 1.0)
    slots = {1: [0.5], 2: [0.3, 0.72], 3: [0.2, 0.5, 0.8]}.get(n) or [(i + 0.5) / max(n, 1) for i in range(n)]
    heads = {}
    for i, it in enumerate(items):
        who = it["who"]
        if who not in chars:
            raise SystemExit(f"알 수 없는 캐릭터: {who}")
        c = chars[who]
        k = c["k"] * factor * it.get("scale", 1.0)
        arms = ARMS.get(it.get("arms", "down"), ARMS["down"])
        # 팔·머리가 칸 밖으로 나가지 않게 가로 위치를 안쪽으로 맞춘다
        half = max(abs(-30 + arms[0][0]), abs(30 + arms[1][0]), 72 if c["style"] == "pig" else 56) * k + 10 * k
        cx = min(max(x0 + (x1 - x0) * it.get("x", slots[i]), x0 + 8 + half), x1 - 8 - half)
        sit = bool(it.get("sit"))
        top = floor - (196 if sit else 206) * k
        expr = it.get("expr", "smile")
        hands, head_top = person(cx, top, k, c, expr if expr in EXPRS else "smile", arms, sit)
        for side, hand, pr in zip((-1, 1), hands, (it.get("props") or [None, None])):
            if pr:
                draw_prop(pr, hand, k, side)
        heads.setdefault(who, (cx, head_top))
    placed = []
    for b in sorted(p.get("bubbles", []), key=lambda b: heads.get(b["who"], (0, 0))[0]):
        if b["who"] not in heads:
            raise SystemExit(f"말풍선 화자가 컷에 없어요: {b['who']}")
        hx, ht = heads[b["who"]]
        size = 34
        lines = b["text"].split("\n")
        f = font("NanumGothicBold.ttf", size)
        w = max(d.textlength(t, font=f) for t in lines) / S + 40
        h = size * 1.3 * len(lines) + 24
        cx = min(max(hx, x0 + 12 + w / 2), x1 - 12 - w / 2)
        cy = ht - 38 - h / 2
        for q in placed:
            if abs(cx - q["cx"]) < (w + q["w"]) / 2 + 8 and abs(cy - q["cy"]) < (h + q["h"]) / 2 + 8:
                for nx in (q["cx"] + (w + q["w"]) / 2 + 10, q["cx"] - (w + q["w"]) / 2 - 10):
                    if x0 + 12 + w / 2 <= nx <= x1 - 12 - w / 2:
                        cx = nx
                        break
                else:
                    cy = q["cy"] - (h + q["h"]) / 2 - 10
        cy = max(cy, y0 + 70 + h / 2)
        placed.append({"cx": cx, "cy": cy, "w": w, "h": h})
        bubble(cx, cy, w, h, b["text"], (hx, ht + 2), size)
    if p.get("sfx"):
        d.text(P((x1 - 28, y1 - 34)), p["sfx"], font=font("NanumGothicExtraBold.ttf", 34), fill="#C25E1F", anchor="rm")


def finish(w, h, out):
    IMG.resize((w, h), Image.LANCZOS).save(out, "PNG", optimize=True)


def render(spec, out):
    chars = {k: {**v, **spec.get("characters", {}).get(k, {})} for k, v in CHARS.items()}
    panels = spec["panels"]
    if len(panels) != 4:
        raise SystemExit(f"컷은 4개여야 해요 (지금 {len(panels)}개)")
    begin(W, H)
    rrect((40, 30, 170, 80), 25, "#E8772E", 0)
    d.text(P((105, 55)), spec.get("tag", "육아툰"), font=font("NanumGothicBold.ttf", 30), fill="#FFFFFF", anchor="mm")
    title = spec["title"]
    for size in (58, 52, 46, 40, 34):
        tf = font("NanumGothicExtraBold.ttf", size)
        if d.textlength(title, font=tf) / S <= 1000:
            break
    d.text(P((40, 125)), title, font=tf, fill=INK, anchor="lm")
    boxes = [(40, 165, 530, 720), (550, 165, 1040, 720), (40, 740, 530, 1295), (550, 740, 1040, 1295)]
    for box, p in zip(boxes, panels):
        draw_panel(box, p, chars)
    d.text(P((540, 1322)), FOOTER, font=font("NanumGothic.ttf", 24), fill="#8A7A66", anchor="mm")
    finish(W, H, out)


def render_sheet(out):
    names = {"dad": "아빠", "hyung": "형아 (7살)", "dongsaeng": "동생 (5살)"}
    w, h = 1080, 780
    begin(w, h)
    d.text(P((40, 50)), "캐릭터 시트", font=font("NanumGothicExtraBold.ttf", 44), fill=INK, anchor="lm")
    lf = font("NanumGothic.ttf", 18)
    for row, (who, c) in enumerate(CHARS.items()):
        y = 110 + row * 220
        d.text(P((40, y)), names[who], font=font("NanumGothicBold.ttf", 28), fill=INK, anchor="lm")
        k = 0.56 * c["k"] / 0.85
        for col, e in enumerate(EXPRS):
            cx = 40 + 55 + col * 111
            person(cx, y + 25, k, c, e, ARMS["down"], False)
            d.text(P((cx, y + 25 + 214 * k + 14)), EXPR_KO[e], font=lf, fill=INK, anchor="mm")
    finish(w, h, out)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--sheet":
        render_sheet(sys.argv[2])
    elif len(sys.argv) >= 3:
        render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2])
    else:
        raise SystemExit(__doc__)
