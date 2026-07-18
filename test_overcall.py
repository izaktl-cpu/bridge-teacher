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

# ── TEST 1: E מכריז אוברקול 1♠ אחרי 1♥ ──────────────────────────────────────
# N פותח 1♥, E עם 5♠ ו-10 נק' → אוברקול 1♠
run('1♥ — E אוברקול 1♠',
    {'N': make_hand('43','AKQ54','KJ32','J5'),     # 14 נק', 5♥
     'S': make_hand('K52','J73','Q76','7652'),      # 6 נק', 3♥
     'E': make_hand('AQJ76','T6','T85','Q43'),      # 10 נק', 5♠ (AQJ=8 נק' בספייד)
     'W': make_hand('T98','982','A94','AKT8')},     # 12 נק'
    'N',
    expected_ns=['1♥','2♥','פס'],
    expected_ew=['1♠'])

# ── TEST 2: E פס (אין 5+ קלפים) ──────────────────────────────────────────────
run('1♥ — E פס (רק 4♠)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),     # 14 נק', 5♥
     'S': make_hand('K52','J73','Q76','7652'),      # 6 נק', 3♥
     'E': make_hand('AQJ7','T6','T85','Q432'),      # 10 נק', 4♠ בלבד
     'W': make_hand('T986','982','A94','AKT8')},
    'N',
    expected_ns=['1♥','2♥','פס'],
    expected_ew=[])

# ── TEST 3: E פס (פחות מ-5 נק' גבוהות בסדרה) ──────────────────────────────────
run('1♥ — E פס (פחות מ-5 נק\' גבוהות בספייד)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),     # 14 נק', 5♥
     'S': make_hand('K52','J73','Q76','7652'),      # 6 נק', 3♥
     'E': make_hand('T9876','T6','AK5','Q43'),      # 10 נק', 5♠ אבל רק 0 נק' גבוהות בספייד
     'W': make_hand('AQJ','982','T874','AKT8')},
    'N',
    expected_ns=['1♥','2♥','פס'],
    expected_ew=[])

# ── TEST 4: W מכריז אוברקול 2♣ אחרי 1♠ (רמה 2, 12+ נק') ────────────────────
# N פותח 1♠, E פס, S עונה, W עם 5♣ חזק → אוברקול 2♣
run('1♠ — W אוברקול 2♣ (רמה 2)',
    {'N': make_hand('AKJ54','K32','Q32','54'),     # 13 נק', 5♠
     'S': make_hand('32','Q65','K542','Q762'),      # 7 נק', מאוזן
     'E': make_hand('Q76','AT9','J76','KJ93'),      # 12 נק', אין 5+ בצבע
     'W': make_hand('T98','J84','AT8','AKT98')},    # 14 נק', 5♣ (AKT=8 נק' גבוהות)
    'N',
    expected_ns=['1♠','1NT','פס','פס'],
    expected_ew=['2♣'])

# ── סיכום ─────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות האוברקול עברו!')
