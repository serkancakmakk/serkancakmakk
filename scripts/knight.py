"""Generate an animated SVG of a pixel knight slashing through the GitHub contribution grid.

Usage: python scripts/knight.py <github-user> <output.svg>
"""
import re
import sys
import urllib.request

LEVEL_COLORS = ["#161b22", "#4a0072", "#7a00ff", "#c000e0", "#ff00cc"]

CELL, GAP = 11, 3
PITCH = CELL + GAP
GRID_X, GRID_Y = 70, 24
PX = 4  # knight pixel size

DT = 0.28  # seconds per column
INTRO, OUTRO = 1.0, 3.0

# Knight sprite, facing right. 12 x 14 pixels.
KNIGHT = [
    "....PP......",
    "...PPP......",
    "..OHHHHO....",
    ".OHHHHHHO...",
    ".OHHVVHHO...",
    ".OHHHHHHO...",
    "..OHHHHO....",
    ".CAAAAAAO...",
    "CCAAYAAAO...",
    "CCAAAAAAO...",
    ".CAAAAAO....",
    "..LL.LL.....",
    "..LL.LL.....",
    ".BBB.BBB....",
]
KNIGHT_COLORS = {
    "P": "#ff00cc", "O": "#0d0221", "H": "#c9d1e8", "V": "#00e5ff",
    "C": "#c000e0", "A": "#7a00ff", "Y": "#ffd23f", "L": "#4b4b6e", "B": "#2a2a40",
}


def fetch_grid(user):
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "knight-svg"})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    cells = {}
    for td in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        pos = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', td)
        level = re.search(r'data-level="(\d)"', td)
        if pos and level:
            cells[(int(pos.group(1)), int(pos.group(2)))] = int(level.group(1))
    if not cells:
        raise SystemExit("no contribution cells found")
    return cells


def pct(t, total):
    return f"{100 * t / total:.3f}%"


def build(cells):
    cols = max(c for _, c in cells) + 1
    width = GRID_X + cols * PITCH + 30
    height = GRID_Y + 7 * PITCH + 30
    total = INTRO + cols * DT + OUTRO

    sprite_w, sprite_h = len(KNIGHT[0]) * PX, len(KNIGHT) * PX
    hand_x, hand_y = 9 * PX, 8 * PX + PX // 2
    reach = hand_x + 4  # distance from knight origin to the column being hit
    knight_y = GRID_Y + (7 * PITCH - GAP) / 2 - hand_y

    def knight_x(col):
        return GRID_X + col * PITCH - reach

    css = [
        ".c{transform-box:fill-box;transform-origin:center}",
        f".kn{{animation:walk {total}s linear infinite}}",
        f"@keyframes walk{{0%{{transform:translate({knight_x(-6)}px,{knight_y}px)}}"
        f"{pct(INTRO, total)}{{transform:translate({knight_x(0)}px,{knight_y}px)}}"
        f"{pct(INTRO + cols * DT, total)}{{transform:translate({knight_x(cols)}px,{knight_y}px)}}"
        f"100%{{transform:translate({width + 40}px,{knight_y}px)}}}}",
        f".bob{{animation:bob {DT}s steps(2,end) infinite}}",
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}",
        f".sw{{animation:sw {DT}s cubic-bezier(.6,0,.2,1) infinite}}",
        "@keyframes sw{0%{transform:rotate(-35deg)}45%{transform:rotate(165deg)}100%{transform:rotate(-35deg)}}",
        f".arc{{animation:arc {DT}s linear infinite}}",
        "@keyframes arc{0%,15%{opacity:0}35%{opacity:.9}60%,100%{opacity:0}}",
        f".clr{{animation:clr {total}s steps(1,end) infinite}}",
        f"@keyframes clr{{0%{{opacity:0}}{pct(INTRO + cols * DT + 0.6, total)}{{opacity:1}}"
        f"{pct(total - 0.3, total)}{{opacity:0}}}}",
        ".bl{animation:bl .5s steps(1,end) infinite}",
        "@keyframes bl{0%{opacity:1}50%{opacity:0}}",
    ]

    rects = []
    for col in range(cols):
        hit = INTRO + col * DT + DT * 0.35
        keyframes_used = False
        for row in range(7):
            level = cells.get((row, col))
            if level is None:
                continue
            x, y = GRID_X + col * PITCH, GRID_Y + row * PITCH
            color = LEVEL_COLORS[level]
            cls = ""
            if level > 0:
                cls = f' class="c h{col}"'
                keyframes_used = True
            rects.append(f'<rect{cls} x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
        if keyframes_used:
            a, b, c = pct(hit, total), pct(hit + 0.08, total), pct(hit + 0.35, total)
            css.append(f".h{col}{{animation:h{col} {total}s linear infinite}}")
            css.append(
                f"@keyframes h{col}{{0%,{a}{{opacity:1;filter:brightness(1);transform:scale(1) rotate(0)}}"
                f"{b}{{opacity:1;filter:brightness(3);transform:scale(1.35) rotate(15deg)}}"
                f"{c}{{opacity:0;transform:scale(0) rotate(90deg)}}"
                f"{pct(total - 0.4, total)}{{opacity:0;transform:scale(0)}}"
                f"100%{{opacity:1;transform:scale(1)}}}}"
            )

    sprite = []
    for r, line in enumerate(KNIGHT):
        for c, ch in enumerate(line):
            if ch != ".":
                sprite.append(f'<rect x="{c * PX}" y="{r * PX}" width="{PX}" height="{PX}" fill="{KNIGHT_COLORS[ch]}"/>')

    blade = 4 * PITCH - 4
    sword = (
        f'<g transform="translate({hand_x},{hand_y})"><g class="sw">'
        f'<path class="arc" d="M0,{-blade} A{blade},{blade} 0 0 1 0,{blade}" fill="none" '
        f'stroke="#00e5ff" stroke-width="3" stroke-linecap="round" opacity="0"/>'
        f'<rect x="-2" y="{-blade}" width="4" height="{blade - 6}" fill="#e6fbff"/>'
        f'<rect x="-1" y="{-blade}" width="2" height="{blade - 6}" fill="#00e5ff"/>'
        f'<rect x="-6" y="-7" width="12" height="3" fill="#ffd23f"/>'
        f'<rect x="-1.5" y="-4" width="3" height="6" fill="#8a5a2b"/>'
        f'</g></g>'
    )

    text_y = GRID_Y + 7 * PITCH + 18
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
        f'<style>{"".join(css)}</style>'
        f'{"".join(rects)}'
        f'<g class="kn"><g class="bob">{"".join(sprite)}{sword}</g></g>'
        f'<g class="clr" opacity="0"><text class="bl" x="{width / 2}" y="{text_y}" text-anchor="middle" '
        f'font-family="Courier New,monospace" font-weight="bold" font-size="14" fill="#ff00cc" '
        f'letter-spacing="3">STAGE CLEAR</text></g>'
        f'</svg>'
    )


if __name__ == "__main__":
    user, out = sys.argv[1], sys.argv[2]
    svg = build(fetch_grid(user))
    with open(out, "w") as f:
        f.write(svg)
