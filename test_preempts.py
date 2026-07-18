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
        if expected_ew is not None and ew_bids != expected_ew:
            print(f'  EW צפוי:   {expected_ew}')
            print(f'  EW קיבלנו: {ew_bids}')
        errors.append(name)

# ── פרי-אמפטים ───────────────────────────────────────────────────────────────

# TEST 1: פתיחה 3♥ — 7 קלפים, 8 נק' → שותף עם 2♥+13 נק' מעלה ל-4♥
# N: 8 נק', 7♥ (KQJ9854) → 3♥; S: 14 נק', 2♥ → 4♥
run('3♥ — פס — 4♥',
    {'N': make_hand('32','KQJ9854','T2','32'),      # 8 נק', 7♥ → 3♥
     'S': make_hand('AKQ4','T2','AJ43','Q65'),       # 14 נק', 2♥ → 4♥
     'E': make_hand('J876','A3','KQ65','KJ4'),        # לא מפריע
     'W': make_hand('T95','76','987','AT987')},
    'N',
    expected_ns=['3♥','4♥','פס'])

# TEST 2: פתיחה 3♥ — שותף חלש (10 נק', 2♥) → פס
run('3♥ — פס (S חלש)',
    {'N': make_hand('32','KQJ9854','T2','32'),      # 8 נק', 7♥ → 3♥
     'S': make_hand('AJ54','T2','KJ43','Q65'),       # 10 נק', 2♥ → פס (< 13)
     'E': make_hand('J876','A3','AQ5','KJ84'),
     'W': make_hand('KT9','76','987','AT987')},
    'N',
    expected_ns=['3♥','פס'])

# TEST 3: פתיחה 3♦ — שותף מאוזן עם 15 נק', 2♦ → 3NT (לא 5♦ כי רק 2 יהלומים)
# N: 6 נק', 7♦ → 3♦; S: 15 נק', 4-3-2-4 מאוזן, 2♦ → 3NT
run('3♦ — פס — 3NT',
    {'N': make_hand('32','T2','KQJ9854','32'),      # 6 נק', 7♦ → 3♦
     'S': make_hand('KQ43','AJ5','T2','AJ54'),       # 15 נק', 2♦, מאוזן → 3NT
     'E': make_hand('J876','Q3','96','QT987'),        # 3 נק', לא מפריע
     'W': make_hand('AT95','K987','53','K6')},        # 8 נק', לא מפריע
    'N',
    expected_ns=['3♦','3NT','פס'])

# TEST 4: פתיחה 3♣ — 7 תלתנים, שותף פס (< 14 נק' ו-2♣)
# N: 8 נק', 7♣ → 3♣; S: 9 נק', 2♣ → פס (צריך 14+ ו-3+ ל-5♣)
run('3♣ — פס (S חלש)',
    {'N': make_hand('32','T2','32','KQJ9854'),      # 8 נק', 7♣ → 3♣
     'S': make_hand('AJ54','KJ4','J543','T2'),       # 9 נק', 2♣ → פס
     'E': make_hand('KT87','AQ65','AQ65','A'),
     'W': make_hand('Q96','9873','KT87','76')},
    'N',
    expected_ns=['3♣','פס'])

# TEST 5: פתיחה 4♥ — 8 קלפים (8 נק'), שותף חלש (12 נק', < 17) → פס
run('4♥ — פס',
    {'N': make_hand('2','KQJ98543','T2','32'),      # 7 נק', 8♥ → 4♥
     'S': make_hand('AKJ4','T2','AJ43','Q65'),       # 12 נק' < 17 → פס
     'E': make_hand('QT87','A76','KQ65','KJ'),
     'W': make_hand('9653','J','987','AT987')},
    'N',
    expected_ns=['4♥','פס'])

# TEST 6: פתיחה 4♥ — שותף עם 17+ נק' → 4NT (Blackwood)
# N: 7 נק', 8♥ → 4♥; S: 17 נק' → 4NT; N: פס (אין handler לBW אחרי פרי-אמפט)
run('4♥ — פס — 4NT',
    {'N': make_hand('2','KQJ98543','T2','32'),      # 7 נק', 8♥ → 4♥
     'S': make_hand('AKJ4','T2','AKJ3','KQ5'),       # 17 נק' → 4NT
     'E': make_hand('QT87','A76','Q965','J84'),
     'W': make_hand('9653','J','87','AT9876')},
    'N',
    expected_ns=['4♥','4NT','פס'])

# ── 2NT — טרנספר ─────────────────────────────────────────────────────────────

# TEST 7: 2NT → 3♦ (טרנספר ♥) → 3♥ → 4♥
# N: 22 נק', 3-3-4-3 מאוזן → 2NT; S: 4 נק', 5♥ → 3♦; N: 3♥; S: 4♥; N: פס
run('2NT → 3♦ → 3♥ → 4♥',
    {'N': make_hand('KQ4','AK3','AQT4','KJ3'),      # 22 נק', מאוזן → 2NT
     'S': make_hand('J32','QJ876','T32','54'),        # 4 נק', 5♥ → 3♦ → 4♥ אחרי 3♥
     'E': make_hand('AT87','T4','K965','Q87'),        # 9 נק', לא מפריע
     'W': make_hand('965','952','87','AT962')},       # 4 נק', לא מפריע
    'N',
    expected_ns=['2NT','3♦','3♥','4♥','פס'])

# TEST 8: 2NT → 3♥ (טרנספר ♠) → 3♠ → 4♠
# N: 22 נק', מאוזן → 2NT; S: 4 נק', 5♠ → 3♥; N: 3♠; S: 4♠; N: פס
run('2NT → 3♥ → 3♠ → 4♠',
    {'N': make_hand('AK3','KQ4','AQT4','KJ3'),      # 22 נק', מאוזן → 2NT
     'S': make_hand('QJ876','32','K32','654'),        # 6 נק', 5♠ → 3♥ → 4♠ אחרי 3♠
     'E': make_hand('T94','AT87','K965','Q8'),        # 9 נק', לא מפריע
     'W': make_hand('52','J965','87','AT972')},       # 6 נק', לא מפריע
    'N',
    expected_ns=['2NT','3♥','3♠','4♠','פס'])

# TEST 9: 2NT → 3♣ (סטיימן) → 3♥ (יש 4♥) → 4♥ (התאמה)
# N: 22 נק', 4♥ → 2NT; S: 5 נק', 4♥ → 3♣; N: 3♥; S: 4♥; N: פס
run('2NT → 3♣ → 3♥ → 4♥ (סטיימן)',
    {'N': make_hand('KQ3','AKJ4','AQT4','K3'),      # 22 נק', 4♥ → 2NT → 3♥
     'S': make_hand('J654','QT87','K2','654'),         # 6 נק', 4♥ → 3♣ → 4♥
     'E': make_hand('AT87','53','K965','QJ7'),        # 9 נק', לא מפריע
     'W': make_hand('92','962','T87','AT982')},       # 4 נק', לא מפריע
    'N',
    expected_ns=['2NT','3♣','3♥','4♥','פס'])

# TEST 10: 2NT → 3♣ (סטיימן) → 3♦ (אין מיגור) → 3NT
# N: 21 נק', 3-3-4-3, אין 4-קלפים במיגור → 3♦; S: 5 נק', 4♥ → 3NT
run('2NT → 3♣ → 3♦ → 3NT (אין מיגור)',
    {'N': make_hand('KQ3','AKJ','AQT4','Q63'),      # 21 נק', 3-3-4-3, אין 4♥/4♠ → 3♦
     'S': make_hand('J65','QT87','Q32','654'),        # 5 נק', 4♥ → 3♣ → 3NT אחרי 3♦
     'E': make_hand('AT87','953','K965','Q7'),        # 9 נק', לא מפריע
     'W': make_hand('942','62','T87','AJT82')},       # 6 נק', לא מפריע
    'N',
    expected_ns=['2NT','3♣','3♦','3NT','פס'])

# ── סיכום ────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות הפרי-אמפטים ו-2NT עברו!')
