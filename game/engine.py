#!/usr/bin/env python3
"""Pixel Arcade - a tiny community game for a GitHub profile README.

Visitors click an arrow in the README. That opens a pre-filled issue titled
"pixelgame: <direction>". A GitHub Action runs `python3 game/engine.py play`,
which applies the move, redraws game/board.svg and rewrites the README block.

Commands:
    init     create a fresh game, the button assets and the README block
    render   redraw board.svg and the README block from state.json
    play     apply one move from the GitHub issue event (used by the workflow)
"""
import json
import os
import random
import re
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets')
STATE_PATH = os.path.join(HERE, 'state.json')
BOARD_PATH = os.path.join(HERE, 'board.svg')
README_PATH = os.path.join(ROOT, 'README.md')

REPO = os.environ.get('GITHUB_REPOSITORY', 'serkancakmakk/serkancakmakk')
BRANCH = os.environ.get('GAME_BRANCH', 'main')
START_MARK, END_MARK = '<!--GAME:START-->', '<!--GAME:END-->'

COLS, ROWS, TILE = 16, 9, 8
HUD, BAR = 12, 10
W, H = COLS * TILE, HUD + ROWS * TILE + BAR
SCALE = 5

DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
WALLS = {(3, 2), (3, 3), (3, 4), (7, 5), (8, 5), (9, 5), (12, 1), (12, 2), (12, 3),
         (5, 7), (6, 7), (10, 7), (14, 5), (7, 1), (8, 1)}
PLAYER_START = (1, 4)
SLIME_START = [(14, 1), (14, 7)]
COIN_COUNT = 3
MAX_HEARTS = 3
HISTORY = 5

# ---------------------------------------------------------------- pixel font
RAW = {
    'A': '01110 10001 10001 11111 10001 10001 10001', 'B': '11110 10001 10001 11110 10001 10001 11110',
    'C': '01110 10001 10000 10000 10000 10001 01110', 'D': '11110 10001 10001 10001 10001 10001 11110',
    'E': '11111 10000 10000 11110 10000 10000 11111', 'F': '11111 10000 10000 11110 10000 10000 10000',
    'G': '01110 10001 10000 10111 10001 10001 01111', 'H': '10001 10001 10001 11111 10001 10001 10001',
    'I': '01110 00100 00100 00100 00100 00100 01110', 'J': '00111 00010 00010 00010 00010 10010 01100',
    'K': '10001 10010 10100 11000 10100 10010 10001', 'L': '10000 10000 10000 10000 10000 10000 11111',
    'M': '10001 11011 10101 10101 10001 10001 10001', 'N': '10001 11001 10101 10011 10001 10001 10001',
    'O': '01110 10001 10001 10001 10001 10001 01110', 'P': '11110 10001 10001 11110 10000 10000 10000',
    'Q': '01110 10001 10001 10001 10101 10010 01101', 'R': '11110 10001 10001 11110 10100 10010 10001',
    'S': '01111 10000 10000 01110 00001 00001 11110', 'T': '11111 00100 00100 00100 00100 00100 00100',
    'U': '10001 10001 10001 10001 10001 10001 01110', 'V': '10001 10001 10001 10001 10001 01010 00100',
    'W': '10001 10001 10001 10101 10101 11011 10001', 'X': '10001 01010 00100 00100 00100 01010 10001',
    'Y': '10001 10001 01010 00100 00100 00100 00100', 'Z': '11111 00001 00010 00100 01000 10000 11111',
    '0': '01110 10001 10011 10101 11001 10001 01110', '1': '00100 01100 00100 00100 00100 00100 01110',
    '2': '01110 10001 00001 00110 01000 10000 11111', '3': '11110 00001 00001 01110 00001 00001 11110',
    '4': '00010 00110 01010 10010 11111 00010 00010', '5': '11111 10000 11110 00001 00001 10001 01110',
    '6': '00110 01000 10000 11110 10001 10001 01110', '7': '11111 00001 00010 00100 01000 01000 01000',
    '8': '01110 10001 10001 01110 10001 10001 01110', '9': '01110 10001 10001 01111 00001 00010 01100',
    '.': '00000 00000 00000 00000 00000 01100 01100', '-': '00000 00000 00000 11111 00000 00000 00000',
    '_': '00000 00000 00000 00000 00000 00000 11111', '#': '01010 11111 01010 01010 11111 01010 01010',
    '!': '00100 00100 00100 00100 00100 00000 00100', ':': '00000 01100 01100 00000 01100 01100 00000',
    '?': '01110 10001 00001 00110 00100 00000 00100', ' ': '00000 00000 00000 00000 00000 00000 00000',
}
FONT = {k: v.split() for k, v in RAW.items()}


def clean(t):
    """Uppercase and replace anything the pixel font cannot draw."""
    return ''.join(c if c in FONT else '_' for c in str(t).upper())


def tw(t):
    return len(t) * 6 - 1


def text(t, x, y, s, color, cls=''):
    t = clean(t)
    rows = [''.join(FONT[ch][r] + '0' for ch in t) for r in range(7)]
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == '1':
                e = c
                while e < len(row) and row[e] == '1':
                    e += 1
                out.append(f'<rect x="{x+c*s}" y="{y+r*s}" width="{(e-c)*s}" height="{s}"/>')
                c = e
            else:
                c += 1
    return f'<g fill="{color}"{cls}>' + ''.join(out) + '</g>'


def sprite(grid, pal, x, y, cls=''):
    out = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch != '.':
                e = c
                while e < len(row) and row[e] == ch:
                    e += 1
                out.append(f'<rect x="{x+c}" y="{y+r}" width="{e-c}" height="1" fill="{pal[ch]}"/>')
                c = e
            else:
                c += 1
    return f'<g{cls}>' + ''.join(out) + '</g>'


CSS = '''<style>
.tw{animation:tw 3s steps(2,end) infinite}
@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}
.bob{animation:bob 1.2s steps(2,end) infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}
.blink{animation:blink 1s steps(1,end) infinite}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
</style>'''


def svg(w, h, scale, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w*scale}" height="{h*scale}" '
            f'shape-rendering="crispEdges">{CSS}{body}</svg>')


def bob(d=0.0):
    return f' class="bob" style="animation-delay:{d}s"'


# ------------------------------------------------------------------ sprites
PLAYER = ["..hhhh..", ".hhhhhh.", ".hssssh.", ".hesseh.", "..ssss..", "sbbbbbbs", ".bbyybb.", "..p..p.."]
PLAYER_PAL = dict(h='#4a2c1a', s='#f2c9a0', e='#111111', b='#7a00ff', y='#ff00cc', p='#2b3a67')
SLIME = ["........", "..gggg..", ".gggggg.", "gwkggwkg", "gggggggg", "gggggggg", "gggggggg", ".dd..dd."]
SLIME_PAL = dict(g='#39e07a', d='#1d9a52', w='#ffffff', k='#111111')
COIN = ["..dddd..", ".dyyyyd.", "dyyywyyd", "dyyyyyyd", "dyyyyyyd", "dyyyyyyd", ".dyyyyd.", "..dddd.."]
COIN_PAL = dict(d='#b8860b', y='#ffd700', w='#fff4b0')
HEART = [".rr...rr.", "rwrr.rrrr", "rrrrrrrrr", "rrrrrrrrr", ".rrrrrrr.", "..rrrrr..", "...rrr...", "....r...."]
HEART_PAL = dict(r='#ff3b6b', w='#ffd1dc')
HEART_OFF = dict(r='#3a1a3a', w='#3a1a3a')


def wall_tile(x, y):
    b = [f'<rect x="{x}" y="{y}" width="8" height="8" fill="#3b2a73"/>',
         f'<rect x="{x}" y="{y}" width="8" height="1" fill="#6a4fc9"/>',
         f'<rect x="{x}" y="{y+3}" width="8" height="1" fill="#241552"/>',
         f'<rect x="{x}" y="{y+7}" width="8" height="1" fill="#241552"/>',
         f'<rect x="{x+3}" y="{y}" width="1" height="3" fill="#241552"/>',
         f'<rect x="{x+6}" y="{y+4}" width="1" height="3" fill="#241552"/>',
         f'<rect x="{x+1}" y="{y+4}" width="1" height="1" fill="#5a3fa0"/>']
    return ''.join(b)


# -------------------------------------------------------------------- state
def new_round(st, seed):
    rng = random.Random(seed)
    st['hearts'] = MAX_HEARTS
    st['score'] = 0
    st['player'] = list(PLAYER_START)
    st['slimes'] = [list(s) for s in SLIME_START]
    st['coins'] = []
    for _ in range(COIN_COUNT):
        st['coins'].append(list(pick_cell(st, rng, min_dist=3)))


def default_state():
    st = {'move': 0, 'rounds': 0, 'total_coins': 0, 'high_score': 0, 'best_by': '',
          'players': {}, 'history': [], 'flash': None}
    new_round(st, 1)
    return st


def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(st):
    with open(STATE_PATH, 'w') as f:
        json.dump(st, f, indent=1, sort_keys=True)
        f.write('\n')


def passable(c):
    x, y = c
    return 0 <= x < COLS and 0 <= y < ROWS and (x, y) not in WALLS


def pick_cell(st, rng, min_dist=0):
    occ = {tuple(c) for c in st['coins']} | {tuple(s) for s in st['slimes']} | {tuple(st['player'])}
    px, py = st['player']
    cells = [(x, y) for x in range(COLS) for y in range(ROWS)
             if (x, y) not in WALLS and (x, y) not in occ and abs(x - px) + abs(y - py) >= min_dist]
    if not cells:
        cells = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in WALLS and (x, y) not in occ]
    return rng.choice(cells)


def sgn(n):
    return (n > 0) - (n < 0)


def slime_step(s, p, others, rng):
    if rng.random() < 0.3:
        return s
    sx, sy = s
    if rng.random() < 0.65:
        dx, dy = p[0] - sx, p[1] - sy
        order = [(sgn(dx), 0), (0, sgn(dy))] if abs(dx) >= abs(dy) else [(0, sgn(dy)), (sgn(dx), 0)]
        opts = [o for o in order if o != (0, 0)]
    else:
        opts = list(DIRS.values())
        rng.shuffle(opts)
    for ox, oy in opts:
        n = (sx + ox, sy + oy)
        if passable(n) and n not in others:
            return n
    return s


def apply_move(st, direction, user):
    """Apply one move in place. Returns a short note describing what happened."""
    st['move'] += 1
    rng = random.Random(st['move'] * 7919 + 13)
    st['flash'] = None
    pl = st['players'].setdefault(user, {'moves': 0, 'coins': 0})
    pl['moves'] += 1
    notes = []

    dx, dy = DIRS[direction]
    target = (st['player'][0] + dx, st['player'][1] + dy)
    if passable(target):
        st['player'] = list(target)
    else:
        notes.append('BONK')
    player = tuple(st['player'])

    hit = False
    if list(player) in st['coins']:
        st['coins'].remove(list(player))
        st['score'] += 1
        st['total_coins'] += 1
        pl['coins'] += 1
        st['coins'].append(list(pick_cell(st, rng, min_dist=3)))
        notes.append('COIN')

    slimes = [tuple(s) for s in st['slimes']]
    for i, s in enumerate(slimes):
        if s == player:
            hit = True
            st['slimes'][i] = list(pick_cell(st, rng, min_dist=6))
    slimes = [tuple(s) for s in st['slimes']]
    for i in range(len(slimes)):
        others = {slimes[j] for j in range(len(slimes)) if j != i}
        slimes[i] = slime_step(slimes[i], player, others, rng)
        if slimes[i] == player:
            hit = True
            st['slimes'][i] = list(pick_cell(st, rng, min_dist=6))
            slimes[i] = tuple(st['slimes'][i])
        else:
            st['slimes'][i] = list(slimes[i])

    if hit:
        st['hearts'] -= 1
        notes.append('HIT')

    if st['hearts'] <= 0:
        final = st['score']
        new_best = final > st['high_score']
        if new_best:
            st['high_score'] = final
            st['best_by'] = user
        st['rounds'] += 1
        st['flash'] = {'score': final, 'best': new_best}
        new_round(st, st['move'] * 31 + 7)
        notes.append('OVER')

    st['history'].append({'user': user, 'dir': direction, 'note': ' '.join(notes)})
    st['history'] = st['history'][-HISTORY:]
    return notes


# ---------------------------------------------------------------- rendering
def render_board(st):
    b = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0d0221"/>']
    top = HUD
    b.append(f'<rect x="0" y="{top}" width="{COLS*TILE}" height="{ROWS*TILE}" fill="#150c30"/>')
    alt = []
    for y in range(ROWS):
        for x in range(COLS):
            if (x + y) % 2:
                alt.append(f'<rect x="{x*TILE}" y="{top+y*TILE}" width="8" height="8"/>')
    b.append('<g fill="#1b1040">' + ''.join(alt) + '</g>')
    for (x, y) in sorted(WALLS):
        b.append(wall_tile(x * TILE, top + y * TILE))
    for i, (x, y) in enumerate(st['coins']):
        b.append(sprite(COIN, COIN_PAL, x * TILE, top + y * TILE, bob(round(i * .3, 1))))
    for i, (x, y) in enumerate(st['slimes']):
        b.append(sprite(SLIME, SLIME_PAL, x * TILE, top + y * TILE, bob(round(i * .5, 1))))
    px, py = st['player']
    b.append(sprite(PLAYER, PLAYER_PAL, px * TILE, top + py * TILE, bob(0)))

    # HUD
    b.append(f'<rect x="0" y="{top-1}" width="{W}" height="1" fill="#ff00cc"/>')
    for i in range(MAX_HEARTS):
        pal = HEART_PAL if i < st['hearts'] else HEART_OFF
        b.append(sprite(HEART, pal, 2 + i * 10, 2))
    b.append(text(f'SCORE {st["score"]}', 36, 3, 1, '#ffd166'))
    best = f'BEST {st["high_score"]}'
    b.append(text(best, W - 2 - tw(best), 3, 1, '#00e5ff'))

    # bottom bar
    by = top + ROWS * TILE
    b.append(f'<rect x="0" y="{by}" width="{W}" height="1" fill="#7a00ff"/>')
    b.append(text(f'#{st["move"]}', 2, by + 2, 1, '#ff00cc'))
    if st['history']:
        last = st['history'][-1]
        msg = f'{last["user"][:9]} {last["dir"]}'
        b.append(text(msg, W - 2 - tw(clean(msg)), by + 2, 1, '#00ff9c'))
    else:
        msg = 'PRESS A BUTTON'
        b.append(text(msg, W - 2 - tw(msg), by + 2, 1, '#00ff9c', ' class="blink"'))

    if st.get('flash'):
        f = st['flash']
        b.append(f'<rect x="8" y="{top+16}" width="{W-16}" height="40" fill="#0d0221" fill-opacity=".92"/>')
        b.append(f'<rect x="8" y="{top+16}" width="{W-16}" height="1" fill="#ff00cc"/>')
        b.append(f'<rect x="8" y="{top+55}" width="{W-16}" height="1" fill="#ff00cc"/>')
        t = 'GAME OVER'
        b.append(text(t, (W - tw(t) * 2) // 2, top + 21, 2, '#ff3b6b'))
        t = f'SCORE {f["score"]}' + ('  NEW BEST!' if f['best'] else '')
        b.append(text(t, (W - tw(clean(t))) // 2, top + 38, 1, '#ffd166'))
        t = 'NEW ROUND'
        b.append(text(t, (W - tw(t)) // 2, top + 47, 1, '#00ff9c', ' class="blink"'))
    return svg(W, H, SCALE, ''.join(b))


def arrow_grid(direction):
    up = ["...xx...", "..xxxx..", ".xxxxxx.", "xxxxxxxx", "..xxxx..", "..xxxx..", "..xxxx..", "..xxxx.."]
    if direction == 'up':
        return up
    if direction == 'down':
        return up[::-1]
    left = rot_left(up)
    if direction == 'left':
        return left
    return [row[::-1] for row in left]


def rot_left(grid):
    n = len(grid)
    return [''.join(grid[r][n - 1 - c] for r in range(n)) for c in range(n)]


def button_svg(direction):
    g = arrow_grid(direction)
    b = ['<rect x="0" y="0" width="16" height="16" fill="#00e5ff"/>',
         '<rect x="1" y="1" width="14" height="14" fill="#0d0221"/>',
         '<rect x="2" y="2" width="12" height="12" fill="#ff00cc"/>',
         '<rect x="3" y="3" width="10" height="10" fill="#241347"/>']
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == 'x':
                b.append(f'<rect x="{4+c}" y="{4+r}" width="1" height="1" fill="#00ff9c"/>')
    return svg(16, 16, 4, ''.join(b))


def title_svg(t):
    w, h = 220, 12
    b = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="#0d0221"/>',
         sprite(COIN, COIN_PAL, 1, 2, bob(0)),
         text(t, 13, 3, 1, '#ff00cc'), text(t, 12, 2, 1, '#ffffff')]
    cols = ['#ff00cc', '#7a00ff', '#00e5ff']
    for i, x in enumerate(range(12 + tw(t) + 4, w - 2, 4)):
        b.append(f'<rect x="{x}" y="5" width="2" height="2" fill="{cols[i % 3]}"/>')
    return svg(w, h, 3, ''.join(b))


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def write_static_assets():
    for d in DIRS:
        write(os.path.join(ASSETS, f'btn_{d}.svg'), button_svg(d))
    write(os.path.join(ASSETS, 't_game.svg'), title_svg('PIXEL ARCADE'))


def move_link(direction):
    title = quote(f'pixelgame: {direction}')
    body = quote('Just press "Submit new issue". Your move is played automatically (takes about 30 seconds).')
    return f'https://github.com/{REPO}/issues/new?title={title}&body={body}'


def readme_block(st):
    board = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/game/board.svg?m={st["move"]}'
    btn = lambda d: f'<a href="{move_link(d)}"><img src="assets/btn_{d}.svg" width="72" alt="{d.upper()}"/></a>'
    lines = [
        '<div align="center">', '',
        '<img src="assets/t_game.svg" alt="PIXEL ARCADE" width="100%"/>', '',
        '<sub>Collect <b>coins</b>, dodge the <b>slimes</b>. Everyone who visits plays the <b>same</b> game together.</sub>', '',
        f'<img src="{board}" width="640" alt="Pixel Arcade board"/>', '',
        btn('up'), '<br/>', btn('left'), btn('down'), btn('right'), '',
        '<sub>Click an arrow, then press <b>Submit new issue</b> (GitHub login needed). '
        'The board updates in about 30 seconds, refresh the page.</sub>', '',
        f'<sub>MOVES <b>{st["move"]}</b> · ROUNDS <b>{st["rounds"]}</b> · COINS <b>{st["total_coins"]}</b> · '
        f'BEST <b>{st["high_score"]}</b>' + (f' by <a href="https://github.com/{st["best_by"]}">@{st["best_by"]}</a>' if st['best_by'] else '') + '</sub>',
        '', '</div>', '',
    ]
    top = sorted(st['players'].items(), key=lambda kv: (-kv[1]['coins'], -kv[1]['moves'], kv[0]))[:5]
    if top:
        lines += ['<div align="center">', '', '| # | PLAYER | COINS | MOVES |', '|:-:|:------:|:-----:|:-----:|']
        for i, (name, p) in enumerate(top, 1):
            lines.append(f'| {i} | [@{name}](https://github.com/{name}) | {p["coins"]} | {p["moves"]} |')
        lines += ['', '</div>', '']
    if st['history']:
        lines += ['<details>', '<summary><b>▶ LAST MOVES</b></summary>', '', '<div align="center">', '',
                  '| PLAYER | MOVE | RESULT |', '|:------:|:----:|:------:|']
        for h in reversed(st['history']):
            lines.append(f'| [@{h["user"]}](https://github.com/{h["user"]}) | {h["dir"].upper()} | {h["note"] or "-"} |')
        lines += ['', '</div>', '', '</details>', '']
    return '\n'.join(lines)


def update_readme(st):
    with open(README_PATH) as f:
        src = f.read()
    pat = re.compile(re.escape(START_MARK) + r'.*?' + re.escape(END_MARK), re.S)
    if not pat.search(src):
        raise SystemExit('README.md is missing the game markers')
    new = START_MARK + '\n' + readme_block(st) + '\n' + END_MARK
    with open(README_PATH, 'w') as f:
        f.write(pat.sub(lambda m: new, src))


def render_all(st):
    write(BOARD_PATH, render_board(st))
    update_readme(st)


# --------------------------------------------------------------------- CLI
def result_dir():
    return os.environ.get('RUNNER_TEMP') or '/tmp'


def finish(number, comment):
    write(os.path.join(result_dir(), 'pixelgame_comment.md'), comment + '\n')
    write(os.path.join(result_dir(), 'pixelgame_number.txt'), str(number) + '\n')


def cmd_play():
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        ev = json.load(f)
    issue = ev.get('issue') or {}
    number = issue.get('number')
    if not isinstance(number, int):
        raise SystemExit('no issue number in event')
    title = (issue.get('title') or '').strip().lower()
    user = (issue.get('user') or {}).get('login') or ''
    m = re.fullmatch(r'pixelgame:\s*(up|down|left|right)', title)
    if not m or not re.fullmatch(r'[A-Za-z0-9-]{1,39}', user):
        finish(number, 'Sorry, I could not read that move. Use one of the arrow buttons in the README.')
        return
    st = load_state()
    notes = apply_move(st, m.group(1), user)
    save_state(st)
    render_all(st)
    msgs = {'COIN': 'You grabbed a coin!', 'HIT': 'A slime got you, -1 heart.', 'BONK': 'Bonk, a wall is in the way.',
            'OVER': 'Game over! A new round has started.'}
    extra = ' '.join(msgs[n] for n in notes if n in msgs)
    finish(number, f'Move **{m.group(1)}** played by @{user}. {extra}\n\n'
                   f'Score: {st["score"]} · Hearts: {st["hearts"]} · Total moves: {st["move"]}\n\n'
                   f'Go back to the profile and refresh to see the board.')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'init':
        st = default_state()
        save_state(st)
        write_static_assets()
        render_all(st)
    elif cmd == 'render':
        write_static_assets()
        render_all(load_state())
    elif cmd == 'play':
        cmd_play()
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
