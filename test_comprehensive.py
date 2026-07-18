# -*- coding: utf-8 -*-
import sys, io, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'D:/bridge-teacher')

from bidding_engine import compute_auction, hcp, sl, is_balanced, suit_hcp
from bridge_teacher import cfg, create_deck, shuffle

cfg['majorLen']=5; cfg['ntMin']=15; cfg['ntMax']=17; cfg['minorLen']=3

SUITS  = ['♠','♥','♦','♣']
RANKS  = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']
errors = []
total  = 0
passed = 0

# ── כלים ────────────────────────────────────────────────────────────────────
def deal_constrained(constraints, n=10, seed_start=0):
    deck = create_deck()
    results = []
    seed = seed_start
    while len(results) < n and seed < seed_start + 100000:
        random.seed(seed)
        d = shuffle(deck)
        h = {'N':d[0:13],'E':d[13:26],'S':d[26:39],'W':d[39:52]}
        if all(constraints.get(p, lambda x: True)(h[p]) for p in 'NESW'):
            results.append((h, seed))
        seed += 1
    return results

def ns_bids(auction, players):
    return [auction[i] for i,p in enumerate(players) if p in ('N','S')]

def fmt(hand):
    parts = []
    for s in SUITS:
        cards = ''.join(sorted([c['r'] for c in hand if c['s']==s],
                               key=lambda r: RANKS.index(r)))
        parts.append(f"{s}{cards or '—'}")
    return ' '.join(parts)

def run(title, constraints, check_fn, dealer='N', n=10, seed_start=0):
    global total, passed
    hands_list = deal_constrained(constraints, n, seed_start)
    cat_ok = 0
    cat_fail = 0
    fail_msgs = []
    for hands, seed in hands_list:
        total += 1
        auction, players = compute_auction(hands, dealer, dict(cfg))
        bids = ns_bids(auction, players)
        ok, msg = check_fn(hands, bids)
        if ok:
            passed += 1
            cat_ok += 1
        else:
            cat_fail += 1
            errors.append(f'{title}: {msg}')
            fail_msgs.append((msg, hands))
    status = '✓' if cat_fail == 0 else '✗'
    n_found = len(hands_list)
    print(f'  {status} {title:<45} {cat_ok}/{n_found}')
    for msg, hands in fail_msgs[:2]:
        print(f'      ✗ {msg}')
        print(f'        N: {fmt(hands["N"])} ({hcp(hands["N"])}נק\')')
        print(f'        S: {fmt(hands["S"])} ({hcp(hands["S"])}נק\')')

# ── אילוצי ידיים נפוצים ──────────────────────────────────────────────────────
ew_weak   = {'E': lambda h: hcp(h)<10, 'W': lambda h: hcp(h)<10}
ew_silent = {'E': lambda h: hcp(h)<12, 'W': lambda h: hcp(h)<12}
ew_quiet  = {'E': lambda h: hcp(h)<9,  'W': lambda h: hcp(h)<9}   # מניע אוברקול (מנוע דורש 9+)

def op_1h(lo, hi):
    return lambda h: sl(h,'♥')>=5 and lo<=hcp(h)<=hi and not(is_balanced(h) and 15<=hcp(h)<=17) and not(is_balanced(h) and 20<=hcp(h)<=22)

def op_1s(lo, hi):
    return lambda h: sl(h,'♠')>=5 and sl(h,'♥')<5 and lo<=hcp(h)<=hi and not(is_balanced(h) and 15<=hcp(h)<=17) and not(is_balanced(h) and 20<=hcp(h)<=22)

def op_1nt():
    return lambda h: is_balanced(h) and 15<=hcp(h)<=17

def op_1m(suit, lo, hi):
    def c(h):
        if sl(h,'♥')>=5 or sl(h,'♠')>=5: return False
        if is_balanced(h) and 15<=hcp(h)<=17: return False
        if is_balanced(h) and 20<=hcp(h)<=22: return False
        if lo<=hcp(h)<=hi:
            if suit=='♣': return sl(h,'♣')>=3 and sl(h,'♣')>=sl(h,'♦')
            if suit=='♦': return sl(h,'♦')>=3 and sl(h,'♦')>sl(h,'♣')
        return False
    return c

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחת 1♥ — כל שילובי כוח')
print('='*65)

# חלש 12-14
def chk(lo,hi,resp_bid,opening='1♥'):
    def f(hands, bids):
        if not bids or bids[0]!=opening: return False,f'פתיחה {bids[0]} במקום {opening}'
        if len(bids)<2 or bids[1]!=resp_bid: return False,f'תשובה {bids[1] if len(bids)>1 else "?"} במקום {resp_bid}'
        return True,''
    return f

for lo,hi,lbl in [(12,14,'חלש'),(15,17,'בינוני'),(18,21,'חזק')]:
    s = lo*100
    run(f'1♥ {lbl} + תמיכה חלשה (2♥)',
        {'N':op_1h(lo,hi),'S':lambda h:sl(h,'♥')>=3 and 6<=hcp(h)<=9, **ew_weak},
        chk(lo,hi,'2♥'), seed_start=s+10)
    run(f'1♥ {lbl} + תמיכה בינונית (3♥)',
        {'N':op_1h(lo,hi),'S':lambda h:sl(h,'♥')>=3 and 10<=hcp(h)<=12, **ew_weak},
        chk(lo,hi,'3♥'), seed_start=s+20)
    run(f'1♥ {lbl} + תמיכה חזקה (4♥)',
        {'N':op_1h(lo,hi),'S':lambda h:sl(h,'♥')>=3 and 13<=hcp(h)<=16, **ew_weak},
        chk(lo,hi,'4♥'), seed_start=s+30)
    run(f'1♥ {lbl} + 1NT (6-10, מאוזן)',
        {'N':op_1h(lo,hi),'S':lambda h:is_balanced(h) and 6<=hcp(h)<=10 and sl(h,'♠')<4 and sl(h,'♥')<3, **ew_weak},
        lambda hands,bids: (bids[1]=='1NT','תשובה '+str(bids[1] if len(bids)>1 else '?')+' במקום 1NT') if len(bids)>0 and bids[0]=='1♥' else (False,'פתיחה שגויה'), seed_start=s+40)
    run(f'1♥ {lbl} + 1♠ (4+♠, 6+)',
        {'N':op_1h(lo,hi),'S':lambda h:sl(h,'♠')>=4 and 6<=hcp(h)<=12 and sl(h,'♥')<3, **ew_weak},
        chk(lo,hi,'1♠'), seed_start=s+50)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחת 1♠ — כל שילובי כוח')
print('='*65)

for lo,hi,lbl in [(12,14,'חלש'),(15,17,'בינוני'),(18,21,'חזק')]:
    s = 4000+lo*100
    run(f'1♠ {lbl} + תמיכה חלשה (2♠)',
        {'N':op_1s(lo,hi),'S':lambda h:sl(h,'♠')>=3 and 6<=hcp(h)<=9 and sl(h,'♥')<4, **ew_weak},
        chk(lo,hi,'2♠','1♠'), seed_start=s+10)
    run(f'1♠ {lbl} + תמיכה בינונית (3♠)',
        {'N':op_1s(lo,hi),'S':lambda h:sl(h,'♠')>=3 and 10<=hcp(h)<=12 and sl(h,'♥')<4, **ew_weak},
        chk(lo,hi,'3♠','1♠'), seed_start=s+20)
    run(f'1♠ {lbl} + תמיכה חזקה (4♠)',
        {'N':op_1s(lo,hi),'S':lambda h:sl(h,'♠')>=3 and 13<=hcp(h)<=16 and sl(h,'♥')<4, **ew_weak},
        chk(lo,hi,'4♠','1♠'), seed_start=s+30)
    run(f'1♠ {lbl} + 1NT (6-10)',
        {'N':op_1s(lo,hi),'S':lambda h:is_balanced(h) and 6<=hcp(h)<=10 and sl(h,'♠')<3, **ew_weak},
        lambda hands,bids: (bids[1]=='1NT',f'תשובה {bids[1] if len(bids)>1 else "?"} במקום 1NT') if len(bids)>0 and bids[0]=='1♠' else (False,'פתיחה שגויה'), seed_start=s+40)
    run(f'1♠ {lbl} + 2♥ (4♥, אין ♠)',
        {'N':op_1s(lo,hi),'S':lambda h:sl(h,'♥')>=4 and sl(h,'♠')<3 and sl(h,'♥')<6 and 11<=hcp(h)<=15, **ew_weak},
        chk(lo,hi,'2♥','1♠'), seed_start=s+50)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחת 1♣/1♦ — תשובות')
print('='*65)

for suit,lbl in [('♣','1♣'),('♦','1♦')]:
    s = 7000 if suit=='♣' else 8000
    open_bid = f'1{suit}'
    def chk_min(ob, rb):
        def f(hands, bids):
            if not bids or bids[0]!=ob: return False,f'פתיחה {bids[0]} במקום {ob}'
            if len(bids)<2 or bids[1]!=rb: return False,f'תשובה {bids[1] if len(bids)>1 else "?"} במקום {rb}'
            return True,''
        return f
    run(f'{lbl} + 1♥ (4+♥, 6+)',
        {'N':op_1m(suit,12,21),'S':lambda h:sl(h,'♥')>=4 and 6<=hcp(h)<=12, **ew_quiet},
        chk_min(open_bid,'1♥'), seed_start=s+10)
    run(f'{lbl} + 1♠ (4+♠, אין ♥, 6+)',
        {'N':op_1m(suit,12,21),'S':lambda h:sl(h,'♠')>=4 and sl(h,'♥')<4 and 6<=hcp(h)<=12, **ew_quiet},
        chk_min(open_bid,'1♠'), seed_start=s+20)
    run(f'{lbl} + 1NT (6-10, מאוזן)',
        {'N':op_1m(suit,12,21),'S':lambda h,su=suit:is_balanced(h) and 6<=hcp(h)<=10 and sl(h,'♥')<4 and sl(h,'♠')<4 and sl(h,su)<5, **ew_quiet},
        chk_min(open_bid,'1NT'), seed_start=s+30)
    run(f'{lbl} + 2NT (11-12, מאוזן)',
        {'N':op_1m(suit,12,21),'S':lambda h:is_balanced(h) and 11<=hcp(h)<=12 and sl(h,'♥')<4 and sl(h,'♠')<4 and sl(h,'♣')<5 and sl(h,'♦')<5, **ew_quiet},
        chk_min(open_bid,'2NT'), seed_start=s+40)
    run(f'{lbl} + 3NT (13-15, מאוזן)',
        {'N':op_1m(suit,12,21),'S':lambda h:is_balanced(h) and 13<=hcp(h)<=15 and sl(h,'♥')<4 and sl(h,'♠')<4 and sl(h,'♣')<5 and sl(h,'♦')<5, **ew_weak},
        chk_min(open_bid,'3NT'), seed_start=s+50)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחת 1NT — כל התשובות')
print('='*65)

def chk1nt(rb):
    def f(hands, bids):
        if not bids or bids[0]!='1NT': return False,f'פתיחה {bids[0]} במקום 1NT'
        if len(bids)<2 or bids[1]!=rb: return False,f'תשובה {bids[1] if len(bids)>1 else "?"} במקום {rb}'
        return True,''
    return f

run('1NT + פס (< 6)',
    {'N':op_1nt(),'S':lambda h:hcp(h)<=5 and sl(h,'♥')<5 and sl(h,'♠')<5, **ew_weak},
    lambda hands,bids: (len(bids)==1 and bids[0]=='1NT' or (len(bids)>1 and bids[1]=='פס'),
                        f'תשובה {bids[1] if len(bids)>1 else "?"} במקום פס'),
    seed_start=9100)
run('1NT + 2♣ סטיימן (4♥/4♠, אין 5)',
    {'N':op_1nt(),'S':lambda h:(sl(h,'♥')>=4 or sl(h,'♠')>=4) and sl(h,'♥')<5 and sl(h,'♠')<5 and 8<=hcp(h)<=12 and sum(1 for su in ['♠','♥','♦','♣'] if sl(h,su)>=4)>=2, **ew_weak},
    chk1nt('2♣'), seed_start=9200)
run('1NT + 2♦ טרנספר ♥ (5+♥)',
    {'N':op_1nt(),'S':lambda h:sl(h,'♥')>=5 and 4<=hcp(h)<=12, **ew_weak},
    chk1nt('2♦'), seed_start=9300)
run('1NT + 2♥ טרנספר ♠ (5+♠)',
    {'N':op_1nt(),'S':lambda h:sl(h,'♠')>=5 and sl(h,'♥')<5 and 4<=hcp(h)<=12, **ew_weak},
    chk1nt('2♥'), seed_start=9400)
run('1NT + 3NT (10-15, מאוזן)',
    {'N':op_1nt(),'S':lambda h:is_balanced(h) and 10<=hcp(h)<=15 and sl(h,'♥')<4 and sl(h,'♠')<4, **ew_weak},
    chk1nt('3NT'), seed_start=9500)
run('1NT + 4NT (16-17, הזמנה לסלאם)',
    {'N':op_1nt(),'S':lambda h:is_balanced(h) and 16<=hcp(h)<=17 and sl(h,'♥')<4 and sl(h,'♠')<4, **ew_weak},
    chk1nt('4NT'), seed_start=9600)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחות חלשות 2♥/2♠/2♦')
print('='*65)

for suit,lbl,s in [('♥','2♥',10000),('♠','2♠',10500),('♦','2♦',11000)]:
    ob = f'2{suit}'
    def c_weak(su=suit):
        return lambda h: sl(h,su)==6 and 6<=hcp(h)<=9 and suit_hcp(h,su)>=5 and sl(h,'♠')<5 if su!='♠' else sl(h,'♠')==6 and 6<=hcp(h)<=9 and suit_hcp(h,'♠')>=5
    def chk_weak(ob_=ob):
        def f(hands, bids):
            if not bids or bids[0]!=ob_: return False,f'פתיחה {bids[0]} במקום {ob_}'
            return True,''
        return f
    run(f'{lbl} פתיחה חלשה (6-9, 6{suit})',
        {'N':c_weak(), **ew_silent},
        chk_weak(), seed_start=s)
    run(f'{lbl} + פס (S חלש <10)',
        {'N':c_weak(),'S':lambda h:hcp(h)<=9, **ew_silent},
        lambda hands,bids,ob_=ob: (bids[0]==ob_ and (len(bids)<2 or bids[1]=='פס'),
            f'{bids[0]} → {bids[1] if len(bids)>1 else "?"}'), seed_start=s+100)
    run(f'{lbl} + 4{suit} (S חזק 17+)',
        {'N':c_weak(),'S':lambda h,su=suit:hcp(h)>=17 and sl(h,su)>=2, **ew_silent},
        lambda hands,bids,ob_=ob,su_=suit: (bids[0]==ob_ and len(bids)>1 and bids[1]==f'4{su_}',
            f'תשובה {bids[1] if len(bids)>1 else "?"} במקום 4{su_}'), seed_start=s+200)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פרי-אמפטים 3x / 4x')
print('='*65)

for suit,cards,level,s in [('♥',7,3,12000),('♠',7,3,12500),('♦',7,3,13000),('♣',7,3,13500),
                             ('♥',8,4,14000),('♠',8,4,14500)]:
    ob = f'{level}{suit}'
    def c_pre(su=suit,ca=cards,lv=level):
        if lv == 3:
            return lambda h: sl(h,su)==7 and 6<=hcp(h)<=9 and suit_hcp(h,su)>=5
        else:
            return lambda h: sl(h,su)>=8 and 6<=hcp(h)<=9 and suit_hcp(h,su)>=6
    def chk_pre(ob_=ob):
        def f(hands, bids):
            if not bids or bids[0]!=ob_: return False,f'פתיחה {bids[0]} במקום {ob_}'
            return True,''
        return f
    run(f'פרי-אמפט {ob} ({cards}+{suit}, 6-9)',
        {'N':c_pre(), **ew_silent},
        chk_pre(), seed_start=s)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחת 2NT (20-22)')
print('='*65)

def op_2nt(): return lambda h: is_balanced(h) and 20<=hcp(h)<=22

def chk2nt(rb):
    def f(hands, bids):
        if not bids or bids[0]!='2NT': return False,f'פתיחה {bids[0]} במקום 2NT'
        if len(bids)<2 or bids[1]!=rb: return False,f'תשובה {bids[1] if len(bids)>1 else "?"} במקום {rb}'
        return True,''
    return f

run('2NT + 3♣ סטיימן',
    {'N':op_2nt(),'S':lambda h:(sl(h,'♥')>=4 or sl(h,'♠')>=4) and sl(h,'♥')<5 and sl(h,'♠')<5 and 4<=hcp(h)<=10, **ew_weak},
    chk2nt('3♣'), seed_start=15000)
run('2NT + 3♦ טרנספר ♥',
    {'N':op_2nt(),'S':lambda h:sl(h,'♥')>=5 and 4<=hcp(h)<=10, **ew_weak},
    chk2nt('3♦'), seed_start=15100)
run('2NT + 3♥ טרנספר ♠',
    {'N':op_2nt(),'S':lambda h:sl(h,'♠')>=5 and sl(h,'♥')<5 and 4<=hcp(h)<=10, **ew_weak},
    chk2nt('3♥'), seed_start=15200)
run('2NT + 3NT ישיר',
    {'N':op_2nt(),'S':lambda h:is_balanced(h) and 4<=hcp(h)<=10 and sl(h,'♥')<4 and sl(h,'♠')<4, **ew_weak},
    chk2nt('3NT'), seed_start=15300)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print('  פתיחת 2♣ חזקה (23+)')
print('='*65)

def op_2c(): return lambda h: hcp(h)>=23

def chk2c(rb):
    def f(hands, bids):
        if not bids or bids[0]!='2♣': return False,f'פתיחה {bids[0]} במקום 2♣'
        if len(bids)<2 or bids[1]!=rb: return False,f'תשובה {bids[1] if len(bids)>1 else "?"} במקום {rb}'
        return True,''
    return f

run('2♣ + 2♦ שלילי (0-6)',
    {'N':op_2c(),'S':lambda h:hcp(h)<=6, **ew_weak},
    chk2c('2♦'), seed_start=16000)
run('2♣ + 2♥ חיובי (5+♥, 8+)',
    {'N':op_2c(),'S':lambda h:sl(h,'♥')>=5 and 8<=hcp(h)<=12, **ew_weak},
    chk2c('2♥'), seed_start=16100)
run('2♣ + 2♠ חיובי (5+♠, 8+)',
    {'N':op_2c(),'S':lambda h:sl(h,'♠')>=5 and sl(h,'♥')<5 and 8<=hcp(h)<=12, **ew_weak},
    chk2c('2♠'), seed_start=16200)
run('2♣ + 2NT (8+, מאוזן)',
    {'N':op_2c(),'S':lambda h:is_balanced(h) and 8<=hcp(h)<=12 and sl(h,'♥')<5 and sl(h,'♠')<5 and sl(h,'♣')<5 and sl(h,'♦')<5, **ew_weak},
    chk2c('2NT'), seed_start=16300)

# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*65)
print(f'  סיכום: {passed}/{total} עברו')
print('='*65)
if errors:
    print(f'  {len(errors)} שגיאות:')
    for e in errors[:20]:
        print(f'  • {e}')
    if len(errors) > 20:
        print(f'  ... ו-{len(errors)-20} נוספות')
else:
    print('  ✓ כל הבדיקות עברו!')
print('='*65)
