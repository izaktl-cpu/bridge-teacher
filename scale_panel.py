# -*- coding: utf-8 -*-
"""
scale_panel.py — בדיקת עומק לכל אפשרויות הפנל ורשימת השיעורים.

מריץ כל תרחיש (פותח/משיב) בשתי השיטות (רגילה 15-17/5, אקול 12-14/4),
מחלק K ידיים לכל תרחיש, ומדווח הפרות:

  NO_DEAL       — אחוז כישלון חלוקה גבוה (over-constrained)
  HCP_OUT       — יד יצאה מחוץ לטווח המוצהר (באג מנוע — לא אמור לקרות)
  LOOSE_RANGE   — הטווח המוצהר רחב מדי (למשל משיב עד 37 = באג 35 הנק')
  SUIT_SHORT    — סדרת הפתיחה קצרה מהנדרש (לא אמור לקרות)
  NOT_LONGEST   — סדרת הפתיחה אינה הארוכה ביד (היד הייתה פותחת סדרה אחרת)
  NO_SUPPORT    — משיב-תמיכה בלי תמיכה בסדרת הפותח

הרצה:  python scale_panel.py         (סיכום)
       python scale_panel.py -v      (כל תרחיש)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

import bridge_teacher as bt

bt.MAX_TRIES = 200000   # כמו באפליקציה — כדי שתרחישים אפשריים-אך-נדירים יעברו
K = 10                  # חלוקות לכל תרחיש (הסוויפ המלא × 4 רוחות × 2 שיטות = ~960 תרחישים)
FAIL_PCT = 0.10         # מעל זה = over-constrained
SANE_RESP_MAX = 18      # משיב מעל זה = מפלצת / טווח פרוץ (אלא אם זה תרחיש סלאם, min≥16)
SANE_OPENER_MAX = 22    # פותח מעל זה חוקי רק ב-2♣(23+)/2NT(20-22)
VERBOSE = '-v' in sys.argv

SUITS = bt.SUITS


def set_cfg(major_len, nt_min, nt_max):
    bt.cfg['majorLen'] = major_len
    bt.cfg['ntMin'] = nt_min
    bt.cfg['ntMax'] = nt_max


def slen(hand, s):
    return sum(1 for x in hand if x['s'] == s)


def setup_lesson(n_open, n_suit, n_str, s_str, s_type, s_suit, opener='N'):
    """שכפול headless של _apply_lesson. הפותח בכל פוזיציה (opener)."""
    for p in 'NESW':
        bt.pState[p] = bt.init_state()
    resp = bt.PARTNER[opener]
    n = bt.pState[opener]
    n.update(mode='opener', openKey=n_open, openSuit=n_suit,
             openType=n_open, strengthKey=n_str, _pendingSuit=None)
    if n_open == 'weak2':
        n['hcpMin'] = 6; n['hcpMax'] = 9
        n['type'] = 'free'; n['commands'] = f'6{n_suit}|hcp5+{n_suit}'
    elif n_open == '2club':
        n['hcpMin'] = 23; n['hcpMax'] = 37
        n['type'] = 'free'; n['commands'] = ''
    elif n_open == '2nt_op':
        n['hcpMin'] = 20; n['hcpMax'] = 22
        n['type'] = 'balanced'; n['commands'] = ''
    else:
        bt.recompute_opener(opener)
    s = bt.pState[resp]
    s.update(mode='responder', openSuit=n_suit, openType=n_open,
             respStrength=s_str, respType=s_type, respSuit=s_suit)
    if n_open == '2club' and s_str is None:
        s['hcpMin'] = 0; s['hcpMax'] = 6
        s['type'] = 'free'; s['commands'] = ''
    else:
        bt.recompute_responder(resp)
    # אין יותר הגבלת E/W (הוסרה מ-_apply_lesson יחד עם ההכרזה האוטומטית)


def setup_panel_opener(open_key, open_suit, strength_key, resp_type=None,
                       resp_suit=None, resp_str=None, opener='N'):
    """שכפול headless של _pick_suit/_apply_opening + הגדרת משיב. הפותח בכל פוזיציה."""
    for p in 'NESW':
        bt.pState[p] = bt.init_state()
    resp = bt.PARTNER[opener]
    n = bt.pState[opener]
    n.update(mode='opener', openKey=open_key, openSuit=open_suit,
             openType=open_key, strengthKey=strength_key, _pendingSuit=None)
    bt.recompute_opener(opener)
    if resp_type is not None:
        s = bt.pState[resp]
        s.update(mode='responder', openSuit=open_suit, openType=open_key,
                 respStrength=resp_str, respType=resp_type, respSuit=resp_suit)
        bt.recompute_responder(resp)


def analyze(label):
    """מחלק K ידיים לפי pState הנוכחי ומחזיר רשומת הפרות. הפותח בכל פוזיציה."""
    print(f'   . {label}', file=sys.stderr, flush=True)
    op = next((p for p in 'NESW' if bt.pState[p]['mode'] == 'opener'), 'N')
    rp = bt.PARTNER[op]
    n_st = bt.pState[op]; s_st = bt.pState[rp]
    n_decl = (n_st['hcpMin'], n_st['hcpMax'])
    s_decl = (s_st['hcpMin'], s_st['hcpMax'])
    open_key = n_st['openKey']; open_suit = n_st['openSuit']
    resp_mode = s_st['mode'] == 'responder'
    resp_type = s_st.get('respType')
    minLen = None
    if open_key == 'major':
        minLen = bt.cfg['majorLen']
    elif open_key == 'minor':
        minLen = bt.cfg['minorLen']

    fails = 0
    n_lo, n_hi, s_lo, s_hi = 99, -1, 99, -1
    hcp_out = 0
    suit_short = 0
    long_major = 0   # NOT_LONGEST כי מיגור אחר ארוך יותר
    long_minor = 0   # NOT_LONGEST כי מינור ארוך יותר
    no_support = 0
    bad_1nt = 0      # משיב 1NT למיגור עם מיגור רביעייה

    for _ in range(K):
        h = bt.deal_one_board()
        if h is None:
            fails += 1
            continue
        oh, rh = h[op], h[rp]
        nh, sh = bt.hcp(oh), bt.hcp(rh)
        n_lo, n_hi = min(n_lo, nh), max(n_hi, nh)
        s_lo, s_hi = min(s_lo, sh), max(s_hi, sh)
        if not (n_decl[0] <= nh <= n_decl[1]):
            hcp_out += 1
        if resp_mode and not (s_decl[0] <= sh <= s_decl[1]):
            hcp_out += 1
        # פותח סדרה: אורך + "הסדרה הארוכה"
        if open_key in ('major', 'minor'):
            if open_suit:                       # סדרה ספציפית
                ol = slen(oh, open_suit)
                if ol < minLen:
                    suit_short += 1
                # אקול מינור (מיגור 4): פותח מינור אסור עם מיגור רביעייה שאינו קצר ממנו
                acol_minor = (open_key == 'minor' and bt.cfg['majorLen'] == 4)
                for s in ('♥', '♠'):
                    if s == open_suit:
                        continue
                    if slen(oh, s) > ol or (acol_minor and slen(oh, s) >= 4 and slen(oh, s) >= ol):
                        long_major += 1
                        break
                if any(slen(oh, s) > ol for s in ('♦', '♣')):
                    long_minor += 1
            elif open_key == 'major':           # מיגור גנרי
                hh, ss = slen(oh, '♥'), slen(oh, '♠')
                if max(hh, ss) < minLen:
                    suit_short += 1
                if max(slen(oh, '♦'), slen(oh, '♣')) > max(hh, ss):
                    long_minor += 1
            else:                               # מינור גנרי
                cl, di = slen(oh, '♣'), slen(oh, '♦')
                ml = max(cl, di)
                if ml < minLen:
                    suit_short += 1
                if slen(oh, '♥') >= 5 or slen(oh, '♠') >= 5:
                    long_major += 1              # 5+ מיגור → היה פותח מיגור
                elif bt.cfg['majorLen'] == 4 and max(slen(oh, '♥'), slen(oh, '♠')) >= ml \
                        and max(slen(oh, '♥'), slen(oh, '♠')) >= 4:
                    long_major += 1              # אקול: מיגור 4 ≥ המינור → מיגור
        # משיב-תמיכה: יש תמיכה בסדרת הפותח?
        if resp_type == 'support':
            om = open_suit
            if om is None and open_key == 'major':   # גנרי — הסדרה בפועל
                hh, ss = slen(oh, '♥'), slen(oh, '♠')
                om = '♠' if ss >= hh else '♥'
            if om and slen(rh, om) < 3:
                no_support += 1
        # משיב 1NT למיגור: אין תמיכה רביעייה במיגור הפותח, ואין מיגור רביעייה
        # שאפשר להכריז ב-1-לבל (מעל 1♥ → 4 ספייד=1♠). מעל 1♠ הרט רביעייה מותר.
        if resp_type == '1nt' and open_key == 'major':
            om = open_suit
            if om is None:                       # גנרי — המיגור בפועל
                om = '♠' if slen(oh, '♠') >= slen(oh, '♥') else '♥'
            if slen(rh, om) >= 4:                # תמיכה רביעייה
                bad_1nt += 1
            elif om == '♥' and slen(rh, '♠') >= 4:   # היה מכריז 1♠
                bad_1nt += 1

    dealt = K - fails
    viol = []
    if fails / K > FAIL_PCT:
        viol.append(f'NO_DEAL {fails}/{K}')
    if hcp_out:
        viol.append(f'HCP_OUT {hcp_out}')
    # טווח פרוץ — לפי המוצהר; מדלגים על תרחישי סלאם מכוונים (min≥16)
    if resp_mode and s_decl[1] > SANE_RESP_MAX and s_decl[0] < 16:
        viol.append(f'LOOSE_RANGE resp={s_decl}')
    if open_key not in ('nt',) and n_decl[1] > SANE_OPENER_MAX and open_key not in ('2club', '2nt_op'):
        # openKey כאן הוא 'major'/'minor'; 2club/2nt_op מגיעים דרך openType
        if bt.pState['N'].get('openType') not in ('2club', '2nt_op', 'weak2'):
            viol.append(f'LOOSE_RANGE opener={n_decl}')
    if suit_short:
        viol.append(f'SUIT_SHORT {suit_short}')
    if long_minor:
        viol.append(f'LONG_MINOR {long_minor}/{dealt}')   # פותח מיגור/מינור עם מינור ארוך יותר
    if long_major:
        viol.append(f'LONG_MAJOR {long_major}/{dealt}')   # פותח עם מיגור אחר ארוך יותר
    if no_support:
        viol.append(f'NO_SUPPORT {no_support}')
    if bad_1nt:
        viol.append(f'BAD_1NT {bad_1nt}')   # משיב 1NT עם מיגור רביעייה

    rec = dict(label=label, fails=fails, dealt=dealt,
               n_decl=n_decl, s_decl=s_decl if resp_mode else None,
               n_obs=(n_lo, n_hi), s_obs=(s_lo, s_hi) if resp_mode else None,
               viol=viol)
    return rec


def report(recs, title):
    print(f'\n{"="*70}\n{title}\n{"="*70}')
    bad = [r for r in recs if r['viol']]
    for r in recs:
        if VERBOSE or r['viol']:
            tag = '  '.join(r['viol']) if r['viol'] else 'ok'
            nobs = f"N{r['n_obs']}"
            sobs = f" S{r['s_obs']}" if r['s_obs'] else ''
            print(f"  [{'FAIL' if r['viol'] else 'ok '}] {r['label']:<32} {nobs}{sobs}  {tag}")
    print(f"  -> {len(bad)}/{len(recs)} תרחישים עם הפרות")
    return bad


def run_lessons():
    """כל השיעורים × 2 שיטות × 4 רוחות פותח."""
    all_bad = []
    for cfg_name, ml, nmin, nmax in [('רגילה 15-17/5', 5, 15, 17), ('אקול 12-14/4', 4, 12, 14)]:
        set_cfg(ml, nmin, nmax)
        for opener in 'NESW':
            recs = []
            for group, items in bt.LESSON_GROUPS:
                for tup in items:
                    label, n_open, n_suit, n_str, s_str, s_type, s_suit = tup
                    setup_lesson(n_open, n_suit, n_str, s_str, s_type, s_suit, opener=opener)
                    recs.append(analyze(f'[{cfg_name} פותח={opener}] {group}:{label}'))
            all_bad += report(recs, f'שיעורים — {cfg_name} · פותח={opener}')
    return all_bad


def run_panel():
    """כל צירוף פותח×תגובה שהפאנל מאפשר, בשתי השיטות."""
    all_bad = []
    configs = [('רגילה 15-17/5', 5, 15, 17), ('אקול 12-14/4', 4, 12, 14)]
    strengths = ['חלש 12-14', 'בינוני 15-17', 'חזק 18-21']
    # (resp_type, resp_str, resp_suit) לכל סוג פותח — לפי כפתורי _build_resp
    NT_RESP = [('stayman', 'חזק 10+', '♥'), ('trans-h', 'חלש 0-7', '♥'),
               ('trans-s', 'חלש 0-7', '♠'), ('2nt', 'חזק 10+', None), (None, 'חלש 0-7', None)]
    MAJ_RESP = [('support', 'חזק 13+', None), ('1nt', 'חלש 6-9', None), ('2nt', 'בינוני 10-12', None)]
    MIN_RESP = [('1h', 'חלש 6-10', '♥'), ('1s', 'חלש 6-10', '♠'), ('1nt', 'חלש 6-10', None),
                ('2nt', 'בינוני 11-12', None), ('supp-minor', 'בינוני 11-12', None)]
    for cfg_name, ml, nmin, nmax in configs:
        set_cfg(ml, nmin, nmax)
        for opener in 'NESW':
            recs = []
            # פותח NT + כל התגובות
            for rt, rstr, rsuit in NT_RESP:
                setup_panel_opener('nt', None, None, resp_type=rt, resp_suit=rsuit, resp_str=rstr, opener=opener)
                recs.append(analyze(f'NT→{rt}'))
            # מיגור גנרי + כל התגובות
            for st in strengths:
                for rt, rstr, _ in MAJ_RESP:
                    setup_panel_opener('major', None, st, resp_type=rt, resp_str=rstr, opener=opener)
                    recs.append(analyze(f'מיגור-גנרי {st}→{rt}'))
            # מינור גנרי + כל התגובות
            for st in strengths:
                for rt, rstr, rsuit in MIN_RESP:
                    setup_panel_opener('minor', None, st, resp_type=rt, resp_suit=rsuit, resp_str=rstr, opener=opener)
                    recs.append(analyze(f'מינור-גנרי {st}→{rt}'))
            # מיגור ספציפי + כל התגובות
            for suit in ('♥', '♠'):
                for st in strengths:
                    for rt, rstr, _ in MAJ_RESP:
                        rsuit = suit if rt == 'support' else None
                        setup_panel_opener('major', suit, st, resp_type=rt, resp_suit=rsuit, resp_str=rstr, opener=opener)
                        recs.append(analyze(f'מיגור {suit} {st}→{rt}'))
            # מינור ספציפי + כל התגובות
            for suit in ('♣', '♦'):
                for st in strengths:
                    for rt, rstr, rsuit in MIN_RESP:
                        rs = suit if rt == 'supp-minor' else rsuit
                        setup_panel_opener('minor', suit, st, resp_type=rt, resp_suit=rs, resp_str=rstr, opener=opener)
                        recs.append(analyze(f'מינור {suit} {st}→{rt}'))
            all_bad += report(recs, f'פאנל — {cfg_name} · פותח={opener}')
    return all_bad


def run_worksheet():
    """כל תרחישי WORKSHEET_PANEL (פנל דפי-העבודה החדש) × 2 שיטות × 4 רוחות."""
    all_bad = []
    for cfg_name, ml, nmin, nmax in [('רגילה 15-17/5', 5, 15, 17), ('אקול 12-14/4', 4, 12, 14)]:
        set_cfg(ml, nmin, nmax)
        for opener in 'NESW':
            recs = []
            for item in bt.WORKSHEET_PANEL:
                if item[0] != 'b':
                    continue
                labelspec, scenarios = item[1], item[2]
                blabel = labelspec if isinstance(labelspec, str) else ''.join(labelspec[1:])
                for sc in scenarios:
                    n_open, n_suit, n_str, s_str, s_type, s_suit = sc
                    setup_lesson(n_open, n_suit, n_str, s_str, s_type, s_suit, opener=opener)
                    tag = f'{s_str or "-"}/{s_type or "-"}'
                    recs.append(analyze(f'[{cfg_name} פותח={opener}] {blabel}:{tag}'))
            all_bad += report(recs, f'דפי-עבודה — {cfg_name} · פותח={opener}')
    return all_bad


if __name__ == '__main__':
    bad1 = run_lessons()   # 43 שיעורים × 2 שיטות × 4 רוחות
    bad2 = run_panel()     # 77 תרחישי פאנל × 2 שיטות × 4 רוחות
    bad3 = run_worksheet() # תרחישי דפי-העבודה החדשים × 2 שיטות × 4 רוחות
    total = len(bad1) + len(bad2) + len(bad3)
    print(f'\n{"#"*70}\nסה״כ תרחישים עם הפרות: {total}  (שיעורים={len(bad1)} פאנל={len(bad2)} דפי-עבודה={len(bad3)})\n{"#"*70}')
    sys.exit(1 if total else 0)
