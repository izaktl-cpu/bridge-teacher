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

# ── TEST 1: 1♣ — E:1♠ — S:X (4♥ חסום, אין עצור) → N:2♥ ──────────────────────
# N: 13 נק', 4♥, פותח 1♣. E אוברקל 1♠. S יש 4♥ בלי עצור ♠ → X. N יש 4♥ → 2♥
run('1♣ — 1♠ — X(4♥) — 2♥',
    {'N': make_hand('K52','AJ54','KJ3','Q87'),       # 13 נק', 4♥ → 2♥ אחרי X
     'S': make_hand('73','KQ86','Q742','J54'),        # 8 נק', 4♥, אין עצור ♠ → X
     'E': make_hand('AQJ86','T2','A65','KT3'),        # 13 נק', 5♠ → אוברקול
     'W': make_hand('T94','973','T98','A962')},
    'N',
    expected_ns=['1♣','X','2♥','פס'],
    expected_ew=['1♠'])

# ── TEST 2: 1♦ — E:1♠ — S:X (4♥ חסום, אין עצור) → N:2♥ ──────────────────────
# N: 13 נק', 4♥, 5♦, לא מאוזן → 1♦. S: 7 נק', 4♥, אין עצור ♠ → X
run('1♦ — 1♠ — X(4♥) — 2♥',
    {'N': make_hand('K3','AJ74','AQ852','87'),         # 14 נק', 5♦, 4♥, לא מאוזן → 1♦; 14≤15 → 2♥
     'S': make_hand('74','KT86','J73','Q654'),         # 7 נק', 4♥, אין עצור ♠ → X
     'E': make_hand('AQJ86','Q2','K64','KT3'),         # 13 נק', 5♠ → אוברקול
     'W': make_hand('T952','953','T9','A982')},
    'N',
    expected_ns=['1♦','X','2♥','פס'],
    expected_ew=['1♠'])

# ── TEST 3: 1♣ — E:1♥ — S:X (4♠+4♥) → N:1♠ ────────────────────────────────
# N: 13 נק', 4♠, 4♦, 3♣ → 1♣. E אוברקל 1♥. S: 8 נק', 4♠+4♥ → X. N יש 4♠ → 1♠
run('1♣ — 1♥ — X(4♠+4♥) — 1♠',
    {'N': make_hand('KJ54','K3','Q32','A987'),         # 13 נק', 4♠, 4♣>3♦ → 1♣; 4♠ → 1♠ אחרי X
     'S': make_hand('QT87','J974','K54','J5'),          # 8 נק', 4♠+4♥ → X
     'E': make_hand('93','AQT65','J87','KT3'),          # 10 נק', 5♥ → אוברקול
     'W': make_hand('A62','82','AT96','Q642')},
    'N',
    expected_ns=['1♣','X','1♠','פס'],
    expected_ew=['1♥'])

# ── TEST 4: 1♣ — E:1♠ — S:1NT (עצור ♠, לא X) ───────────────────────────────
# S יש גם 4♥ וגם KQ7 עצור ♠ → 1NT עדיף על X (עצור מתאר יד טוב יותר)
run('1♣ — 1♠ — 1NT (עצור, לא X)',
    {'N': make_hand('K52','AJ54','KJ3','Q87'),        # 13 נק', 4♥
     'S': make_hand('KQ7','J876','Q742','54'),         # 8 נק', עצור ♠(KQ7), 4♥ → 1NT
     'E': make_hand('AJT86','T2','A65','KT3'),         # 12 נק', 5♠ → אוברקול
     'W': make_hand('943','KQ93','T98','J62')},
    'N',
    expected_ns=['1♣','1NT','פס'],
    expected_ew=['1♠'])

# ── TEST 5: 1♥ — E:2♣ — S:X (4♠ חסום ברמה 2) → N:2♠ ──────────────────────
# N: 14 נק', 5♥, 3322 — אבל 14 < 15 → לא 1NT → פותח 1♥
# E: 12+ נק', 5♣ עם 5+ נק' גבוהות → אוברקול 2♣
# S: 8 נק', 4♠, 2♥ (אין תמיכה) → X (1♠ חסום אחרי 2♣)
# N: 3♠ → 2♠
run('1♥ — 2♣ — X(4♠) — 2♠',
    {'N': make_hand('K32','AKJ54','Q32','J2'),         # 14 נק', 5♥, 3322 → לא 1NT → 1♥; 3♠ → 2♠
     'S': make_hand('AK76','32','J743','T54'),          # 8 נק', 4♠, 2♥ → X אחרי 2♣
     'E': make_hand('J4','T6','A843','AQJ83'),          # 12 נק', 5♣, suit_hcp=7 → 2♣
     'W': make_hand('QT985','Q987','K965','6')},
    'N',
    expected_ns=['1♥','X','2♠','פס'],
    expected_ew=['2♣'])

# ── סיכום ────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות הנגטיב דאבל עברו!')
