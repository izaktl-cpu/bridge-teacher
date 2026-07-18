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

# ── TEST 1: 1♥ — E:X — S:XX (11 נק') → N:X אחרי בריחת W ─────────────────────
# N: 15 נק', 5♥+4♦ (לא מאוזן) → 1♥; 15≥14 → X אחרי בריחה
# E: 15 נק', ≤2♥, 3+ בכל צבע אחר → X (טייקאוט)
# S: 11 נק', 2♥ → XX
# W: ≤0 נק', 4♣ (ארוך ביותר) → בורח 2♣
# N: ew_escape=2♣, 15≥14 → X (עונשין)
run('1♥ — X — XX — 2♣ — X (עונשין)',
    {'N': make_hand('K4','AKJ54','K432','J5'),        # 15 נק', 5♥+4♦, לא מאוזן → 1♥
     'S': make_hand('AJ7','32','QJ54','KT32'),         # 11 נק', 2♥ → XX
     'E': make_hand('AT5','76','AQ76','KQ74'),          # 15 נק', ≤2♥, אין 5 בצבע → X
     'W': make_hand('963','T98','T98','9873')},         # 0 נק', 4♣ → בורח 2♣
    'N',
    expected_ns=['1♥','XX','X','פס'],
    expected_ew=['X','2♣'])

# ── TEST 2: 1♠ — E:X — S:XX (11 נק') → N:פס (12<14) ──────────────────────────
# N: 12 נק', 5♠ מאוזן (12<15) → 1♠; 12<14 → לא מדבל
# E: 14 נק', ≤2♠ → X. W בורח 2♦
run('1♠ — X — XX — פס (N חלש)',
    {'N': make_hand('AKJ54','K32','J54','32'),         # 12 נק', 5♠, מאוזן → 1♠; 12<14 → פס
     'S': make_hand('Q7','AJ54','KT32','J54'),          # 11 נק', 2♠ → XX
     'E': make_hand('T8','AQ76','KQ76','K73'),           # 14 נק', ≤2♠ → X
     'W': make_hand('962','T98','9865','AT6')},          # 4 נק', 4♦ → בורח 2♦
    'N',
    expected_ns=['1♠','XX','פס','פס'],
    expected_ew=['X','2♦'])

# ── TEST 3: 1♥ — E:X — S:2♥ (תמיכה 3♥, לא XX) ──────────────────────────────
# S יש 3♥ + 8 נק' → תמיכה עדיפה על XX → 2♥
run('1♥ — X — 2♥ (תמיכה גוברת)',
    {'N': make_hand('K4','AKJ54','K432','J5'),         # 15 נק', לא מאוזן → 1♥
     'S': make_hand('AJ7','Q32','J54','T832'),          # 8 נק', 3♥ → 2♥ (לא XX)
     'E': make_hand('T85','76','AQ76','AQ74'),           # 12 נק', ≤2♥, אין 5 בצבע → X
     'W': make_hand('9632','T98','T98','983')},          # 0 נק', 4♠ → בורח 2♠
    'N',
    expected_ns=['1♥','2♥','פס','פס'],
    expected_ew=['X','2♠'])

# ── TEST 4: 1♣ — E:X — S:1♠ (5♠, 6 נק' → לא XX) ───────────────────────────
# S יש 5♠ + 6 נק' (< 10) → מכריז 1♠ ישירות בלי XX; N rebids 1NT
run('1♣ — X — 1♠ (5♠, חלש → לא XX)',
    {'N': make_hand('K3','QT3','K432','AJ43'),          # 13 נק', 4♣=4♦ → 1♣
     'S': make_hand('QJ876','J54','Q72','32'),            # 6 נק', 5♠ → 1♠ (לא XX)
     'E': make_hand('AT54','AK76','AJ54','K'),            # 18 נק', ≤1♣ → X
     'W': make_hand('92','982','T986','QT87')},           # 5 נק', 4♦ → בורח 2♦
    'N',
    expected_ns=['1♣','1♠','1NT','פס'],
    expected_ew=['X','2♦'])

# ── סיכום ────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות הרידאבל עברו!')
