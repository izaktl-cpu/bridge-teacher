# -*- coding: utf-8 -*-
# מנוע הכרזות — Acol 5 קלפים במיגור, NT חזק 15-17

SUITS   = ['♠','♥','♦','♣']
HCP_VAL = {'A':4,'K':3,'Q':2,'J':1}

# ── טבלת חוזק ─────────────────────────────────────────────────────────────────
OPENER_WEAK = (12, 14)   # חלש
OPENER_MED  = (15, 17)   # בינוני
OPENER_STR  = (18, 21)   # חזק

RESP_WEAK = (6,  9)      # חלש
RESP_MED  = (10, 12)     # בינוני
RESP_STR  = (13, 37)     # חזק

def hcp(hand):
    return sum(HCP_VAL.get(c['r'],0) for c in hand)

def quick_tricks(hand):
    """לקיחות מידיות: AK=2, A=1, KQ=1, K=0.5"""
    qt = 0.0
    for suit in SUITS:
        ranks = [c['r'] for c in hand if c['s'] == suit]
        has_a, has_k, has_q = 'A' in ranks, 'K' in ranks, 'Q' in ranks
        if has_a and has_k:   qt += 2.0
        elif has_a:           qt += 1.0
        elif has_k and has_q: qt += 1.0
        elif has_k:           qt += 0.5
    return qt

def count_aces(hand):
    return sum(1 for c in hand if c['r'] == 'A')

def gerber_response(hand):
    """תשובה לג'רבר (4♣): 4♦=0/4, 4♥=1, 4♠=2, 4NT=3 אסים"""
    a = count_aces(hand)
    return ['4♦','4♥','4♠','4NT','4♦'][a]

def sl(hand, suit):
    return sum(1 for c in hand if c['s']==suit)

def length_pts(hand):
    """נקודות אורך: +1 לכל קלף מעל 4 בסדרה"""
    return sum(max(0, sl(hand, s) - 4) for s in SUITS)

def total_pts(hand):
    return hcp(hand) + length_pts(hand)

def is_balanced(hand):
    lens = sorted([sl(hand,s) for s in SUITS], reverse=True)
    return lens in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]

def suit_hcp(hand, suit):
    return sum(HCP_VAL.get(c['r'], 0) for c in hand if c['s'] == suit)

def has_ace(hand, suit):
    return any(c['s'] == suit and c['r'] == 'A' for c in hand)

def is_cue_bid(bid, trump_suit):
    """True אם bid הוא הכרזת רמה 4 בסדרה מתחת לצבע הקוז"""
    if not (bid and len(bid) == 2 and bid[0] == '4'): return False
    return bid[1] in SUIT_RANK and SUIT_RANK.get(bid[1], -1) < SUIT_RANK.get(trump_suit, -1)

def has_stopper(hand, suit):
    cards = [c for c in hand if c['s'] == suit]
    n     = len(cards)
    ranks = {c['r'] for c in cards}
    if 'A' in ranks:                    return True
    if 'K' in ranks and n >= 2:         return True
    if 'Q' in ranks and n >= 3:         return True
    if 'J' in ranks and n >= 4:         return True
    return False

SUIT_RANK   = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}
PARTNER_MAP = {'N':'S', 'S':'N', 'E':'W', 'W':'E'}

def is_reverse_bid(opening, rebid_bid):
    """True אם rebid הוא reverse: פותח הכריז סדרה גבוהה יותר בדרגה ברמה 2 → 16+, כפוי לגיים"""
    if len(opening) != 2 or len(rebid_bid) != 2: return False
    if rebid_bid[0] != '2': return False
    os, rs = opening[1], rebid_bid[1]
    return os in SUIT_RANK and rs in SUIT_RANK and SUIT_RANK[rs] > SUIT_RANK[os]

# ── RKCB — Roman Key Card Blackwood ───────────────────────────────────────────
def count_key_cards(hand, trump_suit):
    aces   = sum(1 for c in hand if c['r'] == 'A')
    has_kt = any(c['r'] == 'K' for c in hand if c['s'] == trump_suit)
    return aces + (1 if has_kt else 0)

def has_queen_trump(hand, trump_suit):
    return any(c['r'] == 'Q' for c in hand if c['s'] == trump_suit)

def rkcb_response_bid(hand, trump_suit):
    kc = count_key_cards(hand, trump_suit)
    q  = has_queen_trump(hand, trump_suit)
    if kc in (0, 3): return '5♣'
    if kc in (1, 4): return '5♦'
    return '5♠' if q else '5♥'   # kc == 2

# ── פתיחה ─────────────────────────────────────────────────────────────────────
def opening_bid(hand, cfg):
    pts = hcp(hand)

    # פרי-אמפטים וחלשות — 6-9 נק'
    if pts < 12:
        if 6 <= pts <= 9:
            # רמה 4 — 8 קלפים, 6+ נק' גבוהות בסדרה
            for suit in ['♠','♥','♦','♣']:
                if sl(hand,suit) >= 8 and suit_hcp(hand, suit) >= 6:
                    return f'4{suit}'
            # רמה 3 — 7 קלפים, 5+ נק' גבוהות בסדרה
            for suit in ['♠','♥','♦','♣']:
                if sl(hand,suit) >= 7 and suit_hcp(hand, suit) >= 5:
                    return f'3{suit}'
            # רמה 2 — 6 קלפים (לא תלתן — 2♣ שמורה לחזקה)
            for suit in ['♠','♥','♦']:
                if sl(hand,suit) >= 6 and suit_hcp(hand, suit) >= 5:
                    return f'2{suit}'
        return 'פס'

    # 2♣ חזקה
    if pts >= 23:
        return '2♣'

    # 2NT
    if 20 <= pts <= 22 and is_balanced(hand):
        return '2NT'

    # 1NT — מאוזן 15-17 גובר על הכל (כולל 5 קלפים במיגור)
    if cfg['ntMin'] <= pts <= cfg['ntMax'] and is_balanced(hand):
        return '1NT'

    # מיגורים — 5+ קלפים
    h = sl(hand,'♥'); s = sl(hand,'♠')
    mj = cfg['majorLen']
    if h >= mj and h >= s: return '1♥'
    if s >= mj:            return '1♠'
    if h >= mj:            return '1♥'

    # מינורים — כשאורכים שווים, עדיפות ל-1♣
    c_len = sl(hand,'♣'); d_len = sl(hand,'♦')
    mn = cfg['minorLen']
    if c_len >= mn and c_len >= d_len: return '1♣'   # ♣ ≥ ♦ → 1♣
    if d_len >= mn:                    return '1♦'   # ♦ > ♣ → 1♦
    if c_len >= mn:                    return '1♣'

    return 'פס'

# ── תשובה לפתיחה ─────────────────────────────────────────────────────────────
def response(hand, opening, cfg, overcall_bid=None):
    pts = hcp(hand)

    # עזר: האם ניתן להכריז bid זה (גבוה מהאוברקול)?
    oc_h    = auction_height([overcall_bid]) if overcall_bid else (0, -1)
    oc_suit = overcall_bid[1] if (overcall_bid and len(overcall_bid)==2
                                   and overcall_bid[1] in SUIT_RANK) else None

    def avail(level, s):
        rank = 4 if s == 'NT' else SUIT_RANK.get(s, -1)
        return (level, rank) > oc_h

    def nt_ok():
        return oc_suit is None or has_stopper(hand, oc_suit)

    # ── לפרי-אמפטים ברמה 3 (3♥/3♠/3♦/3♣) ──
    if opening[0] == '3' and len(opening) == 2 and opening[1] in SUIT_RANK:
        open_suit = opening[1]
        support = sl(hand, open_suit)
        is_major = open_suit in ('♥','♠')
        # מיגור: 2+ קלפים מספיק (7+2=9 עצים); מינור: דרוש 3+ לגיים ב-5
        if is_major and support >= 2 and pts >= 13: return f'4{open_suit}'
        if not is_major and support >= 3 and pts >= 14: return f'5{open_suit}'
        if pts < 15: return 'פס'
        if is_balanced(hand) and nt_ok(): return '3NT'
        for suit in ['♠','♥']:
            if suit != open_suit and sl(hand, suit) >= 5:
                return f'4{suit}'
        return 'פס'

    # ── לפרי-אמפטים ברמה 4 (4♥/4♠/4♦/4♣) ──
    if opening[0] == '4' and len(opening) == 2 and opening[1] in SUIT_RANK:
        open_suit = opening[1]
        if pts >= 17: return '4NT'
        return 'פס'

    # ── לפתיחת פתיחה חלשה (2♥ / 2♠ / 2♦) ──
    if opening in ('2♥','2♠','2♦'):
        open_suit = opening[1]
        support = sl(hand, open_suit)
        tp = total_pts(hand)

        # עם תמיכה — בדיקה ע"פ לקיחות מידיות (QT)
        qt = quick_tricks(hand)
        if support >= 3:
            # 4M: 4+ QT + 15+ נק' (≈5 לקיחות מידיות)
            if qt >= 4 and pts >= 15: return f'4{open_suit}'
            # 3M: 3+ QT (≈4 לקיחות מידיות)
            if qt >= 3: return f'3{open_suit}'
            return 'פס'
        if support == 2:
            # גיים עם 2 קלפים — 4+ QT + 16+ נק'
            if qt >= 4 and pts >= 16: return f'4{open_suit}'
            return 'פס'

        # ללא תמיכה — צריך לפחות 15 נק'
        if pts < 15: return 'פס'
        # 2♠ מעל 2♥ — 5+ ספייד
        if opening == '2♥' and sl(hand,'♠') >= 5 and avail(2,'♠'): return '2♠'
        # 3NT — מאוזן עם עצורים
        if nt_ok() and avail(3,'NT'): return '3NT'
        # סדרה חדשה ברמה 3 — 5+ קלפים
        for suit in ['♠','♥','♦','♣']:
            if suit != open_suit and sl(hand, suit) >= 5 and avail(3, suit):
                return f'3{suit}'
        return 'פס'

    # ── לפתיחת 1NT ──
    if opening == '1NT':
        h = sl(hand,'♥'); s = sl(hand,'♠')
        nt_min = cfg.get('ntMin', 15); nt_max = cfg.get('ntMax', 17)
        if h >= 5: return '2♦'                              # טרנספר ♥ — גם עם יד חלשה
        if s >= 5: return '2♥'                              # טרנספר ♠ — גם עם יד חלשה
        if pts < 6: return 'פס'
        # סטיימן: דורש 2+ רביעיות שאחת מהן מיגור (לא יד 4333)
        four_suits = sum(1 for su in SUITS if sl(hand, su) >= 4)
        if pts >= 25-nt_max and (h >= 4 or s >= 4) and four_suits >= 2: return '2♣'
        if pts >= 33-nt_min: return '4♣'    # ג'רבר — בדוק אסים לפני סלאם
        if pts >= 33-nt_max: return '4NT'  # הזמנת סלאם — combined 31-34
        if pts >= 25-nt_min: return '3NT'
        if pts >= 25-nt_max: return '2NT'   # הזמנה עם יד מאוזנת (כולל 4333)
        return 'פס'

    # ── לפתיחת 2NT ──
    if opening == '2NT':
        h = sl(hand,'♥'); s = sl(hand,'♠')
        if h >= 5: return '3♦'     # טרנספר ♥ — עדיפות על סטיימן
        if s >= 5: return '3♥'     # טרנספר ♠
        if pts < 4: return 'פס'
        if h >= 4 or s >= 4: return '3♣'   # סטיימן
        if pts >= 13: return '6NT'
        return '3NT'

    # ── לפתיחת 2♣ ──
    if opening == '2♣':
        if pts <= 6: return '2♦'          # שלילי: 0-6 נק'
        for suit in ['♠','♥','♦','♣']:
            if sl(hand,suit) >= 5: return f'2{suit}' if suit in ['♠','♥'] else f'3{suit}'
        return '2NT'                       # חיובי 7+ ללא 5 קלפים בצבע

    # ── Redouble (XX) — אחרי דאבל טייקאוט של היריב ──
    # כלל: שותף פתח 1x, E דיבל → עם 10+ כבוד ואין תמיכה → XX
    if overcall_bid == 'X' and opening[0] == '1' and opening != '1NT':
        open_suit = opening[1]
        support = sl(hand, open_suit)
        # עם תמיכה — העלה כרגיל (תמיכה חשובה יותר מ-XX)
        if support >= 3:
            if pts >= 13: return f'4{open_suit}' if open_suit in ('♥','♠') else '3NT'
            if pts >= 10: return f'3{open_suit}'
            if pts >= 6:  return f'2{open_suit}'
            return 'פס'
        # 10+ כבוד ללא תמיכה → XX (מראה יד חזקה, פותח ימתין בפס)
        if pts >= 10:
            return 'XX'
        # 6-9 כבוד עם 5+ קלפים — הצג צבע
        if pts >= 6:
            for suit in ['♠','♥','♦','♣']:
                if suit != open_suit and sl(hand, suit) >= 5:
                    lvl = 1 if SUIT_RANK.get(suit,-1) > SUIT_RANK.get(open_suit,-1) else 2
                    return f'{lvl}{suit}'
        return 'פס'

    # ── Negative double ──
    # תנאי: פתיחה ברמה 1 (לא NT), יש אוברקול, 6-11 כבוד (12+ → הכרזה ישירה)
    if overcall_bid and overcall_bid[0].isdigit() and opening[0] == '1' and opening != '1NT':
        oc_level = int(overcall_bid[0])
        min_hcp  = 8 if oc_level >= 2 else 6
        open_suit = opening[1]
        if min_hcp <= pts <= 11:
            h = sl(hand,'♥'); s = sl(hand,'♠')
            # אחרי 1מינור-(1♠): ♥ חסום → X רק אם אין עצור (עם עצור → 1NT עדיף)
            if opening in ('1♣','1♦') and oc_suit == '♠' and h >= 4 and not avail(1,'♥'):
                if not nt_ok():
                    return 'X'
            # אחרי 1מינור-(1♥): X = 4♠+4♥ (רוצה להראות שניהם, אחרת היה מכריז 1♠)
            if opening in ('1♣','1♦') and oc_suit == '♥' and h >= 4 and s >= 4:
                return 'X'
            # אחרי 1מיגור-(2x): המיגור השני חסום → X
            if opening in ('1♥','1♠') and oc_level >= 2:
                other_major = '♠' if open_suit == '♥' else '♥'
                if sl(hand, other_major) >= 4 and not avail(1, other_major):
                    return 'X'

    # ── לפתיחת מיגור (1♥ / 1♠) ──
    open_suit = opening[1]
    if opening in ('1♥','1♠'):
        support = sl(hand, open_suit)
        if support >= 3:
            if pts >= 13: return f'4{open_suit}'
            if pts >= 10: return f'3{open_suit}'
            if pts >= 6:  return f'2{open_suit}'
            return 'פס'
        # ללא תמיכה
        if pts < 6: return 'פס'
        if opening == '1♥' and sl(hand,'♠') >= 4 and avail(1,'♠'): return '1♠'
        if opening == '1♠' and sl(hand,'♥') >= 4 and pts >= 11 and avail(2,'♥'): return '2♥'
        # יד מאוזנת 13+ → 3NT ישיר לפני הצגת מינור
        if pts >= 13 and is_balanced(hand) and nt_ok() and avail(3,'NT'): return '3NT'
        # 11+ נק' יד לא מאוזנת — הצג מינור ברמה 2 (כפוי לגיים, 4+ קלפים)
        if pts >= 11 and not is_balanced(hand):
            for suit in ['♦', '♣']:
                if suit != open_suit and sl(hand, suit) >= 4 and avail(2, suit):
                    return f'2{suit}'
        if pts >= 11 and is_balanced(hand) and nt_ok() and avail(2,'NT'): return '2NT'
        if pts >= 6  and is_balanced(hand) and nt_ok() and avail(1,'NT'): return '1NT'
        # יד לא מאוזנת עם 11+ נק' — הצג סדרה חדשה ברמה 2
        if pts >= 11:
            for suit in ['♥', '♦', '♣']:
                if suit != open_suit and sl(hand, suit) >= 5 and avail(2, suit):
                    return f'2{suit}'
        # יד לא מאוזנת 6+ נק' ללא כיוון אחר — dustbin 1NT
        if pts >= 6 and nt_ok() and avail(1,'NT'): return '1NT'
        return 'פס'

    # ── לפתיחת מינור (1♣ / 1♦) ──
    if opening in ('1♣','1♦'):
        if pts < 6: return 'פס'
        if sl(hand,'♥') >= 5 and sl(hand,'♠') >= 5 and avail(1,'♠'): return '1♠'  # 5-5
        if sl(hand,'♠') > sl(hand,'♥') and sl(hand,'♠') >= 4 and avail(1,'♠'): return '1♠'  # ♠ ארוך מ-♥
        if sl(hand,'♥') >= 4 and avail(1,'♥'): return '1♥'
        if sl(hand,'♠') >= 4 and avail(1,'♠'): return '1♠'
        other_minor = '♦' if opening == '1♣' else '♣'
        if sl(hand, other_minor) >= 5 and pts >= 11 and avail(2, other_minor): return f'2{other_minor}'
        if opening == '1♣' and sl(hand,'♦') >= 4 and not is_balanced(hand) and avail(1,'♦'): return '1♦'
        if sl(hand, open_suit) >= 5:
            if pts >= 13:
                if is_balanced(hand) and nt_ok() and avail(3,'NT'): return '3NT'
                if avail(3, open_suit): return f'3{open_suit}'   # גיים כופה, יד לא מאוזנת
            if avail(2, open_suit): return f'2{open_suit}'       # חלש 6-12
        if pts >= 13 and is_balanced(hand) and nt_ok() and avail(3,'NT'): return '3NT'
        if pts >= 11 and is_balanced(hand) and nt_ok() and avail(2,'NT'): return '2NT'
        if nt_ok() and avail(1,'NT'): return '1NT'
        return 'פס'

    return 'פס'

# ── Rebid של הפותח ────────────────────────────────────────────────────────────
def rebid(hand, opening, resp, cfg, ew_oc=None):
    pts = hcp(hand)
    oc_suit = (ew_oc[1] if (ew_oc and len(ew_oc) == 2 and ew_oc[1] in SUIT_RANK) else None)

    # אחרי Negative double של המשיב (X)
    if resp == 'X' and opening[0] == '1' and opening != '1NT':
        open_suit = opening[1]
        h = sl(hand,'♥'); s = sl(hand,'♠')
        # אחרי 1מינור-X(=4♥ כשאוברקל ♠, או 4♠+4♥ כשאוברקל ♥): הצג ♥/♠
        if opening in ('1♣','1♦'):
            if h >= 4:
                return '2♥' if pts <= 15 else '3♥' if pts <= 18 else '4♥'
            # הצג ♠ רק אם ♠ לא הייתה סדרת האוברקול
            if s >= 4 and oc_suit != '♠': return '1♠'
            return '1NT' if pts <= 14 else '2NT' if pts <= 17 else '3NT'
        # אחרי 1♥/1♠-X(=מיגור שני חסום): הצג התאמה עם כוח
        if opening in ('1♥','1♠'):
            other = '♠' if open_suit == '♥' else '♥'
            if sl(hand, other) >= 3:
                if pts >= 17: return f'4{other}'   # גיים ישיר
                if pts >= 15: return f'3{other}'   # הזמנה
                return f'2{other}'                 # מינימום
            return '1NT' if pts <= 14 else '2NT'

    # אחרי פתיחה חלשה (2♥ / 2♠ / 2♦)
    if opening in ('2♥','2♠','2♦'):
        open_suit = opening[1]
        # אחרי 3M (הרמה תחרותית, 10-14 נק') — פותח תמיד פס
        # (15+ נק' → שותף היה מכריז 4M ישיר)
        if resp == f'3{open_suit}':
            return 'פס'
        # 4M, 2♠, 3NT, סדרה חדשה — פותח פס (תיאר ידו)
        return 'פס'

    # אחרי 1NT
    if opening == '1NT':
        nt_max = cfg.get('ntMax', 17)
        if resp == '4♣': return gerber_response(hand)   # ג'רבר — ספור אסים
        if resp == '4NT': return '6NT' if pts >= nt_max else 'פס'
        if resp == '6NT': return 'פס'
        if resp == '2NT': return '3NT' if pts >= nt_max - 1 else 'פס'
        if resp == '2♦': return '2♥'   # השלמת טרנספר
        if resp == '2♥': return '2♠'   # השלמת טרנספר
        if resp == '2♣':               # סטיימן
            if sl(hand,'♠') >= 4: return '2♠'
            if sl(hand,'♥') >= 4: return '2♥'
            return '2♦'
        return 'פס'

    # אחרי 2NT
    if opening == '2NT':
        if resp == '4NT': return '6NT' if pts >= 21 else 'פס'   # הזמנה כמותית — קבל עם 21+
        if resp == '6NT': return 'פס'
        if resp == '3♦': return '3♥'   # השלמת טרנספר
        if resp == '3♥': return '3♠'   # השלמת טרנספר
        if resp == '3♣':               # סטיימן
            if sl(hand,'♠') >= 4: return '3♠'
            if sl(hand,'♥') >= 4: return '3♥'
            return '3♦'
        return 'פס'

    # אחרי פתיחת מיגור + תמיכה
    open_suit = opening[1] if len(opening) == 2 else ''
    if opening in ('1♥','1♠') and resp in (f'2{open_suit}', f'3{open_suit}', f'4{open_suit}'):
        if resp == f'4{open_suit}':
            if pts >= 18: return '4NT'   # RKCB — כושר + 18+ נק' → שואל על קלפי מפתח
            return 'פס'
        if resp == f'3{open_suit}':
            tp = total_pts(hand)
            if tp >= 23: return '4NT'                # RKCB ישיר
            if tp >= 19:
                # קיו-ביד — הראה א' בסדרה הזולה ביותר מתחת ל-4M
                cue_suits = ['♣','♦'] + (['♥'] if open_suit == '♠' else [])
                for suit in cue_suits:
                    if has_ace(hand, suit): return f'4{suit}'
                return '4NT'                         # אין א' → RKCB ישיר
            if tp >= 15: return f'4{open_suit}'      # מקסימום → קבל הזמנה
            return 'פס'
        if resp == f'2{open_suit}':
            if pts >= 19: return f'4{open_suit}'
            if pts >= 16: return f'3{open_suit}'
        return 'פס'

    # אחרי פתיחת מיגור + תגובה שאינה תמיכה
    if opening in ('1♥','1♠'):
        # אחרי סדרה חדשה ברמה 2 (11+ נק', 5+ קלפים)
        if len(resp) == 2 and resp[0] == '2' and resp[1] in SUIT_RANK and resp[1] != open_suit:
            resp_suit = resp[1]
            if sl(hand, resp_suit) >= 4:          # תמיכה בסדרת המשיב
                tp = total_pts(hand)
                if tp >= 18: return f'4{resp_suit}' if resp_suit in ('♥','♠') else '4NT'
                return f'3{resp_suit}'
            # כמותי — "אתה מינימום (11) או מקסימום (15)?"
            # 4NT כמותי מתאר יד מאוזנת. בלי התנאי הזה יד עם חוסר הכריזה 4NT
            # (ועוד בסדרה שהמשיב בדיוק הראה) — ראה בדיקת הרגרסיה 1♠→2♥.
            if pts >= 18 and is_balanced(hand): return '4NT'
            if sl(hand, open_suit) >= 6: return f'3{open_suit}'
            if sl(hand, open_suit) >= 5: return f'2{open_suit}'
            return '2NT'
        # אחרי 1NT (6-10 נק', אין תמיכה)
        if resp == '1NT':
            if pts >= 19: return '3NT'
            if pts >= 15: return f'3{open_suit}' if sl(hand, open_suit) >= 5 else '2NT'
            if sl(hand, open_suit) >= 5 and pts >= 14: return f'2{open_suit}'
            return 'פס'
        # אחרי 3NT (13+ נק', מאוזן) — פס תמיד
        if resp == '3NT':
            return 'פס'
        # אחרי 2NT (11-12 נק', מאוזן)
        if resp == '2NT':
            if pts >= 14: return '3NT'
            return 'פס'
        # אחרי 1♠ (פתחנו 1♥) — המשיב יש 4+ ספייד
        if opening == '1♥' and resp == '1♠':
            if sl(hand,'♠') >= 4:
                tp = total_pts(hand)
                if tp >= 15: return '4♠'
                return '2♠'
            # אין תמיכה ב-♠ — תאר ידך
            if pts >= 19: return '3NT'
            if pts >= 15: return '2NT'
            if sl(hand,'♥') >= 5: return '2♥'
            return 'פס'

    # אחרי פתיחת מינור
    if opening in ('1♣','1♦'):
        open_suit = opening[1]
        if resp in ('1♥','1♠'):
            resp_suit = resp[1]
            # 4+ תמיכה: תמיד מעלה
            if sl(hand, resp_suit) >= 4:
                tp = total_pts(hand)   # כולל נקודות אורך
                if tp >= 18: return f'4{resp_suit}' if resp_suit in ('♥','♠') else f'3{resp_suit}'
                if tp >= 16: return f'3{resp_suit}' if resp_suit in ('♥','♠') else f'2{resp_suit}'
                return f'2{resp_suit}'
            # 3 קלפי לב — תמיכה מקובלת בפתיחת מינור (ספייד: דרוש 4+ לתמיכה)
            if resp_suit == '♥' and sl(hand, '♥') == 3:
                tp = total_pts(hand)
                if tp >= 18: return '4♥'
                if tp >= 16: return '3♥'
                return '2♥'
            if resp == '1♥' and sl(hand,'♠') >= 4: return '1♠'   # הצג ספייד אחרי 1♥
            # יד דו-צבעית — הצג מינור שני רק אם 5+ קלפים
            other_minor = '♦' if open_suit == '♣' else '♣'
            if sl(hand, other_minor) >= 5: return f'2{other_minor}'
            if pts >= 18: return '3NT'
            if pts >= 15: return '2NT'
            return '1NT'
        if resp == '1♦' and opening == '1♣':   # 4+ יהלומים, 6+ נק'
            if sl(hand,'♦') >= 4:
                if pts >= 16: return '3♦'
                return '2♦'
            if pts >= 18: return '2NT'
            return '1NT'
        if resp in ('2♦','2♣'):                # צבע חדש ברמה 2 — כפוי לסיבוב (11+ נק')
            resp_suit = resp[1]
            if sl(hand, resp_suit) >= 4:
                if pts >= 18: return '3NT'     # חזק מאוד → גיים ישיר
                return f'3{resp_suit}'         # הזמנה 12-17
            if pts >= 15: return '3NT'
            return '2NT'
        if resp == '1NT':
            if pts >= 18: return '3NT'
            if pts >= 15: return '2NT'
            return 'פס'
        if resp == '2NT':          # משיב 11-12 נק' — גיים עם 13+ (13+12=25)
            if pts >= 13: return '3NT'
            return 'פס'
        if resp == '3NT':          # משיב 13-15 מאוזן
            # 18+15=33 → הזמנת סלאם כמותית. בלי הענף הזה הפותח פסס עם 18.
            if pts >= 18: return '4NT'
            return 'פס'

    # אחרי פתיחת 2♣ חזקה
    if opening == '2♣':
        h = sl(hand,'♥'); s = sl(hand,'♠')
        if resp == '2♦':                  # שלילי/המתנה
            if s >= 5: return '2♠'
            if h >= 5: return '2♥'
            if pts >= 25: return '3NT'
            return '2NT'
        if resp in ('2♥','2♠','3♣','3♦'):  # חיובי
            resp_suit = resp[1]
            if sl(hand, resp_suit) >= 3: return f'4{resp_suit}' if resp_suit in ('♥','♠') else f'5{resp_suit}'
            if pts >= 25: return '3NT'
            return '2NT'
        if resp == '2NT':
            if pts >= 25: return '4NT'   # הזמנת סלאם כמותית (25+8=33)
            return '3NT'                 # גיים (23-24 נק')

    return 'פס'

# ── תשובת המשיב השנייה (אחרי rebid של הפותח) ─────────────────────────────────
def second_response(hand, opening, resp1, rebid_bid, cfg):
    pts = hcp(hand)

    # אחרי קיו-ביד של הפותח (1♥/1♠ → 3M → 4♣/4♦/4♥)
    if opening in ('1♥','1♠'):
        open_suit = opening[1]
        if resp1 == f'3{open_suit}' and is_cue_bid(rebid_bid, open_suit):
            if pts >= 11: return '4NT'      # RKCB — מספיק לסלאם
            return f'4{open_suit}'          # גיים — לא מספיק
        # אחרי 4NT כמותי של הפותח — 20+ → 7NT, 16-19 → 6NT, 11-15 → פס
        if (rebid_bid == '4NT' and len(resp1) == 2 and resp1[0] == '2'
                and resp1[1] in SUIT_RANK and resp1[1] != open_suit):
            if pts >= 20: return '7NT'
            if pts >= 16: return '6NT'
            return 'פס'

    # ── אחרי 1מיגור + X(נגטיב דאבל) + rebid עם פיט ──────────────────────────────
    if opening in ('1♥','1♠') and resp1 == 'X':
        other = '♠' if opening[1] == '♥' else '♥'
        if rebid_bid == f'4{other}': return 'פס'          # גיים הושג
        if rebid_bid == f'3{other}':                       # הזמנה (פותח 15-16)
            return f'4{other}' if pts >= 9 else 'פס'
        if rebid_bid == f'2{other}':                       # מינימום (פותח 12-14)
            if pts >= 11: return f'4{other}'
            if pts >= 9:  return f'3{other}'               # הזמנה חזרה
            return 'פס'

    # 5♠+4♥ (או 5-5) — אחרי 1מינור-1♠, הצג לב בסיבוב שני (רק ברמה נמוכה, 10+ נק', ספייד לא הוסכמו)
    if opening in ('1♣','1♦') and resp1 == '1♠' and sl(hand,'♥') >= 4 and pts >= 10:
        if len(rebid_bid) == 2 and int(rebid_bid[0]) <= 2 and rebid_bid[1] != '♠':
            return '2♥'

    # אחרי 2♣ חזקה + rebid בצבע (2♠/2♥/3♣/3♦)
    # פותח הראה את הצבע שלו — מחפשים התאמה
    if opening == '2♣' and len(rebid_bid) == 2 and rebid_bid[1] in SUIT_RANK and rebid_bid[0] in '23':
        open_suit = rebid_bid[1]
        support = sl(hand, open_suit)
        is_major = open_suit in ('♥','♠')
        # 2♣ תמיד כפוי לגיים (פותח 23+); 23+10=33 → סלאם קטן; 23+14=37 → גיים גדול
        if support >= 3:
            if pts >= 14: return f'7{open_suit}'        # גרנד סלאם — 37+
            if pts >= 10: return f'6{open_suit}'        # סלאם קטן — 33+
            return f'4{open_suit}' if is_major else f'5{open_suit}'   # גיים
        # אין התאמה — NT
        if pts >= 14: return '7NT'
        if pts >= 10: return '6NT'
        return '3NT'    # גיים כפוי תמיד ב-2♣

    # אחרי 2♣ חזקה + 2NT rebid — 2NT מראה 23-24 מאוזן.
    if opening == '2♣' and rebid_bid == '2NT':
        if resp1 == '2♦':
            # 0-2 נק' לא מספיקות לגיים — פס (החריג היחיד לכפייה של 2♣)
            if pts <= 2: return 'פס'
            # 3+ נק' עם מיגור רביעייה — סטיימן, לחפש התאמה 4-4
            if sl(hand,'♥') >= 4 or sl(hand,'♠') >= 4: return '3♣'
        if pts >= 10: return '6NT'
        return '3NT'   # כפוי לגיים
    # אחרי 2♣ חזקה + 4NT rebid (הזמנת סלאם כמותית) — קבל עם 8+
    if opening == '2♣' and rebid_bid == '4NT':
        return '6NT' if pts >= 8 else 'פס'   # 25+8=33 → סלאם
    # אחרי 2♣ חזקה + 3NT rebid — בדוק סלאם
    if opening == '2♣' and rebid_bid == '3NT':
        if pts >= 10: return '6NT'
        return 'פס'

    # ── אחרי 4NT כמותי של הפותח (1m → 3NT → 4NT) ──────────────────────────────
    # כלל יצחק: "אתה מינימום 12-13 תכריז פס, אתה 14+ תכריז 6".
    # 4NT כאן אינו RKCB אלא הזמנה כמותית — הפותח מראה 18+ מאוזן.
    if opening in ('1♣','1♦') and resp1 == '3NT' and rebid_bid == '4NT':
        return '6NT' if pts >= 14 else 'פס'

    # RKCB — הפותח שאל על קלפי מפתח, המשיב עונה
    if rebid_bid == '4NT' and opening in ('1♥','1♠'):
        return rkcb_response_bid(hand, opening[1])

    # ── ג'רבר — תשובת המשיב לאחר ספירת אסים ────────────────────────────────────
    if opening in ('1NT','2NT') and resp1 == '4♣':
        # rebid_bid = תשובת הפותח לג'רבר: 4♦=0/4, 4♥=1, 4♠=2, 4NT=3
        my_aces = count_aces(hand)
        opener_aces = {'4♦': 0, '4♥': 1, '4♠': 2, '4NT': 3}.get(rebid_bid, 0)
        # אם פותח ענה 4♦ וגם יש לנו 4 אסים — הוא בעצם יש לו 0
        total = my_aces + opener_aces
        if total >= 3: return '6NT'
        return 'פס'   # חסרים אסים — הישאר בחוזה הנמוך (4NT/4♠...)

    # ── המשך אחרי טרנספר 1NT ──────────────────────────────────────────────────
    if opening == '1NT':
        h = sl(hand,'♥'); s = sl(hand,'♠')
        nt_min = cfg.get('ntMin', 15); nt_max = cfg.get('ntMax', 17)
        game_thr  = 25 - nt_min   # strong:10, weak:13
        inv_thr   = 25 - nt_max   # strong:8,  weak:11

        # טרנספר ל-♥ הושלם (2♦ → 2♥)
        if resp1 == '2♦' and rebid_bid == '2♥':
            if pts < inv_thr: return 'פס'
            if pts >= game_thr:
                if s >= 5: return '3♠'    # 5♥+5♠ גיים-פורסינג
                if s >= 4: return '2♠'    # 5♥+4♠
                if h >= 6: return '4♥'    # 6♥ גיים
                return '3NT'
            else:                          # הזמנה
                if h >= 6: return '3♥'    # 6♥ הזמנה
                return '2NT'              # הזמנה כללית (כולל 5♥+4♠)

        # טרנספר ל-♠ הושלם (2♥ → 2♠)
        if resp1 == '2♥' and rebid_bid == '2♠':
            if pts < inv_thr: return 'פס'
            if pts >= game_thr:
                if h >= 4: return '3♥'    # 5♠+4+♥ גיים-פורסינג — הראה שני צבעים
                if s >= 6: return '4♠'    # 6♠ גיים
                return '3NT'
            else:                          # הזמנה
                if s >= 6: return '3♠'    # 6♠ הזמנה
                return '2NT'              # הזמנה כללית (כולל 5♠+4♥ — 3♥ גיים-פורסינג)

        # ── המשך אחרי סטיימן (2♣) ───────────────────────────────────────────
        if resp1 == '2♣':
            if rebid_bid == '2♥':          # פותח יש 4♥
                if h >= 4:                 # התאמה ב-♥
                    return '4♥' if pts >= game_thr else '3♥'
                else:                      # אין ♥, יש 4♠ → אין התאמה
                    return '3NT' if pts >= game_thr else '2NT'
            if rebid_bid == '2♠':          # פותח יש 4♠
                if s >= 4:                 # התאמה ב-♠
                    return '4♠' if pts >= game_thr else '3♠'
                else:                      # אין ♠, יש 4♥ → אין התאמה
                    return '3NT' if pts >= game_thr else '2NT'
            if rebid_bid == '2♦':          # פותח אין מיגור → NT
                return '3NT' if pts >= game_thr else '2NT'

    # אחרי 2NT+סטיימן (3♣ → 3♥/3♠/3♦ → ?)
    # ספף סלאם: 13+20=33 — ודאי; 11+22=33 — רק עם מקסימום → 4NT הזמנה עדיפה
    if opening == '2NT' and resp1 == '3♣':
        if rebid_bid == '3♥':
            if sl(hand,'♥') >= 4:
                return '6♥' if pts >= 13 else '4♥'
            return '6NT' if pts >= 13 else '3NT'
        if rebid_bid == '3♠':
            if sl(hand,'♠') >= 4:
                return '6♠' if pts >= 13 else '4♠'
            return '6NT' if pts >= 13 else '3NT'
        if rebid_bid == '3♦':
            return '6NT' if pts >= 13 else '3NT'

    # אחרי 2NT+טרנספר ♥ (3♦ → 3♥ → ?)
    if opening == '2NT' and resp1 == '3♦' and rebid_bid == '3♥':
        return '6♥' if pts >= 13 else '4♥'    # 13+20=33 → סלאם ודאי

    # אחרי 2NT+טרנספר ♠ (3♥ → 3♠ → ?)
    if opening == '2NT' and resp1 == '3♥' and rebid_bid == '3♠':
        return '6♠' if pts >= 13 else '4♠'    # 13+20=33 → סלאם ודאי

    # אחרי פתיחת מיגור + 1NT + 3M (פותח מזמין חזק)
    if opening in ('1♥','1♠') and resp1 == '1NT' and rebid_bid == f'3{opening[1]}':
        if sl(hand, opening[1]) >= 2: return f'4{opening[1]}'
        return '3NT'

    # אחרי פתיחת מינור + 2NT rebid
    # resp1=='1♦': פותח 18+ → 7+ נק' ← game (25+)
    # resp1 ברמה 1 אחר (1♥/1♠/1NT): פותח 15-17 → 10+ נק' ← game (25+)
    # resp1 ברמה 2 (2♦/2♣): פותח 12-14 → 13+ נק' ← game
    if opening in ('1♣','1♦') and rebid_bid == '2NT':
        if resp1 == '1♦': thresh = 7
        elif resp1[0] == '1': thresh = 9
        else: thresh = 12
        return '3NT' if pts >= thresh else 'פס'

    # אחרי rebid 3NT של הפותח — בדוק סלאם לפי רמת התשובה הראשונה
    # תשובה ברמה 1: פותח הראה 18+ → צריך 15+ לסלאם (15+18=33)
    # תשובה ברמה 2: פותח הראה 15+ → צריך 18+ לסלאם (18+15=33)
    if rebid_bid == '3NT' and opening in ('1♣','1♦','1♥','1♠'):
        # סלאם קודם — 15+ ברמה 1 (15+18=33), 18+ ברמה 2 (18+15=33)
        slam_thresh = 15 if resp1[0] == '1' else 18
        if pts >= slam_thresh: return '6NT'
        # הצג מיגור שני רק אם אין סלאם
        if opening in ('1♣','1♦') and resp1 in ('1♠',) and sl(hand,'♥') >= 4: return '4♥'
        if opening in ('1♣','1♦') and resp1 in ('1♥',) and sl(hand,'♠') >= 4: return '4♠'
        return 'פס'

    # אחרי rebid של 1NT (פותח 12-14) — צריך 12+ לגיים
    if rebid_bid == '1NT':
        if pts >= 13: return '3NT'
        if pts >= 10: return '2NT'
        return 'פס'
    # אחרי rebid של 2NT (פותח 15-18) — צריך 8+ לגיים
    if rebid_bid == '2NT' and opening in ('1♥','1♠'):
        if pts >= 8: return '3NT'
        return 'פס'

    # אחרי תמיכה של הפותח במיגור
    resp_suit = resp1[1] if len(resp1) == 2 else ''
    if rebid_bid == f'2{resp_suit}':
        # תמיכה פשוטה מראה 12-15. עם 19 יש 31-34 — שאל על אסים לפני שסוגרים
        # גיים. (כלל יצחק)
        if (pts >= 19 and resp_suit in ('♥','♠')
                and opening in ('1♣','1♦')):
            return '4NT'                      # RKCB
        if pts >= 13: return f'4{resp_suit}'
        if pts >= 11: return f'3{resp_suit}'
        return 'פס'
    if rebid_bid == f'3{resp_suit}':
        if resp_suit in ('♥','♠'):
            if pts >= 8: return f'4{resp_suit}'   # מקסימום תגובה חלשה (6-9)
        else:
            if pts >= 11: return '3NT'            # מינור — סף גבוה יותר
        return 'פס'

    # אחרי פתיחת מיגור + תשובת 1♠ + rebid 2♥ (פותח מראה 5♥ שוב)
    if opening == '1♥' and resp1 == '1♠' and rebid_bid == '2♥':
        if pts >= 13: return '4♥' if sl(hand,'♥') >= 3 else '3NT'
        if pts >= 11: return '3♥'
        return 'פס'

    # אחרי מינור + 1M + rebid מינור שני (פותח מראה יד דו-צבעית)
    if opening in ('1♣','1♦') and resp1 in ('1♠','1♥') and \
            len(rebid_bid)==2 and rebid_bid[0]=='2' and rebid_bid[1] in ('♣','♦'):
        # reverse bid (למשל 1♣-1♥-2♦): 16+ נק', כפוי לגיים — אסור לפסוס
        if is_reverse_bid(opening, rebid_bid):
            if pts >= 13: return '3NT'
            if pts >= 10: return '2NT'    # מינימום — מתאר יד חלשה, לא פס
            return '3' + opening[1]       # העדפה לצבע הפותח ברמה 3
        if pts >= 13: return '3NT'
        if pts >= 11: return '2NT'
        return 'פס'

    # אחרי מיגור + 2-level new suit + פותח rebid מיגור שלו (אין התאמה)
    if opening in ('1♥','1♠') and len(resp1)==2 and resp1[0]=='2' and resp1[1] in SUIT_RANK:
        if rebid_bid == f'2{opening[1]}' or rebid_bid == f'3{opening[1]}':
            if pts >= 11: return '3NT'
            return 'פס'
        if rebid_bid == '2NT':
            if pts >= 11: return '3NT'
            return 'פס'
        if rebid_bid == '3NT': return 'פס'

    # אחרי מינור + 1♥ + 1♠ (פותח הראה 4 ספייד) — תמיכה או המשך
    if opening in ('1♣','1♦') and resp1 == '1♥' and rebid_bid == '1♠':
        if sl(hand,'♠') >= 4:
            if pts >= 10: return '4♠'
            if pts >= 6:  return '2♠'
        # אין 4 ספייד — המשיב מתאר ידו
        if pts >= 13: return '3NT'
        if pts >= 11: return '2NT'
        if sl(hand,'♥') >= 5: return '2♥'
        return 'פס'

    return 'פס'

# ── rebid שני של הפותח ────────────────────────────────────────────────────────
def opener_second_rebid(hand, opening, resp1, rebid_bid, resp2, cfg=None):
    cfg = cfg or {}
    pts = hcp(hand)

    # אחרי קיו-ביד של הפותח + תשובת המשיב
    if opening in ('1♥','1♠'):
        open_suit = opening[1]
        if resp1 == f'3{open_suit}' and is_cue_bid(rebid_bid, open_suit):
            if resp2 == '4NT':
                return rkcb_response_bid(hand, open_suit)  # ענה RKCB
            if resp2 == f'4{open_suit}':
                return 'פס'                                # משיב ויתר — גיים

    # ── אחרי סטיימן 2♣ (2♣ → 2♦ → 2NT → 3♣ → ?) ────────────────────────────────
    if (opening == '2♣' and resp1 == '2♦'
            and rebid_bid == '2NT' and resp2 == '3♣'):
        if sl(hand,'♠') >= 4: return '3♠'
        if sl(hand,'♥') >= 4: return '3♥'
        return '3♦'   # אין מיגור רביעייה

    # ── אחרי 2♣ → 2♦ → 2NT → 3NT — גיים, ותו לא ───────────────────────────────
    # 2♦ שלילי מגביל את המשיב ל-0-6, ו-2NT מראה 23-24. מקסימום 24+6=30 —
    # סלאם לא אפשרי חשבונית. בלי הכלל הזה נופלים לכלל הגנרי (resp2=='3NT'
    # → 6NT עם 16+), שמניח משיב של 13-15 ולא רלוונטי כאן.
    if (opening == '2♣' and resp1 == '2♦'
            and rebid_bid == '2NT' and resp2 == '3NT'):
        return 'פס'

    # ── אחרי סטיימן 2NT (2NT → 3♣ → 3x → ?) ────────────────────────────────────
    if opening == '2NT' and resp1 == '3♣':
        if resp2 == '4NT': return '6NT' if pts >= 21 else 'פס'
        return 'פס'   # גיים הושג (4♥/4♠/3NT) — פס

    # ── אחרי טרנספר 2NT (3♦→3♥→4♥ או 3♥→3♠→4♠) ────────────────────────────
    if opening == '2NT' and resp1 in ('3♦','3♥'):
        if resp2 == '4NT': return '6NT' if pts >= 21 else 'פס'
        return 'פס'   # 4♥/4♠/6♥/6♠ — פס

    # ── אחרי סטיימן (1NT → 2♣ → 2x → ?) ─────────────────────────────────────────
    if opening == '1NT' and resp1 == '2♣':
        nt_max = cfg.get('ntMax', 17)
        if rebid_bid == '2♥' and resp2 == '3♥':   # הזמנה עם התאמה ♥
            return '4♥' if pts >= nt_max - 1 else 'פס'
        if rebid_bid == '2♠' and resp2 == '3♠':   # הזמנה עם התאמה ♠
            return '4♠' if pts >= nt_max - 1 else 'פס'
        if resp2 == '2NT':                          # הזמנה ב-NT (אין התאמה)
            return '3NT' if pts >= nt_max - 1 else 'פס'
        return 'פס'

    # ── אחרי השלמת טרנספר ♥ (1NT → 2♦ → 2♥ → ?) ──────────────────────────────
    if opening == '1NT' and resp1 == '2♦' and rebid_bid == '2♥':
        if resp2 in ('פס', '4♥'): return 'פס'
        if resp2 == '3NT':   # 10+, 5♥ מאוזן — עם 3♥ עדיף 4♥
            return '4♥' if sl(hand, '♥') >= 3 else 'פס'
        if resp2 == '3♥':    # הזמנה 8-9 עם 6♥
            return '4♥' if pts >= 16 else 'פס'
        if resp2 == '2NT':   # הזמנה 8-9, 5♥ מאוזן
            if sl(hand, '♥') >= 3: return '4♥' if pts >= 17 else '3♥'
            return '3NT' if pts >= 17 else 'פס'
        if resp2 == '2♠':    # 10+, 5♥+4♠ — בוחר התאמה
            if sl(hand, '♠') >= 4: return '4♠'
            if sl(hand, '♥') >= 3: return '4♥'
            return '3NT'
        if resp2 == '3♠':    # 10+, 5♥+5♠ גיים-פורסינג — בוחר
            return '4♠' if sl(hand, '♠') >= 4 else '4♥'

    # ── אחרי השלמת טרנספר ♠ (1NT → 2♥ → 2♠ → ?) ──────────────────────────────
    if opening == '1NT' and resp1 == '2♥' and rebid_bid == '2♠':
        if resp2 in ('פס', '4♠'): return 'פס'
        if resp2 == '3NT':   # 10+, 5♠ מאוזן — עם 3♠ עדיף 4♠
            return '4♠' if sl(hand, '♠') >= 3 else 'פס'
        if resp2 == '3♠':    # הזמנה 8-9 עם 6♠
            return '4♠' if pts >= 16 else 'פס'
        if resp2 == '2NT':   # הזמנה 8-9, 5♠ מאוזן
            if sl(hand, '♠') >= 3: return '4♠' if pts >= 17 else '3♠'
            return '3NT' if pts >= 17 else 'פס'
        if resp2 == '3♥':    # 10+, 5♠+5♥ גיים-פורסינג — בוחר
            return '4♥' if sl(hand, '♥') >= 4 else '4♠'

    # ── אחרי תמיכה במינור + תשובה שנייה בסדרה חדשה ──────────────────────────
    resp_suit = resp1[1] if len(resp1) == 2 else ''
    if resp2 and len(resp2) == 2 and resp2[0] in '23' and resp2[1] in SUIT_RANK and resp2[1] != resp_suit:
        new_suit = resp2[1]
        if sl(hand, new_suit) >= 4:
            if pts >= 14: return f'4{new_suit}' if new_suit in ('♥','♠') else f'5{new_suit}'
            return f'3{new_suit}'
        if pts >= 14: return f'4{resp_suit}' if resp_suit in ('♥','♠') else '3NT'
        return f'3{resp_suit}' if resp_suit in ('♥','♠') else 'פס'

    # ── המשיב שאל RKCB אחרי התמיכה הפשוטה שלנו (1m→1M→2M→4NT) ────────────────
    if (opening in ('1♣','1♦') and len(resp1) == 2 and resp1[1] in ('♥','♠')
            and rebid_bid == f'2{resp1[1]}' and resp2 == '4NT'):
        return rkcb_response_bid(hand, resp1[1])

    # ── פתחנו מינור, המשיב חוזר על סדרתו ברמה 2 (מינימום, 6-9) ────────────────
    # 19+7=26 — גיים. אותו סף כמו 1M→1NT→3NT (שורה 445).
    if (opening in ('1♣','1♦') and len(resp1) == 2 and resp1[0] == '1'
            and resp1[1] in ('♥','♠') and resp2 == f'2{resp1[1]}'):
        if pts >= 19: return '3NT'
        return 'פס'

    # ── תשובות גנריות ──────────────────────────────────────────────────────────
    if resp2 == '2NT':
        if pts >= 14: return '3NT'
        return 'פס'
    # אחרי 1מינור→1NT→2NT→3NT: N תיאר 15-17, S קיבל — גיים בלבד, לא סלאם
    if opening in ('1♣','1♦') and resp1 == '1NT' and rebid_bid == '2NT' and resp2 == '3NT':
        return 'פס'
    if resp2 == '3NT':
        if pts >= 16: return '6NT'   # פותח חזק → נסה סלאם
        return 'פס'

    resp_suit = resp1[1] if len(resp1) == 2 else ''
    if resp2 == f'3{resp_suit}':
        if pts >= 14: return f'4{resp_suit}'
        return 'פס'

    return 'פס'

# ── דאבל טייקאוט (E/W) ────────────────────────────────────────────────────────
def takeout_double_ok(hand, auction_so_far):
    """האם היד מתאימה לדאבל טייקאוט? 12+ נק', שורטנס בצבע הפותח, 3+ בכל צבע אחר"""
    pts = hcp(hand)
    if pts < 12: return False
    real_bids = [b for b in auction_so_far
                 if b not in ('פס','X','XX') and b[0:1].isdigit()]
    if len(real_bids) != 1: return False   # רק מיד אחרי הפתיחה (לא אחרי תגובה)
    open_bid = real_bids[0]
    if open_bid[0] != '1': return False    # רק אחרי פתיחה ברמה 1
    open_suit = open_bid[1]
    if open_suit not in SUIT_RANK: return False   # לא אחרי 1NT
    if sl(hand, open_suit) > 2: return False
    for suit in SUITS:
        if suit != open_suit and sl(hand, suit) < 3: return False
    return True

def respond_to_double(hand, auction_so_far):
    """תשובה לדאבל טייקאוט של שותף — חייבים לכריז"""
    pts = hcp(hand)
    open_bid = next((b for b in auction_so_far
                     if b not in ('פס','X','XX') and b[0:1].isdigit()), None)
    if not open_bid: return 'פס'
    open_suit = open_bid[1]
    top_level, top_rank = auction_height(auction_so_far)

    def avail(level, suit):
        r = 4 if suit == 'NT' else SUIT_RANK.get(suit, -1)
        return (level, r) > (top_level, top_rank)

    # עצור בצבע הפותח ו-8+ נק' → NT
    if pts >= 8 and has_stopper(hand, open_suit):
        if avail(1, 'NT'): return '1NT'
        if avail(2, 'NT'): return '2NT'

    # בחר סדרה ארוכה ביותר (מיגורים עדיפים בשוויון)
    best_suit, best_len = None, -1
    for suit in ['♠','♥','♦','♣']:
        if suit == open_suit: continue
        length = sl(hand, suit)
        if length > best_len:
            best_suit, best_len = suit, length

    if not best_suit: return 'פס'
    rank = SUIT_RANK[best_suit]
    level = top_level if rank > top_rank else top_level + 1
    if pts >= 9: level = min(level + 1, 4)   # קפיצה עם 9-11 נק'
    if not avail(level, best_suit): return 'פס'
    return f'{level}{best_suit}'

# ── אוברקול (E/W) ─────────────────────────────────────────────────────────────
def auction_height(auction_so_far):
    """מחזיר (רמה, דירוג_צבע) של ההכרזה הגבוהה ביותר עד כה"""
    best = (0, -1)
    for bid in auction_so_far:
        if bid == 'פס' or not bid[0].isdigit():
            continue
        level = int(bid[0])
        rest  = bid[1:]
        rank  = 4 if rest == 'NT' else SUIT_RANK.get(rest, -1)
        if rank >= 0 and (level, rank) > best:
            best = (level, rank)
    return best

def overcall(hand, auction_so_far):
    """אוברקול פשוט: רמה 1 (9-16 נק') או רמה 2 (12-16 נק'), 5+ קלפים, 5+ נק' גבוהות"""
    pts = hcp(hand)
    if pts < 9 or pts > 16:
        return 'פס'

    top_level, top_rank = auction_height(auction_so_far)
    if top_level == 0:
        return 'פס'   # אין פתיחה עדיין

    best_suit, best_level, best_length = None, 99, 0

    for suit in ['♠', '♥', '♦', '♣']:
        length = sl(hand, suit)
        shcp   = suit_hcp(hand, suit)
        if length < 5 or shcp < 5:
            continue

        suit_rank     = SUIT_RANK[suit]
        needed_level  = top_level if suit_rank > top_rank else top_level + 1

        if needed_level == 1 and pts < 9:  continue
        if needed_level == 2 and pts < 12: continue
        if needed_level > 2:               continue   # רק רמות 1-2

        if needed_level < best_level or (needed_level == best_level and length > best_length):
            best_suit, best_level, best_length = suit, needed_level, length

    return f'{best_level}{best_suit}' if best_suit else 'פס'

# ── תשובה שלישית של המשיב ────────────────────────────────────────────────────
def third_response_bid(hand, ns_real):
    """המשיב עונה אחרי rebid שני של הפותח (5 הכרזות N/S)."""
    pts = hcp(hand)
    opening, resp1, rebid_bid, resp2, opener_rebid2 = ns_real
    resp_suit = resp1[1] if len(resp1) == 2 else ''

    # אחרי סטיימן 2♣ (2♣→2♦→2NT→3♣→3x) — 2NT מראה 23-24, למשיב 3-6.
    # יש התאמה 4-4 → גיים במיגור. אין → 3NT.
    if (opening == '2♣' and resp1 == '2♦'
            and rebid_bid == '2NT' and resp2 == '3♣'):
        if opener_rebid2 in ('3♥','3♠') and sl(hand, opener_rebid2[1]) >= 4:
            return f'4{opener_rebid2[1]}'
        return '3NT'

    # אחרי 3M של הפותח (הזמנה לגיים) — קבל עם 8+ נק'
    if (len(opener_rebid2) == 2 and opener_rebid2[0] == '3'
            and opener_rebid2[1] in ('♥','♠') and opener_rebid2[1] == resp_suit):
        return f'4{resp_suit}' if pts >= 8 else 'פס'
    return 'פס'

# ── חישוב רצף מלא ────────────────────────────────────────────────────────────
ORDER    = ['N','E','S','W']

def compute_auction(hands, dealer, cfg):
    idx           = ORDER.index(dealer)
    auction       = []
    passes        = 0
    ns_opener     = None   # השחקן שפתח (ראשון מהזוג הלומד שהכריז הכרזה אמיתית)
    # הזוג הלומד נקבע לפי הדילר: N/S או E/W
    teaching_pair = {'N','S'} if dealer in ('N','S') else {'E','W'}

    for turn in range(40):
        player = ORDER[(idx + turn) % 4]
        hand   = hands[player]

        # הזוג הלא-לומד — אוברקול, דאבל, או תשובה לדאבל
        if player not in teaching_pair:
            partner = PARTNER_MAP[player]
            my_bid = next((auction[i] for i in range(len(auction))
                           if ORDER[(idx+i)%4] == player and auction[i] != 'פס'), None)
            partner_bid = next((auction[i] for i in range(len(auction))
                                if ORDER[(idx+i)%4] == partner and auction[i] != 'פס'), None)
            if my_bid is not None:
                bid = 'פס'                             # כבר הכרזתי
            elif partner_bid == 'X':
                bid = respond_to_double(hand, auction)  # שותף דאבל — עניתי
            elif partner_bid is not None:
                bid = 'פס'                             # שותף אוברקל — פס
            else:
                oc = overcall(hand, auction)
                bid = oc if oc != 'פס' else ('X' if takeout_double_ok(hand, auction) else 'פס')
        else:
            ns_real = [b for i,b in enumerate(auction)
                       if b != 'פס' and ORDER[(idx+i)%4] in teaching_pair]
            if not ns_real:
                bid = opening_bid(hand, cfg)
                if bid != 'פס':
                    ns_opener = player
            elif len(ns_real) == 1:
                if player == ns_opener:
                    bid = 'פס'   # פותח לא מכריז שוב לפני שהמשיב הגיב
                else:
                    ew_oc = next((auction[i] for i in range(len(auction))
                                  if auction[i] != 'פס' and ORDER[(idx+i)%4] not in teaching_pair), None)
                    bid = response(hand, ns_real[0], cfg, ew_oc)
            elif len(ns_real) == 2:
                if ns_real[1] == 'XX':
                    # אחרי XX של המשיב — פותח מחכה. אם EW ברחו → דאבל עונשין עם 14+
                    ew_escape = next((auction[i] for i in range(len(auction))
                                      if ORDER[(idx+i)%4] not in teaching_pair
                                      and auction[i] not in ('פס','X','XX')
                                      and auction[i][0:1].isdigit()), None)
                    bid = 'X' if (ew_escape and hcp(hand) >= 14) else 'פס'
                else:
                    ew_oc2 = next((auction[i] for i in range(len(auction))
                                   if auction[i] not in ('פס','XX')
                                   and ORDER[(idx+i)%4] not in teaching_pair), None)
                    bid = rebid(hand, ns_real[0], ns_real[1], cfg, ew_oc2)
            elif len(ns_real) == 3:
                bid = second_response(hand, ns_real[0], ns_real[1], ns_real[2], cfg)
            elif len(ns_real) == 4:
                # RKCB — הפותח מחליט על סלאם לפי סך קלפי המפתח של שני השחקנים
                ns_resp = 'S' if ns_opener == 'N' else 'N'
                if ns_real[2] == '4NT' and ns_real[0] in ('1♥','1♠'):
                    trump = ns_real[0][1]
                    # RKCB רק אחרי תמיכה במיגור — אחרת 4NT כמותי → פס
                    resp_supported_trump = (len(ns_real[1]) == 2 and ns_real[1][1] == trump)
                    if resp_supported_trump:
                        total_kc   = count_key_cards(hands[ns_opener], trump) + \
                                     count_key_cards(hands[ns_resp],   trump)
                        if total_kc >= 5: bid = f'7{trump}'
                        elif total_kc >= 4: bid = f'6{trump}'
                        else: bid = f'5{trump}'
                    else:
                        bid = 'פס'   # 4NT כמותי — המשיב כבר החליט (6NT/פס)
                elif ns_real[0] == '2♣' and ns_real[2] in ('2♠','2♥','3♣','3♦') and ns_real[2] == '4NT':
                    # 2♣-resp-4NT(RKCB opener)-RKCB answer: opener bids slam
                    trump = ns_real[2][1]
                    total_kc = count_key_cards(hands[ns_opener], trump) + \
                               count_key_cards(hands[ns_resp],   trump)
                    if total_kc >= 5: bid = f'7{trump}'
                    elif total_kc >= 4: bid = f'6{trump}'
                    else: bid = f'5{trump}'
                else:
                    bid = opener_second_rebid(hand, ns_real[0], ns_real[1], ns_real[2], ns_real[3], cfg)
            elif len(ns_real) == 5:
                # סלאם אחרי קיו-ביד + RKCB של המשיב (1M→3M→4x→4NT→RKCB_answer)
                if (ns_real[0] in ('1♥','1♠') and ns_real[1] == f'3{ns_real[0][1]}'
                        and is_cue_bid(ns_real[2], ns_real[0][1]) and ns_real[3] == '4NT'):
                    trump = ns_real[0][1]
                    ns_resp = PARTNER_MAP[ns_opener]
                    total_kc = count_key_cards(hands[ns_opener], trump) + \
                               count_key_cards(hands[ns_resp],   trump)
                    if total_kc >= 5: bid = f'7{trump}'
                    elif total_kc >= 4: bid = f'6{trump}'
                    else: bid = f'4{trump}'
                # RKCB אחרי תמיכה פשוטה של הפותח (1m→1M→2M→4NT→תשובה)
                elif (ns_real[0] in ('1♣','1♦') and len(ns_real[1]) == 2
                        and ns_real[1][1] in ('♥','♠')
                        and ns_real[2] == f'2{ns_real[1][1]}' and ns_real[3] == '4NT'):
                    trump   = ns_real[1][1]
                    ns_resp = PARTNER_MAP[ns_opener]
                    total_kc = count_key_cards(hands[ns_opener], trump) + \
                               count_key_cards(hands[ns_resp],   trump)
                    if total_kc >= 5: bid = f'7{trump}'
                    elif total_kc >= 4: bid = f'6{trump}'
                    else: bid = f'5{trump}'   # חסרים 2 קלפי מפתח — עצור מתחת לסלאם
                else:
                    bid = third_response_bid(hand, ns_real)
            else:
                bid = 'פס'

        auction.append(bid)
        passes = passes + 1 if bid == 'פס' else 0
        if passes >= 3 and len(auction) >= 4:
            break

    return auction, [ORDER[(idx+i)%4] for i in range(len(auction))]
