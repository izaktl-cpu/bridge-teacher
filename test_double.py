# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'D:/bridge-teacher')

from bidding_engine import compute_auction, hcp, sl
from bridge_teacher import cfg

cfg['majorLen']=5; cfg['ntMin']=15; cfg['ntMax']=17; cfg['minorLen']=3

errors = []

def make_hand(spades='', hearts='', diamonds='', clubs=''):
    hand = []
    for suit, cards in [('♠',spades),('♥',hearts),('♦',diamonds),('♣',clubs)]:
        for r in cards:
            hand.append({'s':suit,'r':r})
    return hand

def run(name, hands, dealer, expected_ew):
    c = dict(cfg)
    auction, players = compute_auction(hands, dealer, c)
    ew_bids = [auction[i] for i in range(len(auction))
               if players[i] in ('E','W') and auction[i] != 'פס']
    if ew_bids == expected_ew:
        print(f'[OK] {name}')
    else:
        print(f'[FAIL] {name}')
        print(f'  EW צפוי:   {expected_ew}')
        print(f'  EW קיבלנו: {ew_bids}')
        errors.append(name)

# ── TEST 1: 1♥ — E:X — W:1♠ (S פס, W חלש) ───────────────────────────────────
# S חלש מדי → פס. W עם 5♠ יכול לכריז ברמה 1
run('1♥ — E:X — W:1♠ (S פס, W חלש)',
    {'N': make_hand('743','AKQ54','K32','J5'),    # 13 נק', 5♥
     'S': make_hand('T96','32','8765','9876'),    # 0 נק' → פס
     'E': make_hand('KJ54','J','AQ54','KJ3'),     # 15 נק', 4♠,1♥,4♦,3♣ → X
     'W': make_hand('QT876','976','T9','T84')},   # 2 נק', 5♠ → 1♠
    'N', ['X','1♠'])

# ── TEST 2: 1♥ — E:X — W:1NT (עם עצור ♥, 8+ נק') ────────────────────────────
run('1♥ — E:X — W:1NT (עצור ♥)',
    {'N': make_hand('543','AKQ54','K32','J5'),    # 13 נק', 5♥
     'S': make_hand('AT98','76','QT9','AT87'),    # 8 נק'
     'E': make_hand('KJ54','J','AQ54','KJ3'),     # 15 נק' → X
     'W': make_hand('Q76','KT9','J876','Q32')},   # 8 נק', Kxx בלב → 1NT
    'N', ['X','1NT'])

# ── TEST 3: 1♥ — E:X — W:2♠ (S פס, W עם 9+ קופץ) ────────────────────────────
run('1♥ — E:X — W:2♠ (S פס, קפיצה 9+)',
    {'N': make_hand('743','AKQ54','K32','J5'),    # 13 נק', 5♥
     'S': make_hand('T96','32','8765','9876'),    # 0 נק' → פס
     'E': make_hand('KJ54','J','AQ54','KJ3'),     # 15 נק' → X
     'W': make_hand('QJT86','T9','7','AQ543')},  # 9 נק', 5♠ → 2♠
    'N', ['X','2♠'])

# ── TEST 4: 1♠ — E:X — W:2♥ (פותח 6♠, לא מאוזן) ────────────────────────────
# N עם 5332 יפתח 1NT — צריך 6♠ כדי לפתוח 1♠
run('1♠ — E:X — W:2♥',
    {'N': make_hand('AKQ543','K2','Q32','J4'),    # 15 נק', 6♠ → 1♠
     'S': make_hand('J76','J54','JT9','Q876'),    # 4 נק' → פס
     'E': make_hand('J','KJ54','AJ54','KQ3'),     # 15 נק', 1♠,4♥,4♦,3♣ → X
     'W': make_hand('T92','QT876','K76','T8')},   # 5 נק', 5♥ → 2♥
    'N', ['X','2♥'])

# ── TEST 5: 1♥ — E:פס (3♥ — לא מתאים לדאבל) ─────────────────────────────────
run('1♥ — E:פס (3♥, אין דאבל)',
    {'N': make_hand('743','AKQ54','K32','J5'),    # 13 נק', 5♥
     'S': make_hand('A92','T76','JT9','Q876'),    # 7 נק'
     'E': make_hand('KJ4','KJ4','AQ54','KJ3'),    # 18 נק', 3♥ → לא יכול לדאבל
     'W': make_hand('QT876','932','876','T84')},  # 1 נק'
    'N', [])

# ── סיכום ─────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות הדאבל עברו!')
