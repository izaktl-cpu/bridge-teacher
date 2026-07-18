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

def run(name, hands, dealer, expected_ns, expected_ew=None):
    c = dict(cfg)
    auction, players = compute_auction(hands, dealer, c)
    ns_bids = [auction[i] for i in range(len(auction)) if players[i] in ('N','S')]
    ew_bids = [auction[i] for i in range(len(auction)) if players[i] in ('E','W') and auction[i] != 'פס']
    ok = (ns_bids == expected_ns)
    if expected_ew is not None:
        ok = ok and (ew_bids == expected_ew)
    if ok:
        print(f'[OK] {name}')
    else:
        print(f'[FAIL] {name}')
        if ns_bids != expected_ns:
            print(f'  NS צפוי:   {expected_ns}')
            print(f'  NS קיבלנו: {ns_bids}')
        if expected_ew and ew_bids != expected_ew:
            print(f'  EW צפוי:   {expected_ew}')
            print(f'  EW קיבלנו: {ew_bids}')
        errors.append(name)

# ── TEST 1: 1♥ — E:1♠ — S:2♥ (תמיכה חרף אוברקול) ───────────────────────────
run('1♥ — 1♠ — 2♥ (תמיכה)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),     # 14 נק', 5♥
     'S': make_hand('K52','J73','Q762','652'),      # 7 נק', 3♥
     'E': make_hand('AQJ76','T6','T85','Q43'),      # 10 נק', 5♠ — אוברקול
     'W': make_hand('T98','982','A94','AKT87')},
    'N',
    expected_ns=['1♥','2♥','פס'],
    expected_ew=['1♠'])

# ── TEST 2: 1♦ — E:1♥ — S:1♠ (ספייד עדיין זמין) ────────────────────────────
# 1♠ גבוה מ-1♥ → זמין. N עם 4♠ מעלה ל-2♠
run('1♦ — 1♥ — 1♠ (ספייד זמין)',
    {'N': make_hand('KJ43','4','AQJ92','Q32'),     # 13 נק', 5♦, 4♠
     'S': make_hand('AJ86','832','Q74','975'),      # 7 נק', 4♠
     'E': make_hand('52','AKJ76','T63','KJ4'),      # 12 נק', 5♥ — אוברקול
     'W': make_hand('T97','QT95','85','AT86')},     # 6 נק', אין 5+ בצבע
    'N',
    expected_ns=['1♦','1♠','2♠','פס'],
    expected_ew=['1♥'])

# ── TEST 3: 1♣ — E:1♠ — S:X (♥ חסום, אין עצור → Negative double) ──────────
# S עם 4♥, 1♥ חסום (< 1♠), אין עצור ♠ → X (נגטיב דאבל). N יש 3♥ → 1NT
run('1♣ — 1♠ — X(♥ חסום) — 1NT',
    {'N': make_hand('54','QT3','K32','AKJ43'),     # 13 נק', 5♣, 3♥ → 1NT (אין 4♥)
     'S': make_hand('32','KJ54','Q762','652'),      # 6 נק', 4♥, אין עצור ♠ → X
     'E': make_hand('KQJ76','A6','T85','QJ4'),      # 12 נק', 5♠ — אוברקול
     'W': make_hand('AT98','9872','AJ94','T7')},
    'N',
    expected_ns=['1♣','X','1NT','פס'],
    expected_ew=['1♠'])

# ── TEST 4: 1♥ — E:1♠ — S:1NT (עם עצור בספייד) ──────────────────────────────
# S עם Kxx בספייד → עצור תקין. מכריז 1NT
run('1♥ — 1♠ — 1NT (עצור)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),     # 14 נק', 5♥
     'S': make_hand('KQ2','J3','Q765','T987'),      # 8 נק', עצור ♠ (KQ)
     'E': make_hand('AJ976','T6','T84','KQ3'),      # 10 נק', 5♠ — אוברקול
     'W': make_hand('T85','9872','A9','A642')},     # 8 נק'
    'N',
    expected_ns=['1♥','1NT','2♥','פס'],
    expected_ew=['1♠'])

# ── TEST 5: 1♥ — E:1♠ — S:פס (אין עצור, נק' < 6) ────────────────────────────
run('1♥ — 1♠ — פס (חלש)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),     # 14 נק', 5♥
     'S': make_hand('T62','J3','Q762','T654'),      # 4 נק' בלבד → פס
     'E': make_hand('AQJ76','T6','T85','Q43'),      # 10 נק', 5♠ — אוברקול
     'W': make_hand('K98','9872','AK94','AK87')},
    'N',
    expected_ns=['1♥','פס','פס'],
    expected_ew=['1♠'])

# ── סיכום ─────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות התשובות לאוברקול עברו!')
