# -*- coding: utf-8 -*-
import sys, io, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'D:/bridge-teacher')

from bidding_engine import compute_auction, hcp, sl, is_balanced
from bridge_teacher import cfg, create_deck, shuffle

cfg['majorLen']=5; cfg['ntMin']=15; cfg['ntMax']=17; cfg['minorLen']=3

SUITS = ['♠','♥','♦','♣']
RANKS = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']
errors = []

# ── יצירת ידיים ─────────────────────────────────────────────────────────────
def deal_constrained(constraints, n=10, seed_start=0):
    """מייצר n ידיים העומדות באילוצים"""
    deck = create_deck()
    results = []
    seed = seed_start
    while len(results) < n and seed < seed_start + 50000:
        random.seed(seed)
        d = shuffle(deck)
        h = {'N':d[0:13],'E':d[13:26],'S':d[26:39],'W':d[39:52]}
        if all(constraints.get(p, lambda x: True)(h[p]) for p in 'NESW'):
            results.append((h, seed))
        seed += 1
    return results

def fmt_hand(hand):
    parts = []
    for s in SUITS:
        cards = ''.join(sorted([c['r'] for c in hand if c['s']==s],
                               key=lambda r: RANKS.index(r)))
        parts.append(f"{s}{cards or '—'}")
    return ' '.join(parts)

def run_category(title, constraints, checks, dealer='N', n=10, seed_start=0):
    """מריץ קטגוריה: מייצר ידיים, בודק הכרזות"""
    print(f'\n{"="*60}')
    print(f'  {title}')
    print(f'{"="*60}')
    hands_list = deal_constrained(constraints, n, seed_start)
    if not hands_list:
        print('  ⚠ לא נמצאו ידיים מתאימות')
        return
    cat_errors = 0
    for hands, seed in hands_list:
        c = dict(cfg)
        auction, players = compute_auction(hands, dealer, c)
        ok, msg = checks(hands, auction, players)
        status = '[OK]' if ok else '[FAIL]'
        if not ok:
            cat_errors += 1
            errors.append(f'{title}: {msg}')
        print(f'  {status} {" — ".join(auction[:8])}{"..." if len(auction)>8 else ""}')
        if not ok:
            print(f'       ✗ {msg}')
            print(f'       N: {fmt_hand(hands["N"])} ({hcp(hands["N"])} נק\')')
            print(f'       S: {fmt_hand(hands["S"])} ({hcp(hands["S"])} נק\')')
    if cat_errors == 0:
        print(f'  ✓ {len(hands_list)} ידיים — הכל תקין')
    else:
        print(f'  ✗ {cat_errors}/{len(hands_list)} שגיאות')

# ── בדיקות עזר ──────────────────────────────────────────────────────────────
def first_bid(auction): return auction[0] if auction else ''
def nth_ns(auction, players, n):
    ns = [auction[i] for i,p in enumerate(players) if p in ('N','S')]
    return ns[n] if len(ns) > n else ''

# ════════════════════════════════════════════════════════════════════════════
# 1. פתיחת 1NT
# ════════════════════════════════════════════════════════════════════════════
def c_1nt(h): return is_balanced(h) and 15 <= hcp(h) <= 17
def chk_1nt(hands, auction, players):
    if first_bid(auction) != '1NT':
        return False, f'ציפינו 1NT, קיבלנו {first_bid(auction)}'
    return True, ''
run_category('פתיחת 1NT (15-17, מאוזן)',
    {'N': c_1nt, 'E': lambda h: hcp(h) < 12, 'W': lambda h: hcp(h) < 12},
    chk_1nt, seed_start=100)

# ════════════════════════════════════════════════════════════════════════════
# 2. פתיחת 1♥
# ════════════════════════════════════════════════════════════════════════════
def c_1h(h): return sl(h,'♥')>=5 and 12<=hcp(h)<=21 and not(is_balanced(h) and 15<=hcp(h)<=17)
def chk_1h(hands, auction, players):
    if first_bid(auction) != '1♥':
        return False, f'ציפינו 1♥, קיבלנו {first_bid(auction)}'
    return True, ''
run_category('פתיחת 1♥ (5+♥, 12-21)',
    {'N': c_1h, 'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1h, seed_start=200)

# ════════════════════════════════════════════════════════════════════════════
# 3. פתיחת 1♠
# ════════════════════════════════════════════════════════════════════════════
def c_1s(h): return sl(h,'♠')>=5 and sl(h,'♥')<5 and 12<=hcp(h)<=21 and not(is_balanced(h) and 15<=hcp(h)<=17)
def chk_1s(hands, auction, players):
    if first_bid(auction) != '1♠':
        return False, f'ציפינו 1♠, קיבלנו {first_bid(auction)}'
    return True, ''
run_category('פתיחת 1♠ (5+♠, 12-21)',
    {'N': c_1s, 'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1s, seed_start=300)

# ════════════════════════════════════════════════════════════════════════════
# 4. פתיחת 1♥ + תמיכה חלשה (2♥)
# ════════════════════════════════════════════════════════════════════════════
def c_s_weak_h(h): return sl(h,'♥')>=3 and 6<=hcp(h)<=9
def chk_1h_raise(hands, auction, players):
    b0 = nth_ns(auction, players, 0)
    b1 = nth_ns(auction, players, 1)
    if b0 != '1♥': return False, f'פתיחה {b0} במקום 1♥'
    if b1 != '2♥': return False, f'תשובה {b1} במקום 2♥'
    return True, ''
run_category('1♥ + תמיכה חלשה → 2♥',
    {'N': c_1h, 'S': c_s_weak_h,
     'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1h_raise, seed_start=400)

# ════════════════════════════════════════════════════════════════════════════
# 5. פתיחת 1♠ + תמיכה חזקה (4♠)
# ════════════════════════════════════════════════════════════════════════════
def c_s_str_s(h): return sl(h,'♠')>=3 and 13<=hcp(h)<=16
def chk_1s_game(hands, auction, players):
    b0 = nth_ns(auction, players, 0)
    b1 = nth_ns(auction, players, 1)
    if b0 != '1♠': return False, f'פתיחה {b0} במקום 1♠'
    if b1 != '4♠': return False, f'תשובה {b1} במקום 4♠'
    return True, ''
run_category('1♠ + תמיכה חזקה → 4♠',
    {'N': c_1s, 'S': c_s_str_s,
     'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1s_game, seed_start=500)

# ════════════════════════════════════════════════════════════════════════════
# 6. פתיחת 1NT + סטיימן (4♥/4♠)
# ════════════════════════════════════════════════════════════════════════════
def c_stayman_s(h):
    return (sl(h,'♥')>=4 or sl(h,'♠')>=4) and sl(h,'♥')<5 and sl(h,'♠')<5 and 8<=hcp(h)<=12
def chk_1nt_stayman(hands, auction, players):
    b0 = nth_ns(auction, players, 0)
    b1 = nth_ns(auction, players, 1)
    if b0 != '1NT': return False, f'פתיחה {b0} במקום 1NT'
    if b1 != '2♣': return False, f'תשובה {b1} במקום 2♣ (סטיימן)'
    return True, ''
run_category('1NT + סטיימן (2♣)',
    {'N': c_1nt, 'S': c_stayman_s,
     'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1nt_stayman, seed_start=600)

# ════════════════════════════════════════════════════════════════════════════
# 7. פתיחת 1NT + טרנספר ♥ (2♦ → 2♥)
# ════════════════════════════════════════════════════════════════════════════
def c_trans_h(h): return sl(h,'♥')>=5 and 6<=hcp(h)<=12
def chk_1nt_trans_h(hands, auction, players):
    b0 = nth_ns(auction, players, 0)
    b1 = nth_ns(auction, players, 1)
    b2 = nth_ns(auction, players, 2)
    if b0 != '1NT': return False, f'פתיחה {b0} במקום 1NT'
    if b1 != '2♦': return False, f'תשובה {b1} במקום 2♦ (טרנספר♥)'
    if b2 != '2♥': return False, f'השלמה {b2} במקום 2♥'
    return True, ''
run_category('1NT + טרנספר ♥ (2♦ → 2♥)',
    {'N': c_1nt, 'S': c_trans_h,
     'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1nt_trans_h, seed_start=700)

# ════════════════════════════════════════════════════════════════════════════
# 8. פתיחת 2♣ חזקה
# ════════════════════════════════════════════════════════════════════════════
def c_2c(h): return hcp(h) >= 23
def chk_2c(hands, auction, players):
    if first_bid(auction) != '2♣':
        return False, f'ציפינו 2♣, קיבלנו {first_bid(auction)}'
    b1 = nth_ns(auction, players, 1)
    if b1 not in ('2♦','2♥','2♠','2NT','3♣','3♦','3♥','3♠'):
        return False, f'תשובה לא חוקית ל-2♣: {b1}'
    return True, ''
run_category('פתיחת 2♣ חזקה (23+)',
    {'N': c_2c, 'E': lambda h: hcp(h) < 8, 'W': lambda h: hcp(h) < 8},
    chk_2c, seed_start=800)

# ════════════════════════════════════════════════════════════════════════════
# 9. פתיחה חלשה 2♥ (6-9, 6+ לבבות)
# ════════════════════════════════════════════════════════════════════════════
def c_2h_weak(h):
    from bidding_engine import suit_hcp
    return sl(h,'♥')==6 and 6<=hcp(h)<=9 and suit_hcp(h,'♥')>=5 and sl(h,'♠')<5
def chk_2h_weak(hands, auction, players):
    if first_bid(auction) != '2♥':
        return False, f'ציפינו 2♥, קיבלנו {first_bid(auction)}'
    return True, ''
run_category('פתיחה חלשה 2♥ (6-9, 6+♥)',
    {'N': c_2h_weak, 'E': lambda h: hcp(h) < 12, 'W': lambda h: hcp(h) < 12},
    chk_2h_weak, seed_start=900)

# ════════════════════════════════════════════════════════════════════════════
# 10. פרי-אמפט 3♥ (7+ לבבות, 6-9)
# ════════════════════════════════════════════════════════════════════════════
def c_3h(h):
    from bidding_engine import suit_hcp
    return sl(h,'♥')>=7 and 6<=hcp(h)<=9 and suit_hcp(h,'♥')>=5
def chk_3h(hands, auction, players):
    if first_bid(auction) != '3♥':
        return False, f'ציפינו 3♥, קיבלנו {first_bid(auction)}'
    return True, ''
run_category('פרי-אמפט 3♥ (7+♥, 6-9)',
    {'N': c_3h, 'E': lambda h: hcp(h) < 12, 'W': lambda h: hcp(h) < 12},
    chk_3h, seed_start=1000)

# ════════════════════════════════════════════════════════════════════════════
# 11. 1♥ + 3NT (גיים ישיר, 13+ מאוזן, אין תמיכה)
# ════════════════════════════════════════════════════════════════════════════
def c_3nt_resp(h): return is_balanced(h) and 13<=hcp(h)<=15 and sl(h,'♥')<3 and sl(h,'♠')<4
def chk_1h_3nt(hands, auction, players):
    b0 = nth_ns(auction, players, 0)
    b1 = nth_ns(auction, players, 1)
    b2 = nth_ns(auction, players, 2)
    if b0 != '1♥': return False, f'פתיחה {b0} במקום 1♥'
    if b1 != '3NT': return False, f'תשובה {b1} במקום 3NT'
    if b2 != 'פס': return False, f'rebid {b2} במקום פס'
    return True, ''
run_category('1♥ → 3NT → פס (פותח לא ממשיך)',
    {'N': c_1h, 'S': c_3nt_resp,
     'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1h_3nt, seed_start=1100)

# ════════════════════════════════════════════════════════════════════════════
# 12. 1♠ → 2♥ (חיפוש פיט לב)
# ════════════════════════════════════════════════════════════════════════════
def c_2h_resp(h): return sl(h,'♥')>=4 and sl(h,'♠')<3 and sl(h,'♥')<6 and 11<=hcp(h)<=14
def chk_1s_2h(hands, auction, players):
    b0 = nth_ns(auction, players, 0)
    b1 = nth_ns(auction, players, 1)
    if b0 != '1♠': return False, f'פתיחה {b0} במקום 1♠'
    if b1 != '2♥': return False, f'תשובה {b1} במקום 2♥ (4♥, אין תמיכה ♠)'
    return True, ''
run_category('1♠ → 2♥ (4♥, אין תמיכה ♠)',
    {'N': c_1s, 'S': c_2h_resp,
     'E': lambda h: hcp(h) < 10, 'W': lambda h: hcp(h) < 10},
    chk_1s_2h, seed_start=1200)

# ════════════════════════════════════════════════════════════════════════════
# סיכום
# ════════════════════════════════════════════════════════════════════════════
print(f'\n{"="*60}')
if errors:
    print(f'  {len(errors)} שגיאות:')
    for e in errors:
        print(f'  • {e}')
else:
    print(f'  ✓ כל הבדיקות העמוקות עברו!')
print('='*60)
