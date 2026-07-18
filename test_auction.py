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

def run(name, hands, dealer, expected_ns):
    c = dict(cfg)
    auction, players = compute_auction(hands, dealer, c)
    ns_bids = [auction[i] for i in range(len(auction)) if players[i] in ('N','S')]
    if ns_bids == expected_ns:
        print(f'[OK] {name}')
    else:
        print(f'[FAIL] {name}')
        print(f'  צפוי:   {expected_ns}')
        print(f'  קיבלנו: {ns_bids}')
        errors.append(name)

# ── TEST 1: 1NT → פס (S חלש מדי 5 נק') ──────────────────────────────────────
run('1NT → פס (S חלש)',
    {'N': make_hand('AK3','KQ4','A432','543'),    # 15 נק' מאוזן
     'S': make_hand('752','5432','876','J76'),     # 5 נק'
     'E': make_hand('J964','J976','Q95','Q82'),
     'W': make_hand('QT85','AT8','KJT','AKT')},
    'N', ['1NT','פס'])

# ── TEST 2: 1NT → 3NT (S חזק 13 נק') ────────────────────────────────────────
# אחרי 3NT הפותח עושה פס — זה נכון
run('1NT → 3NT → פס',
    {'N': make_hand('AK3','KQ4','A432','543'),    # 15 נק' מאוזן
     'S': make_hand('Q52','A32','KJ76','Q62'),    # 13 נק' מאוזן
     'E': make_hand('J964','J976','Q95','J87'),
     'W': make_hand('T87','T85','T8','AKT98')},
    'N', ['1NT','3NT','פס'])

# ── TEST 3: 1♥ → 4♥ → פס (תמיכה חזקה) ──────────────────────────────────────
# N: 14 נק', 5♥, לא מאוזן (5422) — לא יפתח 1NT
run('1♥ → 4♥ → פס (תמיכה חזקה)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),    # 14 נק', 5♥, 4♦ — לא מאוזן
     'S': make_hand('KQ2','J73','AQ4','KQ32'),    # 17 נק', 3♥
     'E': make_hand('J9765','T96','T65','T8'),
     'W': make_hand('AT8','82','987','A9764')},
    'N', ['1♥','4♥','פס'])

# ── TEST 4: 1♥ → 2♥ → פס (תמיכה חלשה) ──────────────────────────────────────
run('1♥ → 2♥ → פס (תמיכה חלשה)',
    {'N': make_hand('43','AKQ54','KJ32','J5'),    # 14 נק', 5♥
     'S': make_hand('K52','J73','Q76','7652'),    # 6 נק', 3♥
     'E': make_hand('QJ976','T96','T85','T8'),
     'W': make_hand('AT8','82','A984','AKQ9')},
    'N', ['1♥','2♥','פס'])

# ── TEST 5: 1♠ → 1NT → פס ────────────────────────────────────────────────────
# S: 7 נק', מאוזן, אין 4 מיגור
run('1♠ → 1NT → פס',
    {'N': make_hand('AKJ54','K32','Q32','54'),    # 13 נק', 5♠, 5332 (13<15 → לא NT)
     'S': make_hand('32','Q65','K542','Q762'),    # 7 נק', מאוזן, אין 4 מיגור
     'E': make_hand('Q976','AT9','J76','KJ3'),
     'W': make_hand('T8','J84','AT98','AT98')},
    'N', ['1♠','1NT','פס'])

# ── TEST 6: 1♦ → 1♥ → 2♥ → פס ───────────────────────────────────────────────
# S: 13 נק', 5♦, 3♥ (13<15 → לא NT)
run('1♦ → 1♥ → 2♥ → פס',
    {'N': make_hand('K32','KJ54','32','Q654'),    # 9 נק', 4♥
     'S': make_hand('54','QT3','AKJ43','K32'),    # 13 נק', 5♦, 3♥
     'E': make_hand('QJ976','A876','Q6','J8'),
     'W': make_hand('AT8','92','T87','AT987')},
    'S', ['1♦','1♥','2♥','פס'])

# ── TEST 7: 1♦ → 1♠ → 1NT → 2NT → פס (עקרון ההזמנה) ────────────────────────
# S: 13 נק' 5♦, N: 11 נק' 5♠. N מזמין ב-2NT, S עם 13 עושה פס
run('1♦ → 1♠ → 1NT → 2NT → פס (הזמנה)',
    {'N': make_hand('AKQ54','Q32','32','543'),    # 11 נק', 5♠
     'S': make_hand('32','K54','AKJ54','Q32'),    # 13 נק', 5♦
     'E': make_hand('J976','AT9','Q76','KJ8'),
     'W': make_hand('T8','J876','T8','AT976')},
    'S', ['1♦','1♠','1NT','2NT','פס'])

# ── TEST 8: 1♦ → 1♠ → 1NT → 3NT → פס ───────────────────────────────────────
# N: 14 נק' → מכריז 3NT ישירות, S עושה פס
run('1♦ → 1♠ → 1NT → 3NT → פס',
    {'N': make_hand('AKQ54','KQ2','32','543'),    # 14 נק', 5♠
     'S': make_hand('32','K54','AKJ54','Q32'),    # 13 נק', 5♦
     'E': make_hand('J976','AT9','Q76','KJ8'),
     'W': make_hand('T8','J876','T8','AT976')},
    'S', ['1♦','1♠','1NT','3NT','פס'])

# ── TEST 9: 1♣ → 1♥ → 2♥ → פס ───────────────────────────────────────────────
# S: 13 נק', 4♣, 3♥ (פתיחה 1♣), N: 9 נק' 4♥
run('1♣ → 1♥ → 2♥ → פס',
    {'N': make_hand('K32','KJ54','Q32','654'),    # 9 נק', 4♥
     'S': make_hand('A54','QT3','K32','AJ32'),    # 13 נק', 4♣>3♦ → 1♣
     'E': make_hand('QJ976','A876','J65','8'),
     'W': make_hand('T8','92','AT874','KQT7')},
    'S', ['1♣','1♥','2♥','פס'])

# ── TEST 10: 2♥ חלשה → פס ────────────────────────────────────────────────────
# N: 8 נק', 6♥, KQ בלב (5 נק' גבוהות) → פתיחה חלשה 2♥
run('2♥ חלשה → פס',
    {'N': make_hand('432','KQJ876','54','32'),    # 8 נק', 6♥, KQJ בלב=6 נק' גבוהות
     'S': make_hand('K65','A2','KJ32','Q876'),    # 12 נק' — אבל שותף מכריז פס לעת עתה
     'E': make_hand('QJ97','T95','AQ76','J4'),
     'W': make_hand('AT8','43','T98','AKT95')},
    'N', ['2♥','פס'])

# ── סיכום ─────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות ההכרזה עברו!')
