# -*- coding: utf-8 -*-
"""
בדיקת כל השיעורים — 5 ידיים לכל שיעור, בדיקת פתיחה ותשובה ראשונה.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'D:/bridge-teacher')

from bridge_teacher import (pState, cfg, init_state, recompute_opener,
                             recompute_responder, deal_one_board, LESSON_GROUPS)
from bidding_engine import compute_auction

N_HANDS = 5
cfg_t = {'majorLen':5,'ntMin':15,'ntMax':17,'minorLen':3}

# ── הפעלת שיעור (העתק מ-_apply_lesson) ─────────────────────────────────────
def apply_lesson(n_open, n_suit, n_str, s_str, s_type, s_suit):
    for p in 'NESW': pState[p] = init_state()
    n = pState['N']
    n['mode']='opener'; n['openKey']=n_open; n['openSuit']=n_suit
    n['openType']=n_open; n['strengthKey']=n_str; n['_pendingSuit']=None
    if n_open == 'weak2':
        n['hcpMin']=6; n['hcpMax']=9; n['type']='free'; n['commands']=f'6{n_suit}|hcp5+{n_suit}'
    elif n_open == '2club':
        n['hcpMin']=23; n['hcpMax']=37; n['type']='free'; n['commands']=''
    elif n_open == '2nt_op':
        n['hcpMin']=20; n['hcpMax']=22; n['type']='balanced'; n['commands']=''
    else:
        recompute_opener('N')
    s = pState['S']
    s['mode']='responder'; s['openSuit']=n_suit; s['openType']=n_open
    s['respStrength']=s_str; s['respType']=s_type; s['respSuit']=s_suit
    if n_open == '2club' and s_str is None:
        s['hcpMin']=0; s['hcpMax']=6; s['type']='free'; s['commands']=''
    else:
        recompute_responder('S')
    nt_pass = (n_open == 'nt' and s_type is None)
    if n_open != 'weak2' and not nt_pass:
        for p in ('E','W'): pState[p]['hcpMax'] = 8

# ── מה מצפים לפתיחה ולתשובה הראשונה ───────────────────────────────────────
def expected(n_open, n_suit, s_str, s_type, s_suit):
    # פתיחה
    if   n_open == 'nt':     exp_open = '1NT'
    elif n_open == 'major':  exp_open = f'1{n_suit}'
    elif n_open == 'minor':  exp_open = f'1{n_suit}'
    elif n_open == 'weak2':  exp_open = f'2{n_suit}'
    elif n_open == '2club':  exp_open = '2♣'
    elif n_open == '2nt_op': exp_open = '2NT'
    else: exp_open = '?'

    # תשובה ראשונה — רשימת הכרזות תקינות
    if s_type is None:
        exp_resp = ['2♦'] if n_open == '2club' else ['פס']
    elif s_type == 'stayman':
        exp_resp = ['3♣'] if n_open == '2nt_op' else ['2♣']
    elif s_type == 'trans-h':
        exp_resp = ['3♦'] if n_open == '2nt_op' else ['2♦']
    elif s_type == 'trans-s':
        exp_resp = ['3♥'] if n_open == '2nt_op' else ['2♥']
    elif s_type == 'support':
        suit = s_suit or n_suit
        lvl  = {'חלש 6-9':2,'בינוני 10-12':3,'חזק 13+':4,
                'חלש 6-10':2,'בינוני 11-12':3}.get(s_str, 2)
        # אחרי פתיחה חלשה: תשובה יכולה להיות גם 3 (הזמנה) עם 10-12
        if n_open == 'weak2':
            exp_resp = [f'3{suit}', f'4{suit}', 'פס']
        else:
            exp_resp = [f'{lvl}{suit}']
    elif s_type == '1nt': exp_resp = ['1NT']
    elif s_type == '1h':
        exp_resp = ['2♥'] if n_open == '2club' else ['1♥']
    elif s_type == '1s':
        exp_resp = ['2♠'] if n_open == '2club' else ['1♠']
    elif s_type == '2nt':
        if n_open in ('major','minor'):
            exp_resp = {'בינוני 10-12':['2NT'],'בינוני 11-12':['2NT'],
                        'חזק 13+':['3NT']}.get(s_str,['2NT','3NT'])
        elif n_open == 'nt':
            exp_resp = ['2NT','3NT','4♣','4NT','6NT']  # תלוי כמה נק' בדיוק
        elif n_open == '2nt_op':
            exp_resp = ['3NT','4NT']  # 10-11→3NT, 11-12→4NT (הזמנה לסלאם)
        else: exp_resp = ['?']
    elif s_type == '2c': exp_resp = ['2♣']
    elif s_type == '2d': exp_resp = ['2♦']
    else: exp_resp = ['?']

    return exp_open, exp_resp

# ── ריצה ────────────────────────────────────────────────────────────────────
total_ok = total_fail = 0

for group_name, lessons in LESSON_GROUPS:
    print(f'\n══ {group_name} ══')
    for lesson_tuple in lessons:
        label, n_open, n_suit, n_str, s_str, s_type, s_suit = lesson_tuple
        apply_lesson(n_open, n_suit, n_str, s_str, s_type, s_suit)
        exp_open, exp_resp = expected(n_open, n_suit, s_str, s_type, s_suit)

        ok_count = fail_count = 0
        fail_msgs = []

        for _ in range(N_HANDS):
            h = deal_one_board()
            if h is None:
                fail_count += 1; fail_msgs.append('לא נמצאה חלוקה'); continue

            auction, players = compute_auction(h, 'N', dict(cfg_t))
            ns = [(b,p) for b,p in zip(auction,players) if p in ('N','S')]

            if not ns:
                fail_count += 1; fail_msgs.append('אין הכרזות NS'); continue

            act_open = ns[0][0]
            act_resp = ns[1][0] if len(ns) > 1 else 'פס'

            open_ok = (act_open == exp_open or exp_open == '?')
            resp_ok = ('?' in exp_resp) or (act_resp in exp_resp)

            if open_ok and resp_ok:
                ok_count += 1
            else:
                fail_count += 1
                if not open_ok:
                    fail_msgs.append(f'פתיחה: ציפוי {exp_open} → קיבלנו {act_open}')
                elif not resp_ok:
                    fail_msgs.append(f'תשובה: ציפוי {exp_resp} → קיבלנו {act_resp}')

        mark = '✅' if fail_count == 0 else '❌'
        line = f'  {mark} {label:28s} {ok_count}/{N_HANDS}'
        if fail_msgs:
            line += f'  ← {fail_msgs[0]}'
        print(line)
        total_ok += ok_count; total_fail += fail_count

total = total_ok + total_fail
pct = 100 * total_ok // total if total else 0
print(f'\n{"="*55}')
print(f'סיכום: {total_ok}/{total} עברו ({pct}%)')
print('='*55)
