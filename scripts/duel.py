"""Generate the arcade duel: two pixel knights trading AK-47 fire, plus its section title.

Usage: python scripts/duel.py  (writes assets/duel.svg and assets/t_versus.svg)
"""
import random

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    " ": ["00000"] * 7,
}


def text(s, x, y, color, scale=1, shadow=None):
    """Pixel text as rects; returns (svg, width)."""
    out = []
    for dx, dy, fill in ([(1, 1, shadow)] if shadow else []) + [(0, 0, color)]:
        rects = []
        for i, ch in enumerate(s):
            for r, row in enumerate(FONT[ch]):
                for c, bit in enumerate(row):
                    if bit == "1":
                        rects.append(
                            f'<rect x="{x + (i * 6 + c) * scale + dx}" y="{y + r * scale + dy}" '
                            f'width="{scale}" height="{scale}"/>'
                        )
        out.append(f'<g fill="{fill}">{"".join(rects)}</g>')
    return "".join(out), (len(s) * 6 - 1) * scale


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
P1_COLORS = {"P": "#ff00cc", "O": "#0d0221", "H": "#c9d1e8", "V": "#00e5ff", "C": "#c000e0",
             "A": "#7a00ff", "Y": "#ffd23f", "L": "#4b4b6e", "B": "#2a2a40"}
P2_COLORS = {**P1_COLORS, "P": "#ffd23f", "V": "#ff00cc", "C": "#00e5ff", "A": "#0077a8", "Y": "#ff00cc"}

# AK-47 facing right; grip at (7, 4).
AK = [
    ".......................K",
    "WWWW..KKKKKKKWWWWWKKKKKK",
    "WWWWWWKKKKKKKWWWWW......",
    "WW....KK.MM.............",
    "......KK..MM............",
    "...........MM...........",
]
AK_COLORS = {"K": "#23232f", "W": "#a0602b", "M": "#c4561c"}

PX = 2
W, H = 220, 88
GROUND = 72
P1_X, P2_X = 28, 168
KY = GROUND - len(KNIGHT) * PX
GUN_X, GUN_Y = 9 * PX - 7, 8 * PX + 1 - 4  # gun origin inside the knight
MUZZLE = (GUN_X + len(AK[0]), GUN_Y + 1.5)

T = 12.0
TRAVEL, GAP = 0.45, 0.12
P1_BURSTS = [1.0, 4.0, 7.0]
P2_BURSTS = [2.5, 5.5]
DEATH = P1_BURSTS[-1] + 2 * GAP + TRAVEL


def pc(t):
    return f"{max(0.0, min(100.0, 100 * t / T)):.3f}%"


def keyframes(name, frames):
    """frames: list of (time, css) pairs, time in seconds."""
    body = "".join(f"{pc(t)}{{{css}}}" for t, css in sorted(frames, key=lambda f: f[0]))
    return f"@keyframes {name}{{{body}}}.{name}{{animation:{name} {T}s linear infinite}}"


def sprite(rows, colors):
    return "".join(
        f'<rect x="{c * PX}" y="{r * PX}" width="{PX}" height="{PX}" fill="{colors[ch]}"/>'
        for r, line in enumerate(rows) for c, ch in enumerate(line) if ch != "."
    )


def gun():
    return "".join(
        f'<rect x="{c}" y="{r}" width="1" height="1" fill="{AK_COLORS[ch]}"/>'
        for r, line in enumerate(AK) for c, ch in enumerate(line) if ch != "."
    )


def shots(bursts):
    return [b + i * GAP for b in bursts for i in range(3)]


def build_duel():
    css = [
        ".fb{transform-box:fill-box}",
        ".bob{animation:bob .8s steps(2,end) infinite}",
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}",
        ".tw{animation:tw 2.4s steps(2,end) infinite}",
        "@keyframes tw{0%,100%{opacity:1}50%{opacity:.2}}",
        ".bl{animation:bl .4s steps(1,end) infinite}",
        "@keyframes bl{0%{opacity:1}50%{opacity:0}}",
    ]
    fx = []

    def fighter(name, shooter_shots, hit_times, flip):
        x0 = P2_X + len(KNIGHT[0]) * PX if flip else P1_X
        flip_t = " scale(-1,1)" if flip else ""
        sx = -1 if flip else 1
        muzzle_x = x0 + sx * MUZZLE[0]
        muzzle_y = KY + MUZZLE[1]

        # recoil + muzzle flash
        rec, flash = [(0, "transform:translateX(0)")], [(0, "opacity:0")]
        for s in shooter_shots:
            rec += [(s - .001, "transform:translateX(0)"), (s, "transform:translateX(-1px)"),
                    (s + .06, "transform:translateX(0)")]
            flash += [(s - .001, "opacity:0"), (s, "opacity:1"), (s + .05, "opacity:1"), (s + .051, "opacity:0")]
        rec.append((T, "transform:translateX(0)"))
        flash.append((T, "opacity:0"))
        css.append(keyframes(f"rec{name}", rec))
        css.append(keyframes(f"fl{name}", flash))

        # getting hit: flash bright and stagger back
        hurt = [(0, "filter:brightness(1);transform:translateX(0)")]
        for h in hit_times:
            hurt += [(h - .001, "filter:brightness(1);transform:translateX(0)"),
                     (h, "filter:brightness(3);transform:translateX(-2px)"),
                     (h + .08, "filter:brightness(1);transform:translateX(0)")]
        hurt.append((T, "filter:brightness(1);transform:translateX(0)"))
        css.append(keyframes(f"hu{name}", hurt))

        mx, my = MUZZLE
        flash_svg = (
            f'<g class="fl{name}" opacity="0">'
            f'<rect x="{mx}" y="{my - 2}" width="3" height="5" fill="#ffd23f"/>'
            f'<rect x="{mx + 3}" y="{my - 1}" width="3" height="3" fill="#fff3a0"/>'
            f'<rect x="{mx + 6}" y="{my - .5}" width="2" height="2" fill="#fff"/>'
            f'<rect x="{mx + 1}" y="{my - 4}" width="2" height="2" fill="#ff8a00"/>'
            f'<rect x="{mx + 1}" y="{my + 3}" width="2" height="2" fill="#ff8a00"/></g>'
        )
        colors = P2_COLORS if flip else P1_COLORS
        body = (
            f'<g class="hu{name}"><g class="bob">{sprite(KNIGHT, colors)}'
            f'<g transform="translate({GUN_X},{GUN_Y})"><g class="rec{name}">{gun()}</g></g>'
            f'{flash_svg}</g></g>'
        )
        if flip:
            kw, kh = len(KNIGHT[0]) * PX, len(KNIGHT) * PX
            down = f"transform:translateY({-kw // 2}px) rotate(-90deg)"
            die = [(0, "transform:none"), (DEATH, "transform:none"), (DEATH + .35, down),
                   (T - .3, down), (T, "transform:none")]
            css.append(keyframes("die", die))
            css.append(f".die{{transform-origin:{kw // 2}px {kh}px}}")
            # the rifle leaves his hands and lands on the floor
            held = [(0, "opacity:1"), (DEATH + .1, "opacity:1"), (DEATH + .101, "opacity:0"),
                    (T - .3, "opacity:0"), (T - .299, "opacity:1"), (T, "opacity:1")]
            dropped = [(0, "opacity:0"), (DEATH + .1, "opacity:0"), (DEATH + .101, "opacity:1"),
                       (T - .3, "opacity:1"), (T - .299, "opacity:0"), (T, "opacity:0")]
            css.append(keyframes("held", held))
            css.append(keyframes("drop", dropped))
            body = body.replace(f'<g class="rec{name}">', f'<g class="held"><g class="rec{name}">', 1)
            body = body.replace(f'{gun()}</g></g>', f'{gun()}</g></g></g>', 1)
            body = f'<g class="die">{body}</g>'
            fx.append(f'<g class="drop" opacity="0" transform="translate({P2_X - 14},{GROUND - 6})">{gun()}</g>')
        knight = f'<g transform="translate({x0},{KY}){flip_t}">{body}</g>'
        return knight, muzzle_x, muzzle_y

    p1_shots, p2_shots = shots(P1_BURSTS), shots(P2_BURSTS)
    p1_hits = [s + TRAVEL for s in p2_shots]
    p2_hits = [s + TRAVEL for s in p1_shots]
    k1, m1x, m1y = fighter("A", p1_shots, p1_hits, False)
    k2, m2x, m2y = fighter("B", p2_shots, p2_hits, True)

    def bullets(prefix, shot_times, mx, my, target_x, direction):
        out = []
        dx = target_x - mx
        for i, s in enumerate(shot_times):
            n = f"{prefix}{i}"
            css.append(keyframes(f"bu{n}", [
                (0, "opacity:0;transform:translateX(0)"),
                (s, "opacity:0;transform:translateX(0)"),
                (s + .001, "opacity:1;transform:translateX(0)"),
                (s + TRAVEL, f"opacity:1;transform:translateX({dx}px)"),
                (s + TRAVEL + .001, f"opacity:0;transform:translateX({dx}px)"),
                (T, f"opacity:0;transform:translateX({dx}px)"),
            ]))
            out.append(
                f'<g transform="translate({mx},{my}) scale({direction},1)"><g class="bu{n}" opacity="0">'
                f'<rect x="-8" y="-.5" width="8" height="1" fill="#ff8a00" opacity=".55"/>'
                f'<rect x="0" y="-1" width="3" height="2" fill="#ffd23f"/>'
                f'<rect x="3" y="-.5" width="1" height="1" fill="#fff"/></g></g>'
            )
            # impact spark
            h = s + TRAVEL
            css.append(keyframes(f"sp{n}", [
                (0, "opacity:0;transform:scale(.2)"), (h, "opacity:0;transform:scale(.2)"),
                (h + .001, "opacity:1;transform:scale(.6)"), (h + .15, "opacity:0;transform:scale(1.6)"),
                (T, "opacity:0;transform:scale(.2)"),
            ]))
            out.append(
                f'<g transform="translate({target_x},{my})"><g class="fb sp{n}" opacity="0" '
                f'style="transform-origin:center">'
                f'<rect x="-1" y="-5" width="2" height="3" fill="#fff"/><rect x="-1" y="2" width="2" height="3" fill="#fff"/>'
                f'<rect x="-5" y="-1" width="3" height="2" fill="#ffd23f"/><rect x="2" y="-1" width="3" height="2" fill="#ffd23f"/>'
                f'<rect x="-1" y="-1" width="2" height="2" fill="#ff00cc"/></g></g>'
            )
            # ejected casing
            ex = mx - direction * 12
            fall = GROUND - (my - 1) - 1
            css.append(keyframes(f"ca{n}", [
                (0, "opacity:0;transform:translate(0,0)"), (s, "opacity:0;transform:translate(0,0)"),
                (s + .001, "opacity:1;transform:translate(0,0)"),
                (s + .15, f"opacity:1;transform:translate({-direction * 4}px,-6px)"),
                (s + .4, f"opacity:1;transform:translate({-direction * 7}px,{fall}px)"),
                (s + 1.2, f"opacity:0;transform:translate({-direction * 7}px,{fall}px)"),
                (T, f"opacity:0;transform:translate({-direction * 7}px,{fall}px)"),
            ]))
            out.append(
                f'<g transform="translate({ex},{my - 1})"><rect class="ca{n}" width="2" height="1" '
                f'fill="#ffd23f" opacity="0"/></g>'
            )
        return "".join(out)

    target_p2 = P2_X + 10
    target_p1 = P1_X + 2 * PX * 6 - 10
    fx.append(bullets("a", p1_shots, m1x, m1y, target_p2, 1))
    fx.append(bullets("b", p2_shots, m2x, m2y, target_p1, -1))

    # HP bars
    def hp(name, x, hits, color, origin):
        per = 1 / len(p1_shots) if name == "B" else 0.1  # P1 survives the duel
        frames, v = [(0, "transform:scaleX(1)")], 1.0
        for h in hits:
            frames += [(h - .001, f"transform:scaleX({v:.3f})")]
            v = max(0.0, v - per)
            frames += [(h, f"transform:scaleX({v:.3f})")]
        frames += [(T - .3, f"transform:scaleX({v:.3f})"), (T, "transform:scaleX(1)")]
        css.append(keyframes(f"hp{name}", frames))
        return (
            f'<rect x="{x - 1}" y="5" width="82" height="7" fill="#fff"/>'
            f'<rect x="{x}" y="6" width="80" height="5" fill="#3a0b3f"/>'
            f'<rect class="fb hp{name}" style="transform-origin:{origin}" x="{x}" y="6" width="80" height="5" fill="{color}"/>'
            f'<rect x="{x}" y="6" width="80" height="1" fill="#fff" opacity=".35"/>'
        )

    hud = hp("A", 18, p1_hits, "#ff00cc", "left") + hp("B", 122, p2_hits, "#00e5ff", "right")
    t, _ = text("P1", 3, 5, "#ff00cc")
    hud += t
    t, _ = text("P2", W - 14, 5, "#00e5ff")
    hud += t
    t, _ = text("VS", 104, 5, "#ffd23f")
    hud += f'<g class="tw">{t}</g>'

    # banners
    def banner(s, color, scale, y, start, end, blink=False):
        t, w = text(s, (W - (len(s) * 6 - 1) * scale) / 2, y, color, scale, "#0d0221")
        name = f"bn{len(css)}"
        css.append(keyframes(name, [(0, "opacity:0"), (start - .001, "opacity:0"), (start, "opacity:1"),
                                    (end, "opacity:1"), (end + .001, "opacity:0"), (T, "opacity:0")]))
        inner = f'<g class="bl">{t}</g>' if blink else t
        return f'<g class="{name}" opacity="0">{inner}</g>'

    banners = (
        banner("FIGHT!", "#ffd23f", 2, 26, 0.0, 0.9, True)
        + banner("K.O.", "#ff00cc", 3, 20, DEATH + .2, T - .4, True)
        + banner("P1 WINS", "#ffd23f", 1, 46, DEATH + 1.0, T - .4)
    )

    # backdrop: stars, striped sun, perspective floor
    rnd = random.Random(7)
    stars = "".join(
        f'<rect class="{"tw" if i % 3 == 0 else ""}" style="animation-delay:{rnd.random() * 2:.2f}s" '
        f'x="{rnd.randrange(W)}" y="{rnd.randrange(16, 50)}" width="1" height="1" fill="#ffffff" opacity=".7"/>'
        for i in range(28)
    )
    sun = (
        '<defs><linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ffd23f"/><stop offset="1" stop-color="#ff00cc"/></linearGradient>'
        f'<clipPath id="sky"><rect width="{W}" height="{GROUND}"/></clipPath></defs>'
        f'<g clip-path="url(#sky)"><circle cx="110" cy="{GROUND - 4}" r="20" fill="url(#sun)" opacity=".85"/>'
        + "".join(f'<rect x="88" y="{y}" width="44" height="{1 + i // 2}" fill="#0d0221"/>'
                  for i, y in enumerate(range(GROUND - 14, GROUND, 3)))
        + "</g>"
    )
    floor = [f'<rect x="0" y="{GROUND}" width="{W}" height="1" fill="#ff00cc"/>']
    for i, y in enumerate([GROUND + 3, GROUND + 7, GROUND + 12]):
        floor.append(f'<rect x="0" y="{y}" width="{W}" height="1" fill="#7a00ff" opacity="{.6 - i * .1:.1f}"/>')
    for k in range(-8, 9):
        floor.append(
            f'<line x1="{110 + k * 8}" y1="{GROUND}" x2="{110 + k * 40}" y2="{H}" stroke="#7a00ff" '
            f'stroke-width=".6" opacity=".45" shape-rendering="geometricPrecision"/>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 3}" height="{H * 3}" '
        f'shape-rendering="crispEdges"><style>{"".join(css)}</style>'
        f'<rect width="{W}" height="{H}" fill="#0d0221"/>{stars}{sun}{"".join(floor)}'
        f'{k1}{k2}{"".join(fx)}{hud}{banners}</svg>'
    )


def build_title():
    s = "VERSUS MODE"
    t, w = text(s, 12, 2, "#ffffff", 1, "#ff00cc")
    # crosshair icon
    icon = "".join(
        f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="#ff3b6b"/>'
        for x, y, ww, hh in [(4, 1, 3, 1), (4, 9, 3, 1), (1, 4, 1, 3), (9, 4, 1, 3),
                             (2, 2, 1, 1), (8, 2, 1, 1), (2, 8, 1, 1), (8, 8, 1, 1), (5, 5, 1, 1)]
    )
    dots = "".join(
        f'<rect x="{x}" y="5" width="2" height="2" fill="{["#ff00cc", "#7a00ff", "#00e5ff"][i % 3]}"/>'
        for i, x in enumerate(range(12 + w + 4, 219, 4))
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 12" width="660" height="36" '
        'shape-rendering="crispEdges"><style>.bob{animation:bob 1.2s steps(2,end) infinite}'
        '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}</style>'
        f'<rect x="0" y="0" width="220" height="12" fill="#0d0221"/><g class="bob">{icon}</g>{t}{dots}</svg>'
    )


if __name__ == "__main__":
    with open("assets/duel.svg", "w") as f:
        f.write(build_duel())
    with open("assets/t_versus.svg", "w") as f:
        f.write(build_title())
