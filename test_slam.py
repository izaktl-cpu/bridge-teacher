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

# ── TEST 1: 1NT → 4♣(ג'רבר) → 4♠(2 אסים) → 6NT ────────────────────────────
# N: 15 נק' מאוזן → 1NT. S: 18 נק' → 4♣ ג'רבר. N: A♠+A♦=2 אסים → 4♠. S: 4 אסים סה"כ → 6NT
run('1NT → 4♣(ג\'רבר) → 4♠ → 6NT',
    {'N': make_hand('AK3','KQ4','A432','543'),    # 15 נק', מאוזן, A♠+A♦=2 אסים
     'S': make_hand('Q52','A32','KQJ6','AQ2'),    # 18 נק', מאוזן, A♥+A♣=2 אסים
     'E': make_hand('J964','J976','T95','J87'),
     'W': make_hand('T87','T85','87','KT986')},
    'N', ['1NT','4♣','4♠','6NT','פס'])

# ── TEST 2: 1NT → 4NT → 6NT (N עם 17 מקבל הזמנה) ────────────────────────────
# N: 17 נק' מאוזן → 1NT. S: 16 נק' → 4NT הזמנה. N עם 17 → מקבל → 6NT
run('1NT → 4NT → 6NT (הזמנה מתקבלת)',
    {'N': make_hand('AKQ','K73','K432','Q54'),    # 17 נק', מאוזן (4333)
     'S': make_hand('J54','AQ2','AJ65','KJ3'),    # 16 נק', מאוזן (4333)
     'E': make_hand('T98','JT98','QT9','AT9'),
     'W': make_hand('7632','654','87','8762')},
    'N', ['1NT','4NT','6NT','פס'])

# ── TEST 3: 1NT → 4NT → פס (N עם 15 דוחה הזמנה) ─────────────────────────────
# N: 15 נק' מאוזן → 1NT. S: 16 נק' → 4NT הזמנה. N עם 15 → דוחה → פס
run('1NT → 4NT → פס (הזמנה נדחית)',
    {'N': make_hand('AQ3','Q73','A432','K54'),    # 15 נק', מאוזן (4333)
     'S': make_hand('KJ5','AK2','QJ65','Q32'),    # 16 נק', מאוזן (4333)
     'E': make_hand('T9876','JT98','T9','JT9'),
     'W': make_hand('42','654','K87','A8765')},
    'N', ['1NT','4NT','פס'])

# ── TEST 4: 1♥ → 4♥ → 4NT(RKCB) → 5♦ → 6♥ (4 קלפי מפתח) ───────────────────
# N: 20 נק', 5431 לא מאוזן — KC: A♠ A♥ A♦ = 3
# S: 15 נק', 4♥ — KC: K♥ = 1. סה"כ 4 KC → 6♥
run('1♥ → 4♥ → 4NT → 5♦ → 6♥ (RKCB)',
    {'N': make_hand('AQ32','AQJ85','AK4','T'),    # 20 נק', 5431, KC=3
     'S': make_hand('KJ5','K732','QJ6','KQ3'),    # 15 נק', 4♥, KC=1(K♥)
     'E': make_hand('T98','T96','T987','AJ98'),
     'W': make_hand('764','4','532','765432')},
    'N', ['1♥','4♥','4NT','5♦','6♥','פס'])

# ── TEST 5: 1♥ → 4♥ → 4NT(RKCB) → 5♥ → 7♥ (5 קלפי מפתח — גרנד סלאם) ───────
# N: 20 נק', 5431 לא מאוזן — KC: A♠ A♥ A♣ = 3
# S: 15 נק', 4♥ — KC: K♥ + A♦ = 2, ללא Q♥. סה"כ 5 KC → 7♥
run('1♥ → 4♥ → 4NT → 5♥ → 7♥ (RKCB גרנד סלאם)',
    {'N': make_hand('AQ32','AQJ85','KT4','A'),    # 20 נק', 5431, KC=3 (A♠ A♥ A♣)
     'S': make_hand('J65','K732','AQ5','KQ3'),    # 15 נק', 4♥, KC=2 (K♥ A♦)
     'E': make_hand('KT9','T96','J987','JT9'),
     'W': make_hand('874','4','632','876542')},
    'N', ['1♥','4♥','4NT','5♥','7♥','פס'])

# ── TEST 6: 1♥ → 3♥ → 4♣(קיו) → 4NT(RKCB) → 5♠ → 6♥ (4 KC) ────────────────
# N: 20 נק', 6♥, לא מאוזן, A♣ → קיו-ביד 4♣; KC: A♥+A♣=2
# S: 11 נק', 4♥ → 3♥; KC: A♠+K♥=2 → total=4 → 6♥
run('1♥ → 3♥ → 4♣(קיו) → 4NT → 5♠ → 6♥',
    {'N': make_hand('QJ2','AQJ986','K2','AK'),      # 20 נק', 6♥, לא מאוזן
     'S': make_hand('AT4','K532','Q43','Q92'),       # 11 נק', 4♥
     'E': make_hand('K987','T7','AJT9','J87'),
     'W': make_hand('653','4','8765','T6543')},
    'N', ['1♥','3♥','4♣','4NT','5♠','6♥','פס'])

# ── TEST 7: 1♥ → 3♥ → 4♣(קיו) → 4♥ (S ויתר, < 11 נק') ─────────────────────
# N: 21 נק', 6♥, A♣ → קיו-ביד 4♣
# S: 10 נק', 4♥ → 3♥; ויתר → 4♥ (גיים בלבד)
run('1♥ → 3♥ → 4♣(קיו) → 4♥ (ויתור)',
    {'N': make_hand('J32','AKJ986','K2','AK'),       # 19 נק', 6♥, לא מאוזן
     'S': make_hand('KQ4','Q532','Q43','J92'),       # 10 נק', 4♥
     'E': make_hand('AT98','T74','AJT9','Q8'),
     'W': make_hand('765','','8765','T76543')},
    'N', ['1♥','3♥','4♣','4♥','פס'])

# ── TEST 8: 1♠ → 3♠ → 4♦(קיו) → 4NT(RKCB) → 5♣ → 6♠ (4 KC) ────────────────
# N: 20 נק', 5♠, לא מאוזן, A♦ (ראשון אחרי A♣ אין) → קיו-ביד 4♦; KC: A♠+A♦+K♠=3
# S: 11 נק', 4♠ → 3♠; KC: A♣=1 → total=4 → 6♠
run('1♠ → 3♠ → 4♦(קיו) → 4NT → 5♣ → 6♠',
    {'N': make_hand('AKQJ8','2','AK32','Q43'),       # 19 נק', 5♠, לא מאוזן
     'S': make_hand('T532','KJ4','Q54','AJ2'),       # 11 נק', 4♠
     'E': make_hand('974','AQT9','JT9','KT9'),
     'W': make_hand('6','87653','876','8765')},
    'N', ['1♠','3♠','4♦','4NT','5♣','6♠','פס'])

# ── סיכום ─────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות הסלאם עברו!')
