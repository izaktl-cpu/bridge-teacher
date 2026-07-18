# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'D:/bridge-teacher')

from bridge_teacher import (
    hcp, sorted_len, deal_one_board,
    pState, init_state, cfg, recompute_opener, recompute_responder, SUITS
)

N_DEALS = 200
errors = []

def reset():
    for p in 'NESW':
        pState[p] = init_state()

def set_opener(p, open_key, open_suit=None, strength=None, open_type=None):
    reset()
    st = pState[p]
    st['strengthKey'] = strength
    st['openKey']     = open_key
    st['openSuit']    = open_suit
    st['openType']    = open_type or open_key
    st['mode']        = 'opener'
    recompute_opener(p)

def set_responder(p, resp_strength=None, resp_type=None, resp_suit=None):
    st = pState[p]
    st['mode']         = 'responder'
    st['respStrength'] = resp_strength
    st['respType']     = resp_type
    st['respSuit']     = resp_suit
    recompute_responder(p)

def suit_len(hand, suit):
    return sum(1 for c in hand if c['s'] == suit)

def run_test(name, setup_fn, check_fn, n=N_DEALS):
    setup_fn()
    ok = fail = 0
    for _ in range(n):
        h = deal_one_board()
        if h is None:
            errors.append(f'{name}: לא הצליח לחלק')
            return
        result, msg = check_fn(h)
        if result: ok += 1
        else:
            fail += 1
            errors.append(f'{name}: {msg}')
            if fail >= 3: break
    icon = 'OK' if fail == 0 else 'FAIL'
    print(f'[{icon}] {name}: {ok}/{ok+fail}')

# TEST 1: 1NT
def setup_1nt():
    cfg['ntMin'] = 15; cfg['ntMax'] = 17
    set_opener('N', 'nt', None, None, 'nt')

def check_1nt(h):
    hand = h['N']; pts = hcp(hand)
    if not (15 <= pts <= 17): return False, f'HCP={pts}'
    sl = sorted_len(hand)
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'חלוקה {sl}'
    return True, ''

run_test('1NT פותח (15-17 מאוזן)', setup_1nt, check_1nt)

# TEST 2: 1NT + משיב 2NT
def setup_1nt_2nt():
    cfg['ntMin'] = 15; cfg['ntMax'] = 17
    set_opener('N', 'nt', None, None, 'nt')
    pState['S']['openType'] = 'nt'
    set_responder('S', 'בינוני 10-12', '2nt')

def check_1nt_2nt(h):
    pts_n = hcp(h['N']); pts_s = hcp(h['S'])
    if not (15 <= pts_n <= 17): return False, f'N HCP={pts_n}'
    if not (10 <= pts_s <= 12): return False, f'S HCP={pts_s}'
    sl = sorted_len(h['N'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'N חלוקה {sl}'
    return True, ''

run_test('1NT + 2NT משיב (10-12)', setup_1nt_2nt, check_1nt_2nt)

# TEST 3: פתיחה ב♥
def setup_heart():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '\u2665', None, 'major')

def check_heart(h):
    hand = h['N']
    if suit_len(hand, '\u2665') < 5: return False, f'H={suit_len(hand,chr(9829))}'
    return True, ''

run_test('פתיחה ב♥ (5+)', setup_heart, check_heart)

# TEST 4: פתיחה ב♦ — ♦>=♣, אין 5 מיגור
def setup_diamond():
    cfg['minorLen'] = 3
    set_opener('N', 'minor', '\u2666', None, 'minor')

def check_diamond(h):
    hand = h['N']
    d = suit_len(hand, '\u2666'); c = suit_len(hand, '\u2663')
    h2 = suit_len(hand, '\u2665'); s2 = suit_len(hand, '\u2660')
    if d < 3: return False, f'D={d}'
    if d < c: return False, f'D={d} < C={c}'
    if h2 >= 5: return False, f'H={h2} (יש 5 לבבות)'
    if s2 >= 5: return False, f'S={s2} (יש 5 עלות)'
    return True, ''

run_test('פתיחה ב♦ (♦>=♣, אין 5 מיגור)', setup_diamond, check_diamond)

# TEST 5: פתיחה ב♣ — ♣>=♦, אין 5 מיגור
def setup_club():
    cfg['minorLen'] = 3
    set_opener('N', 'minor', '\u2663', None, 'minor')

def check_club(h):
    hand = h['N']
    c = suit_len(hand, '\u2663'); d = suit_len(hand, '\u2666')
    h2 = suit_len(hand, '\u2665'); s2 = suit_len(hand, '\u2660')
    if c < 3: return False, f'C={c}'
    if c < d: return False, f'C={c} < D={d}'
    if h2 >= 5: return False, f'H={h2}'
    if s2 >= 5: return False, f'S={s2}'
    return True, ''

run_test('פתיחה ב♣ (♣>=♦, אין 5 מיגור)', setup_club, check_club)

# TEST 6: תמיכה ב♥ — 3+ קלפים, 6-9 נקודות
def setup_support():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '\u2665', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '\u2665'
    set_responder('S', 'חלש 6-9', 'support', '\u2665')

def check_support(h):
    if suit_len(h['N'], '\u2665') < 5: return False, f'N H={suit_len(h["N"],chr(9829))}'
    if suit_len(h['S'], '\u2665') < 3: return False, f'S H={suit_len(h["S"],chr(9829))} (צריך 3+)'
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    return True, ''

run_test('תמיכה ב♥ (3+♥, 6-9 נק)', setup_support, check_support)

# TEST 7: תשובה 1♠ אחרי 1♥
def setup_resp_1s():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '\u2665', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '\u2665'
    set_responder('S', 'בינוני 10-12', '1s', '\u2660')

def check_resp_1s(h):
    if suit_len(h['S'], '\u2660') < 4: return False, f'S S={suit_len(h["S"],chr(9824))}'
    pts = hcp(h['S'])
    if not (10 <= pts <= 12): return False, f'S HCP={pts}'
    return True, ''

run_test('תשובה 1♠ אחרי 1♥ (4+♠, 10-12)', setup_resp_1s, check_resp_1s)

# TEST 8: פתיחה ב♣ — ♣>♦ או ♣=♦=3
def setup_club2():
    cfg['minorLen'] = 3
    set_opener('N', 'minor', '♣', None, 'minor')

def check_club2(h):
    hand = h['N']
    cl = suit_len(hand,'♣'); di = suit_len(hand,'♦')
    if cl < 3: return False, f'♣={cl}'
    if not (cl > di or (cl == di == 3)):
        return False, f'♣={cl} ♦={di} — צריך ♣>♦ או שניהם 3'
    if suit_len(hand,'♥')>=5 or suit_len(hand,'♠')>=5:
        return False, 'יש 5 מיגור'
    return True, ''

run_test('פתיחה ב♣ — ♣>♦ או 3=3', setup_club2, check_club2)

# TEST 9: פתיחה ב♦ — ♦>♣ או ♦=♣≥4
def setup_diamond2():
    cfg['minorLen'] = 3
    set_opener('N', 'minor', '♦', None, 'minor')

def check_diamond2(h):
    hand = h['N']
    cl = suit_len(hand,'♣'); di = suit_len(hand,'♦')
    if di < 3: return False, f'♦={di}'
    if not (di > cl or (di == cl and di >= 4)):
        return False, f'♣={cl} ♦={di} — צריך ♦>♣ או שניהם 4+'
    if suit_len(hand,'♥')>=5 or suit_len(hand,'♠')>=5:
        return False, 'יש 5 מיגור'
    return True, ''

run_test('פתיחה ב♦ — ♦>♣ או 4+=4+', setup_diamond2, check_diamond2)

# TEST 8: פתיחה ב♠ עם 15-17 — חייב לא מאוזן
def setup_spade_15_17():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♠', 'בינוני 15-17', 'major')

def check_spade_15_17(h):
    hand = h['N']
    pts = hcp(hand)
    if not (15 <= pts <= 17): return False, f'HCP={pts}'
    if suit_len(hand, '♠') < 5: return False, f'S={suit_len(hand,"♠")}'
    sl = sorted_len(hand)
    if sl in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]:
        return False, f'יד מאוזנת {sl} — חייב 1NT'
    return True, ''

run_test('פתיחה ב♠ 15-17 — לא מאוזן', setup_spade_15_17, check_spade_15_17)

# TEST 11: 1♠ — 12-21 נק', 5+ ספייד, לא מאוזן אם 15-17
def setup_spade_full():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♠', None, 'major')

def check_spade_full(h):
    hand = h['N']; pts = hcp(hand)
    if not (12 <= pts <= 21): return False, f'HCP={pts}'
    if suit_len(hand,'♠') < 5: return False, f'♠={suit_len(hand,"♠")}'
    return True, ''

run_test('1♠ (12-21, 5+♠)', setup_spade_full, check_spade_full)

# TEST 12: 1♥ — 12-21 נק', 5+ לבבות
def setup_heart_full():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♥', None, 'major')

def check_heart_full(h):
    hand = h['N']; pts = hcp(hand)
    if not (12 <= pts <= 21): return False, f'HCP={pts}'
    if suit_len(hand,'♥') < 5: return False, f'♥={suit_len(hand,"♥")}'
    return True, ''

run_test('1♥ (12-21, 5+♥)', setup_heart_full, check_heart_full)

# TEST 13: 1♦ — 12-21 נק'
def setup_diamond_hcp():
    cfg['minorLen'] = 3
    set_opener('N', 'minor', '♦', None, 'minor')

def check_diamond_hcp(h):
    hand = h['N']; pts = hcp(hand)
    if not (12 <= pts <= 21): return False, f'HCP={pts}'
    return True, ''

run_test('1♦ (12-21 נק\')', setup_diamond_hcp, check_diamond_hcp)

# TEST 14: 1♣ — 12-21 נק'
def setup_club_hcp():
    cfg['minorLen'] = 3
    set_opener('N', 'minor', '♣', None, 'minor')

def check_club_hcp(h):
    hand = h['N']; pts = hcp(hand)
    if not (12 <= pts <= 21): return False, f'HCP={pts}'
    return True, ''

run_test('1♣ (12-21 נק\')', setup_club_hcp, check_club_hcp)

# TEST 15: 1♠ חלש — 12-14 נק', 5+ ספייד
def setup_spade_weak():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♠', 'חלש 12-14', 'major')

def check_spade_weak(h):
    hand = h['N']; pts = hcp(hand)
    if not (12 <= pts <= 14): return False, f'HCP={pts}'
    if suit_len(hand,'♠') < 5: return False, f'♠={suit_len(hand,"♠")}'
    return True, ''

run_test('1♠ חלש (12-14, 5+♠)', setup_spade_weak, check_spade_weak)

# TEST 16: 1♠ חזק — 18-21 נק', 5+ ספייד
def setup_spade_strong():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♠', 'חזק 18-21', 'major')

def check_spade_strong(h):
    hand = h['N']; pts = hcp(hand)
    if not (18 <= pts <= 21): return False, f'HCP={pts}'
    if suit_len(hand,'♠') < 5: return False, f'♠={suit_len(hand,"♠")}'
    return True, ''

run_test('1♠ חזק (18-21, 5+♠)', setup_spade_strong, check_spade_strong)

# ── תשובות למיגור ──────────────────────────────────────────────────────────────

# TEST 17: תמיכה 3♥ אחרי 1♥ (10-12 נק', 3+♥)
def setup_support_h_med():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♥', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '♥'
    set_responder('S', 'בינוני 10-12', 'support', '♥')

def check_support_h_med(h):
    pts = hcp(h['S'])
    if not (10 <= pts <= 12): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♥') < 3: return False, f'♥={suit_len(h["S"],"♥")}'
    if suit_len(h['N'],'♥') < 5: return False, f'N ♥={suit_len(h["N"],"♥")}'
    return True, ''

run_test('3♥ תמיכה (10-12, 3+♥)', setup_support_h_med, check_support_h_med)

# TEST 18: תמיכה 4♥ אחרי 1♥ (13+ נק', 3+♥)
def setup_support_h_str():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♥', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '♥'
    set_responder('S', 'חזק 13+', 'support', '♥')

def check_support_h_str(h):
    pts = hcp(h['S'])
    if not (13 <= pts <= 37): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♥') < 3: return False, f'♥={suit_len(h["S"],"♥")}'
    return True, ''

run_test('4♥ תמיכה (13+, 3+♥)', setup_support_h_str, check_support_h_str)

# TEST 19: תמיכה 2♠ אחרי 1♠ (6-9 נק', 3+♠)
def setup_support_s():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♠', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '♠'
    set_responder('S', 'חלש 6-9', 'support', '♠')

def check_support_s(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♠') < 3: return False, f'♠={suit_len(h["S"],"♠")}'
    if suit_len(h['N'],'♠') < 5: return False, f'N ♠={suit_len(h["N"],"♠")}'
    return True, ''

run_test('2♠ תמיכה (6-9, 3+♠)', setup_support_s, check_support_s)

# TEST 20: 1NT אחרי 1♥ (6-10 נק', אין מיגור 4)
def setup_1nt_after_heart():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♥', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '♥'
    set_responder('S', 'חלש 6-9', '1nt', None)

def check_1nt_after_heart(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    sl = sorted_len(h['S'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'לא מאוזן {sl}'
    return True, ''

run_test('1NT אחרי 1♥ (6-9, מאוזן)', setup_1nt_after_heart, check_1nt_after_heart)

# TEST 21: 2NT אחרי 1♥ (11-12 נק', מאוזן)
def setup_2nt_after_heart():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♥', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '♥'
    set_responder('S', 'בינוני 10-12', '2nt', None)

def check_2nt_after_heart(h):
    pts = hcp(h['S'])
    if not (10 <= pts <= 12): return False, f'S HCP={pts}'
    sl = sorted_len(h['S'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'לא מאוזן {sl}'
    return True, ''

run_test('2NT אחרי 1♥ (10-12, מאוזן)', setup_2nt_after_heart, check_2nt_after_heart)

# TEST 22: 1♠ אחרי 1♥ (6-9 נק', 4+♠)
def setup_1s_after_heart_weak():
    cfg['majorLen'] = 5
    set_opener('N', 'major', '♥', None, 'major')
    pState['S']['openType'] = 'major'; pState['S']['openSuit'] = '♥'
    set_responder('S', 'חלש 6-9', '1s', '♠')

def check_1s_after_heart_weak(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♠') < 4: return False, f'♠={suit_len(h["S"],"♠")}'
    return True, ''

run_test('1♠ אחרי 1♥ (6-9, 4+♠)', setup_1s_after_heart_weak, check_1s_after_heart_weak)

# ── תשובות למינור ──────────────────────────────────────────────────────────────

# TEST 23: 1♥ אחרי 1♣ (6-9, 4+♥)
def setup_1h_after_club():
    set_opener('N', 'minor', '♣', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♣'
    set_responder('S', 'חלש 6-9', '1h', '♥')

def check_1h_after_club(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♥') < 4: return False, f'♥={suit_len(h["S"],"♥")}'
    return True, ''

run_test('1♥ אחרי 1♣ (6-9, 4+♥)', setup_1h_after_club, check_1h_after_club)

# TEST 24: 1♠ אחרי 1♣ (6-9, 4+♠)
def setup_1s_after_club():
    set_opener('N', 'minor', '♣', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♣'
    set_responder('S', 'חלש 6-9', '1s', '♠')

def check_1s_after_club(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♠') < 4: return False, f'♠={suit_len(h["S"],"♠")}'
    return True, ''

run_test('1♠ אחרי 1♣ (6-9, 4+♠)', setup_1s_after_club, check_1s_after_club)

# TEST 25: תמיכה 2♣ אחרי 1♣ (6-9, 5+♣)
def setup_supp_club():
    set_opener('N', 'minor', '♣', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♣'
    set_responder('S', 'חלש 6-9', 'supp-minor', '♣')

def check_supp_club(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♣') < 5: return False, f'♣={suit_len(h["S"],"♣")}'
    return True, ''

run_test('2♣ תמיכה (6-9, 5+♣)', setup_supp_club, check_supp_club)

# TEST 26: תמיכה 2♦ אחרי 1♦ (6-9, 5+♦)
def setup_supp_diamond():
    set_opener('N', 'minor', '♦', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♦'
    set_responder('S', 'חלש 6-9', 'supp-minor', '♦')

def check_supp_diamond(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♦') < 5: return False, f'♦={suit_len(h["S"],"♦")}'
    return True, ''

run_test('2♦ תמיכה (6-9, 5+♦)', setup_supp_diamond, check_supp_diamond)

# TEST 27: 1NT אחרי 1♣ (6-9)
def setup_1nt_after_club():
    set_opener('N', 'minor', '♣', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♣'
    set_responder('S', 'חלש 6-9', '1nt', None)

def check_1nt_after_club(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    sl = sorted_len(h['S'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'לא מאוזן {sl}'
    return True, ''

run_test('1NT אחרי 1♣ (6-9, מאוזן)', setup_1nt_after_club, check_1nt_after_club)

# TEST 28: 2NT אחרי 1♣ (10-12, מאוזן)
def setup_2nt_after_club():
    set_opener('N', 'minor', '♣', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♣'
    set_responder('S', 'בינוני 10-12', '2nt', None)

def check_2nt_after_club(h):
    pts = hcp(h['S'])
    if not (10 <= pts <= 12): return False, f'S HCP={pts}'
    sl = sorted_len(h['S'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'לא מאוזן {sl}'
    return True, ''

run_test('2NT אחרי 1♣ (10-12, מאוזן)', setup_2nt_after_club, check_2nt_after_club)

# TEST 29: 1♥ אחרי 1♦ (6-9, 4+♥)
def setup_1h_after_diamond():
    set_opener('N', 'minor', '♦', None, 'minor')
    pState['S']['openType'] = 'minor'; pState['S']['openSuit'] = '♦'
    set_responder('S', 'חלש 6-9', '1h', '♥')

def check_1h_after_diamond(h):
    pts = hcp(h['S'])
    if not (6 <= pts <= 9): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♥') < 4: return False, f'♥={suit_len(h["S"],"♥")}'
    return True, ''

run_test('1♥ אחרי 1♦ (6-9, 4+♥)', setup_1h_after_diamond, check_1h_after_diamond)

# ── תשובות ל-1NT ───────────────────────────────────────────────────────────────

# TEST 30: סטיימן 2♣ (8+, 4+ מיגור)
def setup_stayman():
    cfg['ntMin']=15; cfg['ntMax']=17
    set_opener('N', 'nt', None, None, 'nt')
    pState['S']['openType']='nt'
    set_responder('S', 'בינוני 10-12', 'stayman', '♥')

def check_stayman(h):
    pts = hcp(h['S'])
    if not (10 <= pts <= 12): return False, f'S HCP={pts}'
    if suit_len(h['S'],'♥') < 4 and suit_len(h['S'],'♠') < 4:
        return False, f'♥={suit_len(h["S"],"♥")} ♠={suit_len(h["S"],"♠")} — צריך 4+ מיגור'
    return True, ''

run_test('סטיימן 2♣ (10-12, 4+ מיגור)', setup_stayman, check_stayman)

# TEST 31: טרנספר ל♥ (5+♥)
def setup_trans_h():
    cfg['ntMin']=15; cfg['ntMax']=17
    set_opener('N', 'nt', None, None, 'nt')
    pState['S']['openType']='nt'
    set_responder('S', 'חלש 6-9', 'trans-h', '♥')

def check_trans_h(h):
    if suit_len(h['S'],'♥') < 5: return False, f'♥={suit_len(h["S"],"♥")}'
    return True, ''

run_test('טרנספר ♥ (5+♥)', setup_trans_h, check_trans_h)

# TEST 32: טרנספר ל♠ (5+♠)
def setup_trans_s():
    cfg['ntMin']=15; cfg['ntMax']=17
    set_opener('N', 'nt', None, None, 'nt')
    pState['S']['openType']='nt'
    set_responder('S', 'חלש 6-9', 'trans-s', '♠')

def check_trans_s(h):
    if suit_len(h['S'],'♠') < 5: return False, f'♠={suit_len(h["S"],"♠")}'
    return True, ''

run_test('טרנספר ♠ (5+♠)', setup_trans_s, check_trans_s)

# TEST 33: 3NT אחרי 1NT (10-12, מאוזן)
def setup_3nt():
    cfg['ntMin']=15; cfg['ntMax']=17
    set_opener('N', 'nt', None, None, 'nt')
    pState['S']['openType']='nt'
    set_responder('S', 'בינוני 10-12', '2nt', None)

def check_3nt(h):
    pts = hcp(h['S'])
    if not (10 <= pts <= 12): return False, f'S HCP={pts}'
    sl = sorted_len(h['S'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'לא מאוזן {sl}'
    return True, ''

run_test('2NT אחרי 1NT (10-12, מאוזן)', setup_3nt, check_3nt)

# ── פתיחות חלשות ────────────────────────────────────────────────────────────────

def weak2_setup(suit):
    reset()
    st = pState['N']
    st['mode']='opener'; st['hcpMin']=6; st['hcpMax']=9
    st['commands']=f'6+{suit}|hcp5+{suit}'

def weak2_check(suit):
    def check(h):
        hand = h['N']; pts = hcp(hand)
        if not (6 <= pts <= 9): return False, f'HCP={pts}'
        if suit_len(hand,suit) < 6: return False, f'{suit}={suit_len(hand,suit)}'
        suit_pts = sum({'A':4,'K':3,'Q':2,'J':1}.get(c['r'],0) for c in hand if c['s']==suit)
        if suit_pts < 5: return False, f'נקודות גבוהות בסדרה={suit_pts} (צריך 5+)'
        return True, ''
    return check

for s in ['♥','♠','♦']:
    run_test(f'פתיחה חלשה 2{s} (6-9, 6+{s}, 5+נק בסדרה)',
             lambda s=s: weak2_setup(s), weak2_check(s))

# ── 2NT ─────────────────────────────────────────────────────────────────────────

# TEST 37: פתיחה 2NT (20-22, מאוזן)
def setup_2nt_open():
    reset()
    st = pState['N']
    st['mode']='opener'; st['type']='balanced'
    st['hcpMin']=20; st['hcpMax']=22; st['commands']=''

def check_2nt_open(h):
    pts = hcp(h['N'])
    if not (20 <= pts <= 22): return False, f'HCP={pts}'
    sl = sorted_len(h['N'])
    if sl not in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False, f'לא מאוזן {sl}'
    return True, ''

run_test('פתיחה 2NT (20-22, מאוזן)', setup_2nt_open, check_2nt_open)

# SUMMARY
print()
if errors:
    print(f'{len(errors)} שגיאות:')
    for e in errors[:15]:
        print(f'  * {e}')
else:
    print('כל הבדיקות עברו!')
