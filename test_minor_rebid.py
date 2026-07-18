# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'D:/bridge-teacher')
from bidding_engine import compute_auction
from bridge_teacher import cfg

cfg['majorLen']=5; cfg['ntMin']=15; cfg['ntMax']=17; cfg['minorLen']=3

errors = []

def make_hand(spades='', hearts='', diamonds='', clubs=''):
    hand = []
    for suit, cards in [('♠',spades),('♥',hearts),('♦',diamonds),('♣',clubs)]:
        for r in cards: hand.append({'s':suit,'r':r})
    return hand

# EW חלשים — לא יתערבו
EW_E = make_hand('T97','976','T987','876')   # 0 נק', 13 קלפים
EW_W = make_hand('862','543','654','T932')   # 0 נק', 13 קלפים

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

# ── 1♣ → 1♥ → 2♥ → פס (N=12, S=6, תמיכה מינימום) ─────────────────────────
# N: ♠KJ3 ♥Q32 ♦Q32 ♣KJ54 = K+J+Q+Q+K+J = 3+1+2+2+3+1 = 12 נק', 4333
# S: ♠654 ♥KJ87 ♦Q54 ♣T32 = K+J+Q = 3+1+2 = 6 נק', 4♥
run('1♣ → 1♥ → 2♥ → פס',
    {'N': make_hand('KJ3','Q32','Q32','KJ54'),
     'S': make_hand('654','KJ87','Q54','T32'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','1♥','2♥','פס'])

# ── 1♣ → 1♥ → 4♥ → פס (N=19, S=12, תמיכה חזקה) ────────────────────────────
# N: ♠A32 ♥AK2 ♦K32 ♣AJ54 = A+A+K+K+A+J = 4+4+3+3+4+1 = 19 נק', 3♥
# S: ♠KQ4 ♥QJT87 ♦54 ♣A32 = K+Q+Q+J+A = 3+2+2+1+4 = 12 נק', 5♥
run('1♣ → 1♥ → 4♥ → פס',
    {'N': make_hand('A32','AK2','K32','AJ54'),
     'S': make_hand('KQ4','QJT87','54','A32'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','1♥','4♥','פס'])

# ── 1♣ → 1NT → פס (N=12, S=9, 4♦ מאוזן — ביד מאוזנת לא מגיבים 1♦) ──────
# N: ♠KJ3 ♥Q32 ♦Q32 ♣KJ54 = 12 נק', 4♣3♦ מאוזן
# S: ♠Q65 ♥654 ♦KQ76 ♣Q32 = Q+K+Q+Q = 9 נק', 4♦ מאוזן → 1NT ישיר
run('1♣ → 1NT → פס',
    {'N': make_hand('KJ3','Q32','Q32','KJ54'),
     'S': make_hand('Q65','654','KQ76','Q32'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','1NT','פס'])

# ── 1♣ → 1♦ → 2♦ → פס (N=12, 4♦, S=9, 5♦ לא מאוזן 5422) ──────────────────
# N: ♠J2 ♥J2 ♦KQ32 ♣KQ542 = 12 נק', 5♣, 4♦
# S: ♠Q6 ♥Q4 ♦AJ762 ♣T532 = Q+Q+A+J = 9 נק', 5♦ לא מאוזן (2♠2♥5♦4♣=5422)
run('1♣ → 1♦ → 2♦ → פס',
    {'N': make_hand('J2','J2','KQ32','KQ542'),
     'S': make_hand('Q6','Q4','AJ762','T532'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','1♦','2♦','פס'])

# ── 1♣ → 1♦ → 3♦ → פס (N=17, 4♦, S=9, 5♦ לא מאוזן 5422) ──────────────────
# N: ♠K2 ♥AJ ♦KQ32 ♣KJ542 = 17 נק', 5♣, 4♦
# S: ♠Q6 ♥Q4 ♦AJ762 ♣T532 = 9 נק', 5♦ לא מאוזן (2♠2♥5♦4♣=5422)
run('1♣ → 1♦ → 3♦ → פס',
    {'N': make_hand('K2','AJ','KQ32','KJ542'),
     'S': make_hand('Q6','Q4','AJ762','T532'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','1♦','3♦','פס'])

# ── 1♣ → 2♦ → 2NT → 3NT → פס (N=12, S=13, 5♦) ─────────────────────────────
# N: ♠KJ3 ♥Q32 ♦Q32 ♣KJ54 = 12 נק', 3♦ (אין תמיכה)
# S: ♠Q65 ♥K54 ♦AKJ76 ♣32 = Q+K+A+K+J = 2+3+4+3+1 = 13 נק', 5♦
run('1♣ → 2♦ → 2NT → 3NT → פס',
    {'N': make_hand('KJ3','Q32','Q32','KJ54'),
     'S': make_hand('Q65','K54','AKJ76','32'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','2♦','2NT','3NT','פס'])

# ── 1♣ → 2♦ → 3NT → פס (N=15, לא מאוזן, S=13, 5♦) ─────────────────────────
# N: ♠AJ32 ♥J2 ♦Q2 ♣AKQ54 = A+J+J+Q+A+K+Q = 4+1+1+2+4+3+2 = 17 נק', 5♣ לא מאוזן
# S: ♠Q65 ♥K54 ♦AKJ76 ♣32 = Q+K+A+K+J = 2+3+4+3+1 = 13 נק', 5♦
run('1♣ → 2♦ → 3NT → פס',
    {'N': make_hand('AJ32','J2','Q2','AKQ54'),
     'S': make_hand('Q65','K54','AKJ76','32'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','2♦','3NT','פס'])

# ── 1♣ → 2♦ → 3♦ → פס (N=12, 4♦, S=11, 5♦) ────────────────────────────────
# N: ♠J2 ♥J2 ♦KQ32 ♣KQ542 = 12 נק', 4♦ (תמיכה)
# S: ♠Q65 ♥Q54 ♦AQJ76 ♣32 = Q+Q+A+Q+J = 2+2+4+2+1 = 11 נק', 5♦
run('1♣ → 2♦ → 3♦ → פס',
    {'N': make_hand('J2','J2','KQ32','KQ542'),
     'S': make_hand('Q65','Q54','AQJ76','32'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♣','2♦','3♦','3NT','פס'])

# ── 1♦ → 1♥ → 4♥ → פס (N=19, 3♥, S=12, 5♥) ────────────────────────────────
# N: ♠A32 ♥AK2 ♦AKJ54 ♣32 = A+A+K+A+K+J = 4+4+3+4+3+1 = 19 נק', 5♦, 3♥
# S: ♠KQ4 ♥QJT87 ♦32 ♣A54 = K+Q+Q+J+A = 3+2+2+1+4 = 12 נק', 5♥
run('1♦ → 1♥ → 4♥ → פס',
    {'N': make_hand('A32','AK2','AKJ54','32'),
     'S': make_hand('KQ4','QJT87','32','A54'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♦','1♥','4♥','פס'])

# ── 1♦ → 1♠ → 3NT → פס (N=19, S=10, 5♠) ────────────────────────────────────
# N: ♠K2 ♥AKQ ♦AKJ54 ♣K32 = K+A+K+Q+A+K+J+K = 3+4+3+2+4+3+1+3 = 23 נק'... יפתח 2♣
# N: ♠K2 ♥AQ3 ♦AKJ54 ♣K32 = K+A+Q+A+K+J+K = 3+4+2+4+3+1+3 = 20 נק'... יפתח 2NT
# N: ♠K2 ♥Q32 ♦AKJ54 ♣AJ3 = K+Q+A+K+J+A+J = 3+2+4+3+1+4+1 = 18 נק', 5♦
# S: ♠AJ876 ♥654 ♦32 ♣K54 = A+J+K = 4+1+3 = 8 נק'... need 10
# S: ♠AJT87 ♥654 ♦32 ♣KQ4 = A+J+K+Q = 4+1+3+2 = 10 נק', 5♠
run('1♦ → 1♠ → 3NT → פס',
    {'N': make_hand('K2','Q32','AKJ54','AJ3'),
     'S': make_hand('AJT87','654','32','KQ4'),
     'E': EW_E, 'W': EW_W}, 'N',
    ['1♦','1♠','3NT','פס'])

print()
if errors:
    print(f'{len(errors)} שגיאות: {errors}')
else:
    print('כל בדיקות המינור עברו!')
