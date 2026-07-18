# -*- coding: utf-8 -*-
"""
מנוע ניתוח הכרזות לעומק.

ממשק עיקרי:
    analyses, summary = analyze_auction(hands, dealer, auction_bids, cfg)
    print(format_analysis(analyses, summary, hands))
"""

from bidding_engine import (
    hcp, sl, total_pts, is_balanced, suit_hcp, has_stopper, has_ace,
    count_key_cards, count_aces,
    opening_bid, response, rebid, second_response, opener_second_rebid,
    overcall, takeout_double_ok, respond_to_double,
    auction_height, is_cue_bid, rkcb_response_bid, gerber_response,
    SUITS, SUIT_RANK, PARTNER_MAP,
)

ORDER = ['N', 'E', 'S', 'W']

GAME_LEVEL = {'NT': 3, '♠': 4, '♥': 4, '♦': 5, '♣': 5}
SLAM_LEVEL = 6

SUIT_HE = {'♠': 'ספייד', '♥': 'לבבות', '♦': 'יהלומים', '♣': 'תלתנים'}
PLAYER_HE = {'N': 'צפון', 'S': 'דרום', 'E': 'מזרח', 'W': 'מערב'}


# ─── עזרים ────────────────────────────────────────────────────────────────────

def _parse_bid(bid):
    if not bid or bid in ('פס', 'X', 'XX') or len(bid) < 2:
        return None
    try:
        return int(bid[0]), bid[1:]
    except ValueError:
        return None


def _is_game(bid):
    pb = _parse_bid(bid)
    return pb and pb[0] >= GAME_LEVEL.get(pb[1], 99)


def _is_slam(bid):
    pb = _parse_bid(bid)
    return pb and pb[0] >= SLAM_LEVEL


def hand_info(hand, cfg=None):
    """מחזיר dict עם נתוני יד עיקריים."""
    pts = hcp(hand)
    tp  = total_pts(hand)
    bal = is_balanced(hand)
    lens = {s: sl(hand, s) for s in SUITS}
    return {
        'hcp': pts, 'total_pts': tp, 'balanced': bal, 'lengths': lens,
        'lens_str': '  '.join(f'{s}{lens[s]}' for s in SUITS),
    }


def _first_ew_bid(auction_bids, players, before_idx, teaching_pair):
    """מחזיר את ההכרזה הראשונה של הזוג היריב (לא פס) לפני מיקום given."""
    for j in range(before_idx):
        if players[j] not in teaching_pair and auction_bids[j] not in ('פס',):
            return auction_bids[j]
    return None


def _ew_bid_after(auction_bids, players, after_idx, before_idx, teaching_pair):
    """מחזיר הכרזת הזוג היריב (לא פס/XX) בין after_idx ו-before_idx."""
    for j in range(after_idx, before_idx):
        if players[j] not in teaching_pair and auction_bids[j] not in ('פס', 'XX'):
            return auction_bids[j]
    return None


# ─── זיהוי מוסכמות ─────────────────────────────────────────────────────────────

def identify_convention(bid, ns_history):
    """
    מזהה מוסכמה לפי הכרזה ורקע ההכרזות של N/S עד כה.
    ns_history — רשימת הכרזות N/S (לא פס) לפני ההכרזה הנוכחית.
    """
    if not bid or bid == 'פס':
        return None

    n = len(ns_history)
    prev = ns_history  # alias for clarity

    # ── פתיחות ──────────────────────────────────────────────────────────────
    if n == 0:
        if bid == '2♣':                                  return '2♣ חזקה'
        if bid == '2NT':                                 return 'פתיחת 2NT (20-22)'
        if bid == '1NT':                                 return 'פתיחת 1NT'
        if len(bid) == 2 and bid[0] == '2' and bid[1] in SUIT_RANK:
            return 'פתיחה חלשה (6-9 נק\')'
        if len(bid) == 2 and bid[0] == '3':             return 'פרי-אמפט ברמה 3'
        if len(bid) == 2 and bid[0] == '4':             return 'פרי-אמפט ברמה 4'
        return None

    opening = prev[0]

    # ── תשובות ל-1NT ─────────────────────────────────────────────────────────
    if n == 1 and opening == '1NT':
        if bid == '2♣':  return 'סטיימן'
        if bid == '2♦':  return 'טרנספר ל-♥'
        if bid == '2♥':  return 'טרנספר ל-♠'
        if bid == '4♣':  return "ג'רבר — ספירת אסים"
        if bid == '4NT': return 'הזמנת סלאם כמותית'
        if bid == '2♦':  return 'טרנספר ל-♥'

    # ── תשובות ל-2NT ─────────────────────────────────────────────────────────
    if n == 1 and opening == '2NT':
        if bid == '3♣':  return 'סטיימן'
        if bid == '3♦':  return 'טרנספר ל-♥'
        if bid == '3♥':  return 'טרנספר ל-♠'
        if bid == '4NT': return 'הזמנת סלאם כמותית'

    # ── תשובה ל-2♣ חזקה ──────────────────────────────────────────────────────
    if n == 1 and opening == '2♣':
        if bid == '2♦':  return 'תשובה שלילית ל-2♣'
        if bid == '2NT': return 'תשובה חיובית ללא צבע (7+ נק\')'
        if len(bid) == 2 and bid[1] in SUIT_RANK:
            return f'תשובה חיובית עם {SUIT_HE.get(bid[1], bid[1])}'

    # ── השלמת טרנספר ─────────────────────────────────────────────────────────
    if n == 2:
        if prev[0] == '1NT' and prev[1] == '2♦' and bid == '2♥':
            return 'השלמת טרנספר ל-♥'
        if prev[0] == '1NT' and prev[1] == '2♥' and bid == '2♠':
            return 'השלמת טרנספר ל-♠'
        if prev[0] == '2NT' and prev[1] == '3♦' and bid == '3♥':
            return 'השלמת טרנספר ל-♥'
        if prev[0] == '2NT' and prev[1] == '3♥' and bid == '3♠':
            return 'השלמת טרנספר ל-♠'

    # ── תשובת סטיימן ─────────────────────────────────────────────────────────
    if n == 2:
        if prev[0] == '1NT' and prev[1] == '2♣':
            return 'תשובה לסטיימן'
        if prev[0] == '2NT' and prev[1] == '3♣':
            return 'תשובה לסטיימן'

    # ── RKCB ─────────────────────────────────────────────────────────────────
    if bid == '4NT' and n >= 2:
        # בדוק אם יש הסכמה על צבע מיגור
        for b in prev:
            pb = _parse_bid(b)
            if pb and pb[1] in ('♥', '♠') and pb[0] >= 2:
                return 'RKCB — שאלה על קלפי מפתח'

    # ── תשובה ל-RKCB ─────────────────────────────────────────────────────────
    if bid in ('5♣', '5♦', '5♥', '5♠') and '4NT' in prev:
        return 'תשובה ל-RKCB'

    # ── קיו-ביד ─────────────────────────────────────────────────────────────
    if len(bid) == 2 and bid[0] == '4' and bid[1] in SUIT_RANK:
        # חפש צבע מוסכם
        for b in prev:
            pb = _parse_bid(b)
            if pb and pb[1] in ('♥', '♠') and pb[0] >= 2:
                trump = pb[1]
                if is_cue_bid(bid, trump):
                    suit_name = SUIT_HE.get(bid[1], bid[1])
                    return f"קיו-ביד — הצגת א' ב-{suit_name}"
                break

    # ── ג'רבר (תשובה) ─────────────────────────────────────────────────────────
    if n >= 2 and prev[0] in ('1NT', '2NT') and prev[1] == '4♣':
        return "תשובה לג'רבר"

    # ── דאבל / רדאבל ─────────────────────────────────────────────────────────
    if bid == 'X':  return 'דאבל נגטיבי'
    if bid == 'XX': return "רדאבל — יד חזקה (10+ נק')"

    return None


# ─── הסברים לפתיחה ────────────────────────────────────────────────────────────

def _explain_opening(hand, bid, expected, cfg):
    pts = hcp(hand)
    h = sl(hand, '♥'); s = sl(hand, '♠')
    c = sl(hand, '♣'); d = sl(hand, '♦')
    bal = is_balanced(hand)
    ntmin = cfg.get('ntMin', 15); ntmax = cfg.get('ntMax', 17)
    mj = cfg.get('majorLen', 5)
    correct = (bid == expected)
    mark = '✓' if correct else '✗'

    def wrong(why):
        return f'{mark} {"נכון" if correct else f"שגיאה! הכרזת {bid} — {expected} נכון"}. {why}'

    if pts < 12:
        # Could be weak/preempt or pass
        if expected == 'פס':
            if correct:
                return f'✓ נכון — פס עם {pts} נק\' (פחות מ-12).'
            else:
                return wrong(f'עם {pts} נק\' — פס נדרש, אלא אם יש 6+ קלפים לפתיחה חלשה.')
        else:
            lvl = expected[0]; suit = expected[1] if len(expected) > 1 else ''
            slen = sl(hand, suit) if suit in SUIT_RANK else 0
            shcp = suit_hcp(hand, suit) if suit in SUIT_RANK else 0
            if lvl in '234':
                return f'{mark} {"נכון" if correct else f"שגיאה! {expected} נכון"}. ' \
                       f'פתיחה חלשה — {slen} {SUIT_HE.get(suit,suit)}, {shcp} נק\' גבוהות בסדרה, {pts} נק\' כולל.'

    if expected == '2♣':
        return f'{mark} {"נכון" if correct else f"שגיאה — {expected} נכון"}. ' \
               f'{pts} נק\' — חזק מאוד, דורש 2♣.'

    if expected == '2NT':
        return f'{mark} {"נכון" if correct else f"שגיאה — {expected} נכון"}. ' \
               f'{pts} נק\', מאוזן — 2NT (20-22).'

    if expected == '1NT':
        return f'{mark} {"נכון" if correct else f"שגיאה — {expected} נכון"}. ' \
               f'{pts} נק\' ({ntmin}-{ntmax}), יד מאוזנת — 1NT. גובר על 5 קלפים במיגור.'

    if expected in ('1♥', '1♠'):
        suit = expected[1]
        slen = sl(hand, suit)
        other = '♠' if suit == '♥' else '♥'
        olen  = sl(hand, other)
        base  = f'{mark} {"נכון" if correct else f"שגיאה — {expected} נכון"}. ' \
                f'{slen} {SUIT_HE[suit]}'
        if suit == '♥' and olen >= mj:
            base += f', ♥{h} ≥ ♠{s} → 1♥ ראשון'
        base += f', {pts} נק\'.'
        return base

    if expected in ('1♣', '1♦'):
        reason = ''
        if c >= d: reason = f'♣({c}) ≥ ♦({d}) → 1♣'
        else:      reason = f'♦({d}) > ♣({c}) → 1♦'
        return f'{mark} {"נכון" if correct else f"שגיאה — {expected} נכון"}. ' \
               f'אין 5+ קלפים במיגור. {reason}, {pts} נק\'.'

    if expected == 'פס':
        return f'{mark} {"נכון" if correct else f"שגיאה — פס נכון"}. {pts} נק\'.'

    return f'{mark} {"נכון" if correct else f"שגיאה — {expected} נכון"}. {pts} נק\'.'


# ─── הסברים לתשובה ────────────────────────────────────────────────────────────

def _explain_response(hand, opening, bid, expected, cfg, ew_oc=None):
    pts = hcp(hand)
    h = sl(hand, '♥'); s = sl(hand, '♠')
    c = sl(hand, '♣'); d = sl(hand, '♦')
    bal = is_balanced(hand)
    ntmin = cfg.get('ntMin', 15); ntmax = cfg.get('ntMax', 17)
    correct = (bid == expected)
    mark = '✓' if correct else '✗'
    wrong_prefix = '' if correct else f'שגיאה! הכרזת {bid} — {expected} נכון. '

    oc_note = f' (יש אוברקול {ew_oc})' if ew_oc else ''

    # ── פס ─────────────────────────────────────────────────────────────────
    if pts < 6:
        if correct:
            return f'✓ נכון — פס, {pts} נק\' (פחות מ-6){oc_note}.'
        return f'✗ {wrong_prefix}עם {pts} נק\' — פס נדרש{oc_note}.'

    # ── תשובה ל-1NT ─────────────────────────────────────────────────────────
    if opening == '1NT':
        ntrange = f'{ntmin}-{ntmax}'
        if h >= 5:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{h} לבבות — טרנספר 2♦ (בלי קשר לחוזק){oc_note}.'
        if s >= 5:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{s} ספייד — טרנספר 2♥ (בלי קשר לחוזק){oc_note}.'
        four_suits = sum(1 for su in SUITS if sl(hand, su) >= 4)
        if (h >= 4 or s >= 4) and pts >= 8 and four_suits >= 2:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\', 4+ מיגור — סטיימן 2♣{oc_note}.'
        gerber_thr = 33 - ntmin
        qt_thr     = 33 - ntmax
        game_thr   = 25 - ntmin
        inv_thr    = 25 - ntmax
        if pts >= gerber_thr:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — ג\'רבר 4♣ (בדוק אסים לפני סלאם){oc_note}.'
        if pts >= qt_thr:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — הזמנת סלאם כמותית 4NT{oc_note}.'
        if pts >= game_thr:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — גיים: 3NT{oc_note}.'
        if pts >= inv_thr:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — הזמנה: 2NT{oc_note}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}' \
               f'{pts} נק\' — פס (מינימום){oc_note}.'

    # ── תשובה ל-2NT ─────────────────────────────────────────────────────────
    if opening == '2NT':
        if h >= 5:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{h} לבבות — טרנספר 3♦{oc_note}.'
        if s >= 5:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{s} ספייד — טרנספר 3♥{oc_note}.'
        if pts < 4:
            return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — פס{oc_note}.'
        if h >= 4 or s >= 4:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'4+ מיגור — סטיימן 3♣{oc_note}.'
        if pts >= 13:
            return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — 6NT{oc_note}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — 3NT{oc_note}.'

    # ── תשובה ל-2♣ חזקה ──────────────────────────────────────────────────────
    if opening == '2♣':
        if pts <= 6:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — תשובה שלילית 2♦{oc_note}.'
        for suit in ['♠', '♥']:
            if sl(hand, suit) >= 5:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{pts} נק\', 5+ {SUIT_HE[suit]} — תשובה חיובית 2{suit}{oc_note}.'
        for suit in ['♦', '♣']:
            if sl(hand, suit) >= 5:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{pts} נק\', 5+ {SUIT_HE[suit]} — תשובה חיובית 3{suit}{oc_note}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}' \
               f'{pts} נק\', אין 5 קלפים בצבע — 2NT{oc_note}.'

    # ── תשובה לפתיחה חלשה ────────────────────────────────────────────────────
    if opening[0] in '234' and len(opening) == 2 and opening[1] in SUIT_RANK:
        open_suit = opening[1]
        support   = sl(hand, open_suit)
        is_major  = open_suit in ('♥', '♠')
        if support >= 2 and is_major and pts >= 13:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{support} תמיכה + {pts} נק\' — גיים 4{open_suit}{oc_note}.'
        if support >= 3 and not is_major and pts >= 14:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{support} תמיכה + {pts} נק\' — גיים 5{open_suit}{oc_note}.'
        if pts < 15:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — פס (פתיחה חלשה, אין מספיק לגיים){oc_note}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}' \
               f'{pts} נק\' — {expected}{oc_note}.'

    # ── תשובה למיגור 1♥/1♠ ───────────────────────────────────────────────────
    if opening in ('1♥', '1♠'):
        open_suit = opening[1]
        support   = sl(hand, open_suit)
        if support >= 3:
            if pts >= 13:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{support} תמיכה + {pts} נק\' — גיים 4{open_suit}{oc_note}.'
            if pts >= 10:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{support} תמיכה + {pts} נק\' — הזמנה 3{open_suit}{oc_note}.'
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{support} תמיכה + {pts} נק\' — תמיכה מינימום 2{open_suit}{oc_note}.'
        # ♥ response shows ♠
        if opening == '1♥' and s >= 4:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{s} ספייד + {pts} נק\' — הצג 1♠{oc_note}.'
        # 2-over-1: new suit at 2-level
        if pts >= 11:
            for suit in ['♥', '♦', '♣']:
                if suit != open_suit and sl(hand, suit) >= 5:
                    return f'{mark} {"נכון" if correct else wrong_prefix}' \
                           f'{pts} נק\', 5+ {SUIT_HE[suit]} — כפוי לגיים (2-over-1){oc_note}.'
            if pts >= 11 and opening == '1♠' and h >= 4:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{h} לבבות + {pts} נק\' — 2♥ (2-over-1){oc_note}.'
        if pts >= 13 and bal:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\', מאוזן, ללא תמיכה — קפיצה 3NT{oc_note}.'
        if pts >= 6:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\', ללא פיט — 1NT{oc_note}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — פס{oc_note}.'

    # ── תשובה למינור 1♣/1♦ ───────────────────────────────────────────────────
    if opening in ('1♣', '1♦'):
        if h >= 5 and s >= 5:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'5♥+5♠ — הכריז 1♠ (הגבוה ראשון){oc_note}.'
        if h >= 4 and s <= h:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{h} לבבות — 1♥ ראשון{oc_note}.'
        if s >= 4:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{s} ספייד — 1♠{oc_note}.'
        if pts >= 13 and bal:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\', מאוזן — 3NT{oc_note}.'
        if pts >= 6:
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — 1NT{oc_note}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — פס{oc_note}.'

    # fallback
    if correct:
        return f'✓ נכון — {bid}{oc_note}.'
    return f'✗ שגיאה! {bid} → {expected}{oc_note}.'


# ─── הסברים ל-rebid ────────────────────────────────────────────────────────────

def _explain_rebid(hand, opening, resp, bid, expected, cfg):
    pts = hcp(hand)
    tp  = total_pts(hand)
    h   = sl(hand, '♥'); s = sl(hand, '♠')
    correct = (bid == expected)
    mark = '✓' if correct else '✗'
    wrong_prefix = '' if correct else f'שגיאה! {bid} → {expected}. '
    open_suit = opening[1] if len(opening) == 2 and opening[1] in SUIT_RANK else ''

    # ── rebid אחרי 1NT/2NT ────────────────────────────────────────────────────
    if opening in ('1NT', '2NT'):
        ntmax = cfg.get('ntMax', 17)
        if resp == '4♣':
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f"תשובה לג'רבר — {bid}."
        if resp in ('2♦', '2♥') and opening == '1NT':
            return f'{mark} {"נכון" if correct else wrong_prefix}השלמת טרנספר.'
        if resp in ('3♦', '3♥') and opening == '2NT':
            return f'{mark} {"נכון" if correct else wrong_prefix}השלמת טרנספר.'
        if resp == '2♣' and opening == '1NT':
            return f'{mark} {"נכון" if correct else wrong_prefix}תשובה לסטיימן: ' \
                   f'{"4♠" if s >= 4 else "4♥" if h >= 4 else "2♦ (אין מיגור)"}.'
        if resp in ('2NT', '4NT'):
            return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — {expected}.'
        return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\'.'

    # ── rebid אחרי פתיחה חלשה ────────────────────────────────────────────────
    if opening in ('2♥', '2♠', '2♦'):
        return f'{mark} {"נכון" if correct else wrong_prefix}' \
               f'פותח חלש — תיאר ידו, ממתין לשותף.'

    # ── rebid אחרי פתיחת מיגור ───────────────────────────────────────────────
    if opening in ('1♥', '1♠') and open_suit:
        open_len = sl(hand, open_suit)
        support  = resp and len(resp) == 2 and resp[1] == open_suit

        if resp == f'4{open_suit}':
            return f'{mark} {"נכון" if correct else wrong_prefix}גיים הושג — פס.'

        if resp == f'3{open_suit}':
            if tp >= 23:
                note = f'RKCB — {tp} נק\', שאל על קלפי מפתח.'
            elif tp >= 19:
                note = f'קיו-ביד תחילה — {tp} נק\' (הצג א\' לצורך סלאם).'
            elif tp >= 15:
                note = f'קבל הזמנה — {tp} נק\': 4{open_suit}.'
            else:
                note = f'מינימום — {tp} נק\': פס.'
            return f'{mark} {"נכון" if correct else wrong_prefix}{note}'

        if resp == f'2{open_suit}':
            if pts >= 19:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{pts} נק\' חזק — גיים ישיר 4{open_suit}.'
            if pts >= 16:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{pts} נק\' — הזמנה 3{open_suit}.'
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — מינימום, פס.'

        if resp == '1NT':
            if open_len >= 5 and pts >= 14:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'5+ {SUIT_HE[open_suit]}, {pts} נק\' — חזור 2{open_suit}.'
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' / {open_len} קלפים — פס.'

        if opening == '1♥' and resp == '1♠':
            if s >= 4:
                if tp >= 15:
                    return f'{mark} {"נכון" if correct else wrong_prefix}' \
                           f'4 ספייד + {tp} נק\' — גיים 4♠.'
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'4 ספייד, מינימום — 2♠.'
            if pts >= 15:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{pts} נק\', אין 4♠ — {expected}.'
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'5+ {SUIT_HE[open_suit]}, {pts} נק\' — חזור 2{open_suit}.'

    # ── rebid אחרי פתיחת מינור ───────────────────────────────────────────────
    if opening in ('1♣', '1♦') and open_suit:
        if resp in ('1♥', '1♠'):
            resp_suit = resp[1]
            support   = sl(hand, resp_suit)
            min_sup   = 4 if resp_suit == '♠' else 3
            if support >= min_sup:
                if tp >= 18:
                    return f'{mark} {"נכון" if correct else wrong_prefix}' \
                           f'{support} תמיכה + {tp} נק\' — גיים 4{resp_suit}.'
                if tp >= 16:
                    return f'{mark} {"נכון" if correct else wrong_prefix}' \
                           f'{support} תמיכה + {tp} נק\' — הזמנה 3{resp_suit}.'
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'{support} תמיכה + {tp} נק\' — מינימום 2{resp_suit}.'
            if resp == '1♥' and s >= 4:
                return f'{mark} {"נכון" if correct else wrong_prefix}' \
                       f'4 ספייד — הצג 1♠.'
            if pts >= 18:
                return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — 3NT.'
            if pts >= 15:
                return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — 2NT.'
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — 1NT (מינימום).'

        if resp == '1NT':
            if pts >= 18:
                return f'{mark} {"נכון" if correct else wrong_prefix}{pts} נק\' — 2NT.'
            return f'{mark} {"נכון" if correct else wrong_prefix}' \
                   f'{pts} נק\' — פס (מינימום).'

    # fallback
    if correct:
        return f'✓ נכון — {bid}. {pts} נק\'.'
    return f'✗ שגיאה! {bid} → {expected}. {pts} נק\'.'


# ─── הסבר גנרי ───────────────────────────────────────────────────────────────

def _explain_generic(hand, bid, expected, role):
    pts = hcp(hand)
    correct = (bid == expected)
    if correct:
        return f'✓ נכון — {bid}. ({pts} נק\')'
    return f'✗ שגיאה! הכרזת {bid} במקום {expected} ({role}). {pts} נק\'.'


def _explain_ew(hand, bid, prev_bids, prev_players, cfg, teaching_pair=None):
    if teaching_pair is None:
        teaching_pair = {'N', 'S'}
    pts = hcp(hand)
    if bid == 'פס':
        return f'{pts} נק\' — פס.'
    if bid == 'X':
        open_bid = next((b for b, p in zip(prev_bids, prev_players)
                         if p in teaching_pair and b != 'פס'), None)
        short = open_bid[1] if (open_bid and len(open_bid) == 2) else '?'
        return f'{pts} נק\', שורטנס ב-{short} — דאבל טייקאוט.'
    if bid == 'XX':
        return f'{pts} נק\' גבוהים — רדאבל.'
    if len(bid) == 2 and bid[0].isdigit() and bid[1] in SUIT_RANK:
        suit  = bid[1]
        slen  = sl(hand, suit)
        shcp  = suit_hcp(hand, suit)
        return f'{slen} {SUIT_HE[suit]}, {shcp} נק\' בסדרה, {pts} נק\' כולל — אוברקול {bid}.'
    return f'{bid} — {pts} נק\'.'


# ─── פונקצית הניתוח הראשית ────────────────────────────────────────────────────

def analyze_auction(hands, dealer, auction_bids, cfg):
    """
    מנתח רצף הכרזות לעומק.

    קלט:
      hands        — {'N': hand, 'E': hand, 'S': hand, 'W': hand}
      dealer       — 'N'/'E'/'S'/'W'
      auction_bids — רשימת מחרוזות הכרזה, למשל ['1♥','פס','2♥','פס','פס','פס']
      cfg          — dict הגדרות (majorLen, ntMin, ntMax, minorLen)

    פלט:
      analyses — list of dicts (אחד לכל הכרזה)
      summary  — dict עם סיכום
    """
    idx           = ORDER.index(dealer)
    players       = [ORDER[(idx + i) % 4] for i in range(len(auction_bids))]
    teaching_pair = {'N','S'} if dealer in ('N','S') else {'E','W'}

    ns_real   = []   # הכרזות הזוג הלומד שאינן פס
    ns_opener = None # מי פתח ראשון מהזוג הלומד

    analyses = []

    for i, bid in enumerate(auction_bids):
        player = players[i]
        hand   = hands[player]
        hi     = hand_info(hand, cfg)
        is_ns  = player in teaching_pair

        analysis = {
            'bid': bid,
            'player': player,
            'is_ns': is_ns,
            'expected': bid,     # ברירת מחדל: מה שהוכרז נחשב "צפוי" (יוחלף למטה)
            'correct': True,
            'role': 'פס' if bid == 'פס' else ('הכרזה' if is_ns else 'E/W'),
            'convention': None,
            'explanation': '',
            'hand_info': hi,
            'ns_before': ns_real.copy(),
        }

        if is_ns:
            n = len(ns_real)  # כמה הכרזות N/S (לא פס) נעשו לפני

            # חפש אוברקול של הזוג היריב לפני ההכרזה הנוכחית
            ew_oc = _first_ew_bid(auction_bids, players, i, teaching_pair)

            # ──────────────────────────────────────────────────────────────
            if n == 0:
                # פתיחה
                expected = opening_bid(hand, cfg)
                analysis['role']       = 'פתיחה'
                analysis['expected']   = expected
                analysis['correct']    = (bid == expected)
                analysis['convention'] = identify_convention(bid, ns_real)
                analysis['explanation'] = _explain_opening(hand, bid, expected, cfg)
                if bid != 'פס':
                    ns_opener = player

            elif n == 1 and player == ns_opener:
                # פותח ממתין לתשובה (לא אמור לכריז)
                analysis['role']       = 'המתנה'
                analysis['expected']   = 'פס'
                analysis['correct']    = (bid == 'פס')
                analysis['explanation'] = 'פותח ממתין לתשובת השותף.'

            elif n == 1:
                # תשובה ראשונה
                opening  = ns_real[0]
                expected = response(hand, opening, cfg, ew_oc)
                analysis['role']        = f'תשובה ל-{opening}'
                analysis['expected']    = expected
                analysis['correct']     = (bid == expected)
                analysis['convention']  = identify_convention(bid, ns_real)
                analysis['explanation'] = _explain_response(
                    hand, opening, bid, expected, cfg, ew_oc)

            elif n == 2 and player == ns_opener:
                # Rebid של הפותח
                opening  = ns_real[0]
                resp1    = ns_real[1]
                # EW בין תשובה ל-rebid
                resp_idx = next(j for j in range(i - 1, -1, -1)
                                if players[j] in teaching_pair and auction_bids[j] == resp1)
                ew_oc2 = _ew_bid_after(auction_bids, players, resp_idx + 1, i, teaching_pair)
                expected = rebid(hand, opening, resp1, cfg, ew_oc2)
                analysis['role']        = 'חזרת הפותח'
                analysis['expected']    = expected
                analysis['correct']     = (bid == expected)
                analysis['convention']  = identify_convention(bid, ns_real)
                analysis['explanation'] = _explain_rebid(
                    hand, opening, resp1, bid, expected, cfg)

            elif n == 3:
                # תשובה שנייה של המשיב
                opening, resp1, rebid1 = ns_real[0], ns_real[1], ns_real[2]
                expected = second_response(hand, opening, resp1, rebid1, cfg)
                analysis['role']        = 'תשובה שנייה'
                analysis['expected']    = expected
                analysis['correct']     = (bid == expected)
                analysis['convention']  = identify_convention(bid, ns_real)
                analysis['explanation'] = _explain_generic(
                    hand, bid, expected, 'תשובה שנייה')

            elif n == 4 and player == ns_opener:
                # Rebid שני של הפותח
                opening, resp1, rebid1, resp2 = ns_real
                # RKCB slam: 1M → 3M → 4NT → RKCB_response → slam decision
                if (opening in ('1♥', '1♠')
                        and resp1 == f'3{opening[1]}'
                        and rebid1 == '4NT'):
                    trump   = opening[1]
                    ns_resp = PARTNER_MAP[ns_opener]
                    total_kc = (count_key_cards(hand, trump)
                                + count_key_cards(hands[ns_resp], trump))
                    if total_kc >= 5:   expected = f'7{trump}'
                    elif total_kc >= 4: expected = f'6{trump}'
                    else:               expected = f'5{trump}'
                else:
                    expected = opener_second_rebid(
                        hand, opening, resp1, rebid1, resp2, cfg)
                analysis['role']        = 'rebid שני'
                analysis['expected']    = expected
                analysis['correct']     = (bid == expected)
                analysis['convention']  = identify_convention(bid, ns_real)
                analysis['explanation'] = _explain_generic(
                    hand, bid, expected, 'rebid שני')

            else:
                analysis['role']        = 'המשך'
                analysis['explanation'] = f'{bid} — {hi["hcp"]} נק\'.'

            # עדכן ns_real אם ההכרזה אינה פס
            if bid != 'פס':
                ns_real.append(bid)

        else:
            # E/W
            analysis['explanation'] = _explain_ew(
                hand, bid, auction_bids[:i], players[:i], cfg, teaching_pair)

        analyses.append(analysis)

    summary = _make_summary(hands, auction_bids, players, analyses, cfg, teaching_pair)
    return analyses, summary


# ─── סיכום ────────────────────────────────────────────────────────────────────

def _make_summary(hands, auction_bids, players, analyses, cfg, teaching_pair=None):
    if teaching_pair is None:
        teaching_pair = {'N', 'S'}
    ns_hcp = sum(hcp(hands[p]) for p in teaching_pair)

    # חוזה סופי
    final_bid = final_player = None
    for bid, player in zip(auction_bids, players):
        if bid not in ('פס', 'X', 'XX'):
            final_bid, final_player = bid, player

    # שגיאות N/S (כולל פס במקום הכרזה)
    ns_errors = sum(
        1 for a in analyses
        if a['is_ns'] and not a['correct']
        and a['role'] not in ('המתנה', 'המשך', 'E/W', 'פס')
    )

    # ציון
    ns_meaningful = [a for a in analyses
                     if a['is_ns'] and a['bid'] != 'פס'
                     and a['role'] not in ('המתנה',)]
    score = max(0, 100 - ns_errors * 20) if ns_meaningful else 100

    # גיים/סלאם
    game_reached = slam_reached = False
    if final_bid and final_player in teaching_pair:
        game_reached = bool(_is_game(final_bid))
        slam_reached = bool(_is_slam(final_bid))

    game_due = ns_hcp >= 26
    slam_due = ns_hcp >= 33

    issues = []
    if final_player in teaching_pair:
        if game_due and not game_reached:
            issues.append(
                f'הזוג הלומד יש {ns_hcp} נק\' — היה צריך להגיע לגיים! (עצרו ב-{final_bid})')
        if slam_due and not slam_reached:
            issues.append(
                f'הזוג הלומד יש {ns_hcp} נק\' — היה צריך סלאם! (עצרו ב-{final_bid})')
        if ns_hcp <= 20 and game_reached and not slam_reached:
            issues.append(
                f'הגעתם לגיים ({final_bid}) עם רק {ns_hcp} נק\' — אולי הגזמה?')

    # רצף הזוג הלומד
    ns_auction = [b for b, p in zip(auction_bids, players) if p in teaching_pair]

    return {
        'final_contract': final_bid,
        'final_player':   final_player,
        'ns_hcp':         ns_hcp,
        'ns_errors':      ns_errors,
        'score':          score,
        'game_reached':   game_reached,
        'slam_reached':   slam_reached,
        'game_due':       game_due,
        'slam_due':       slam_due,
        'issues':         issues,
        'ns_auction':     ns_auction,
        'full_auction':   list(zip(auction_bids, players)),
    }


# ─── פורמט פלט ────────────────────────────────────────────────────────────────

def _hand_str(hand):
    return '  '.join(
        f'{s}{"".join(sorted([c["r"] for c in hand if c["s"] == s], key=lambda r: "AKQJT98765432".index(r))) or "-"}'
        for s in SUITS
    )


def format_analysis(analyses, summary, hands=None):
    """מחזיר מחרוזת ניתוח מעוצבת."""
    lines = ['═' * 66, 'ניתוח הכרזות לעומק', '═' * 66]

    if hands:
        for p in ('N', 'S', 'E', 'W'):
            pts = hcp(hands[p])
            lines.append(
                f'{PLAYER_HE[p]:6s} ({p}):  {_hand_str(hands[p])}  [{pts} נק\']')
        lines.append(f'נק\' N/S משולב: {summary["ns_hcp"]}')
        lines.append('')

    lines.append('רצף הכרזות:')
    lines.append('─' * 66)

    for a in analyses:
        player = a['player']
        bid    = a['bid']
        dot    = '●' if a['is_ns'] else '·'

        # סימן נכון/שגוי
        chk = ''
        if a['is_ns'] and bid != 'פס' and a.get('expected') and a['role'] != 'המתנה':
            chk = ' ✓' if a['correct'] else f' ✗  ← צפוי: {a["expected"]}'

        # מוסכמה
        conv = f'  [{a["convention"]}]' if a.get('convention') else ''

        # תפקיד
        role_str = ''
        if a.get('role') and a['role'] not in ('פס', 'הכרזה', 'E/W', 'המתנה'):
            role_str = f'  ({a["role"]})'

        lines.append(f'  {dot} {PLAYER_HE[player]:6s}: {bid:6s}{chk}{conv}{role_str}')
        if a.get('explanation'):
            lines.append(f'           {a["explanation"]}')

    lines.append('─' * 66)
    lines.append(f'חוזה סופי:   {summary["final_contract"] or "— כולם פסו"}')
    lines.append(f'נק\' N/S:     {summary["ns_hcp"]}')
    lines.append(f'שגיאות N/S:  {summary["ns_errors"]}')
    lines.append(f'ציון:        {summary["score"]}/100')

    if summary['issues']:
        lines.append('')
        lines.append('הערות חשובות:')
        for issue in summary['issues']:
            lines.append(f'  ⚠  {issue}')

    lines.append('═' * 66)
    return '\n'.join(lines)


# ─── עזרים לבדיקות ────────────────────────────────────────────────────────────

def _make_hand(spades='', hearts='', diamonds='', clubs=''):
    hand = []
    for suit, cards in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for r in cards:
            hand.append({'s': suit, 'r': r})
    return hand


# ─── בדיקות רגרסיה ────────────────────────────────────────────────────────────
#
# כל בדיקה: (שם, יד_N, יד_S, דילר, רצף_הכרזות, שגיאות_צפויות)
# שגיאות_צפויות = 0  →  רצף נכון לחלוטין
# שגיאות_צפויות = N  →  רצף עם N שגיאות (בדיקת זיהוי שגיאות)
#
# תרחישים מכוסים:
#   מיגור + תמיכה (חלש / בינוני / חזק / גיים)
#   1NT: טרנספר, סטיימן, 3NT, המשך אחרי טרנספר
#   מינור → מיגור → גיים
#   2♣ חזקה
#   פתיחה חלשה
#   סלאם: RKCB, קיו-ביד
#   זיהוי שגיאות: תמיכה שנשכחה, חוזה לא מושג, קפיצה ישירה במקום הכרזה שלב-שלב

_EWE = _make_hand('T97', '976', 'T987', '876')   # E חלש (כשN/S הם הזוג הלומד)
_EWW = _make_hand('862', '543', '654',  'T932')   # W חלש
_NSN = _make_hand('T97', '965', 'T987', '875')    # N חלש (כשE/W הם הזוג הלומד)
_NSS = _make_hand('862', '432', '654',  'T943')   # S חלש

REGRESSION_TESTS = [

    # ── מיגור + תמיכה ────────────────────────────────────────────────────────
    ('מיגור: 1♥→2♥→3♥→פס (16+6, הזמנה נדחית)',
     _make_hand('A2','AKJ54','Q432','Q2'),       # 16 HCP
     _make_hand('J54','Q76','J876','Q54'),        # 6 HCP
     'N', ['1♥','פס','2♥','פס','3♥','פס','פס','פס'], 0),

    ('מיגור: 1♥→2♥→3♥→4♥ (16+10, קבלת הזמנה)',
     _make_hand('A2','AKJ54','Q432','Q2'),        # 16 HCP
     _make_hand('J54','Q76','KJ6','Q654'),        # 10 HCP
     'N', ['1♥','פס','2♥','פס','3♥','פס','4♥','פס','פס','פס'], 0),

    ('מיגור: 1♥→3♥→4♥ (15+13, גיים ישיר)',
     _make_hand('K32','AKJ54','K32','32'),        # 15 HCP
     _make_hand('A54','Q76','Q54','KJ76'),        # 13 HCP
     'N', ['1♥','פס','3♥','פס','4♥','פס','פס','פס'], 0),

    ('מיגור: 1♠→3♠→4♠ (15+13)',
     _make_hand('AKJ54','K32','K32','32'),        # 15 HCP
     _make_hand('Q76','AJ4','Q54','QJ76'),        # 13 HCP
     'N', ['1♠','פס','3♠','פס','4♠','פס','פס','פס'], 0),

    ('מיגור: 1♥→4♥ (16+14, גיים ישיר)',
     _make_hand('A2','AKJ54','Q432','Q2'),        # 16 HCP
     _make_hand('AQ4','KQ76','J876','Q4'),        # 14 HCP, 4♥
     'N', ['1♥','פס','4♥','פס','פס','פס'], 0),

    # ── שגיאת תמיכה ───────────────────────────────────────────────────────────
    ('שגיאה: 1NT במקום 2♥ (3♥ + 6 נק\')',
     _make_hand('A2','AKJ54','Q432','Q2'),        # 16 HCP
     _make_hand('J54','Q76','J876','Q54'),        # 6 HCP, 3♥
     'N', ['1♥','פס','1NT','פס','פס','פס'], 2),  # 2 שגיאות: תשובה + rebid שטעה

    # ── 1NT + מוסכמות ─────────────────────────────────────────────────────────
    ('1NT→3NT (16+10, קפיצה ישירה)',
     _make_hand('AQ3','KJ4','Q873','KJ5'),        # 16 HCP
     _make_hand('K54','Q87','AK5','Q432'),        # 10 HCP
     'N', ['1NT','פס','3NT','פס','פס','פס'], 0),

    ('1NT→טרנספר♥→2♥→3NT→4♥ (16+14, פותח עם 3♥)',
     _make_hand('AQ3','KJ4','Q873','KJ5'),        # 16 HCP, 3♥
     _make_hand('K54','Q8732','AK5','Q4'),        # 14 HCP, 5♥
     'N', ['1NT','פס','2♦','פס','2♥','פס','3NT','פס','4♥','פס','פס','פס'], 0),

    ('1NT→טרנספר♥→2♥→פס (5♥ חלש, פותח משלים)',
     _make_hand('AQ3','KJ4','Q873','KJ5'),        # 16 HCP
     _make_hand('K54','J8732','854','Q4'),        # 7 HCP, 5♥
     'N', ['1NT','פס','2♦','פס','2♥','פס','פס','פס'], 0),

    # סטיימן דורש 2+ רביעיות (אחת מיגור): S יש 4♠+4♥
    ('1NT→סטיימן→2♥→4♥ (16+12, פיט ♥)',
     _make_hand('AQ3','KJ54','Q873','K5'),        # 16 HCP, 4♥
     _make_hand('K432','Q876','AK5','32'),        # 12 HCP, 4♠+4♥
     'N', ['1NT','פס','2♣','פס','2♥','פס','4♥','פס','פס','פס'], 0),

    ('1NT→סטיימן→2♦→3NT (16+12, אין פיט)',
     _make_hand('AQ3','KJ4','Q873','KJ5'),        # 16 HCP, אין 4-קלף במיגור
     _make_hand('K432','Q876','AK5','32'),        # 12 HCP, 4♠+4♥
     'N', ['1NT','פס','2♣','פס','2♦','פס','3NT','פס','פס','פס'], 0),

    # ── מינור → מיגור ────────────────────────────────────────────────────────
    ('1♣→1♥→1♠→4♠ (מינור, פיט ♠)',
     _make_hand('AQ32','J2','K32','KJ542'),       # 14 HCP, 4♠
     _make_hand('KJ76','AQ54','J54','32'),        # 14 HCP, 4♠+4♥
     'N', ['1♣','פס','1♥','פס','1♠','פס','4♠','פס','פס','פס'], 0),

    ('1♦→1♥→4♥ (20+14, גיים)',
     _make_hand('A32','AK2','AKJ54','32'),        # 20 HCP
     _make_hand('KQ4','QJT87','32','A54'),        # 14 HCP, 5♥
     'N', ['1♦','פס','1♥','פס','4♥','פס','פס','פס'], 0),

    ('1♣→2♦→2NT→3NT (מינור, 2-over-1)',
     _make_hand('KJ3','Q32','Q32','KJ54'),        # 14 HCP
     _make_hand('Q65','K54','AKJ76','32'),        # 13 HCP, 5♦
     'N', ['1♣','פס','2♦','פס','2NT','פס','3NT','פס','פס','פס'], 0),

    # ── 2♣ חזקה ──────────────────────────────────────────────────────────────
    # N: 23 HCP (pts>=23 → 2♣ לפני כל בדיקה אחרת)
    ('2♣→2♦→2♠→4♠ (חזקה 23 נק\' + שלילי)',
     _make_hand('AKQ54','AK2','AK2','32'),        # 23 HCP, 5♠
     _make_hand('J876','543','K54','765'),        # 4 HCP, 4♠
     'N', ['2♣','פס','2♦','פס','2♠','פס','4♠','פס','פס','פס'], 0),

    # ── פתיחה חלשה ───────────────────────────────────────────────────────────
    # דרוש: 6-9 HCP, 6+ קלפים, 5+ נק' גבוהות בסדרה
    ('2♥ חלשה→פס (8 נק\', 6♥, 6 נק\' בסדרה)',
     _make_hand('32','KQJ854','Q43','32'),        # 8 HCP, suit_hcp=6
     _make_hand('K76','32','K876','K654'),        # 9 HCP
     'N', ['2♥','פס','פס','פס'], 0),

    ('2♥ חלשה→4♥ (עם תמיכה + 16 נק\')',
     _make_hand('32','KQJ854','Q43','32'),        # 8 HCP, 6♥
     _make_hand('AK6','Q32','AK76','654'),        # 16 HCP, 3♥
     'N', ['2♥','פס','4♥','פס','פס','פס'], 0),

    # ── סלאם: קיו-ביד + RKCB ─────────────────────────────────────────────────
    # N: tp=22 (19-22 → קיו-ביד, לא RKCB ישיר)
    # S: 11 HCP, 3♥ → הזמנה 3♥; 11+ → 4NT אחרי קיו
    # RKCB: N יש 4 key cards → 5♦
    ('סלאם: 1♥→3♥→4♣(קיו)→4NT→5♦→6♥',
     _make_hand('K2','AKJ54','AQ32','A2'),        # 21 HCP, tp=22, A♣
     _make_hand('Q54','Q76','K54','KJ32'),        # 11 HCP, 3♥
     'N', ['1♥','פס','3♥','פס','4♣','פס','4NT','פס','5♦','פס','6♥','פס','פס','פס'], 0),

    # N: tp=21 (19-22 → קיו-ביד); יש A♦ → 4♦
    # S: 12 HCP, 3♠ → הזמנה 3♠; 11+ → 4NT אחרי קיו
    # RKCB: N יש 3 key cards (A♠,A♦,K♠) → 5♣
    ('סלאם: 1♠→3♠→4♦(קיו)→4NT→5♣→6♠',
     _make_hand('AKJ54','2','AK2','K432'),        # 18 HCP, 5-1-3-4 לא מאוזן, A♦ לקיו, 3 KC
     _make_hand('Q76','A54','Q54','KJ43'),        # 12 HCP, 3♠
     'N', ['1♠','פס','3♠','פס','4♦','פס','4NT','פס','5♣','פס','6♠','פס','פס','פס'], 0),

    # ── תיקוני מינור (באגים שנמצאו בשימוש) ──────────────────────────────────
    # באג: משיב עם 13+ נק' ו-5♦ הכריז 2♦ במקום 3NT
    ('מינור: 1♦→3NT (13+13, משיב 5♦ מאוזן)',
     _make_hand('K32','K32','AJ75','K43'),        # 14 HCP, מאוזן → 1♦
     _make_hand('AJ4','Q54','KQ932','J7'),         # 13 HCP, 5♦ מאוזן → 3NT
     'N', ['1♦','פס','3NT','פס','פס','פס'], 0),

    # באג: פותח 1♦ עם 5♣ הכריז 1NT במקום 2♣ אחרי תשובת 1♠
    ('מינור: 1♦→1♠→2♣→3NT (יד דו-צבעית)',
     _make_hand('8','2','AQT532','KQJ98'),         # 12 HCP, 6♦+5♣ → 1♦, rebid 2♣
     _make_hand('QJ43','KQ3','K4','A532'),          # 15 HCP, 4♠ → 1♠, אח"כ 3NT
     'N', ['1♦','פס','1♠','פס','2♣','פס','3NT','פס','פס','פס'], 0),

    # ── שגיאה: לא הגיע לגיים ─────────────────────────────────────────────────
    # N: 18 HCP לא מאוזן (2-5-4-2) → פותח 1♥; אחרי 2♥ צריך rebid 3♥ (pts>=16)
    ('שגיאה: עצרו ב-2♥ עם 26 נק\'',
     _make_hand('A2','AKJ54','QJ32','K2'),        # 18 HCP, לא מאוזן
     _make_hand('J54','Q76','K876','Q54'),        # 8 HCP
     'N', ['1♥','פס','2♥','פס','פס','פס'], 1),   # שגיאה: פס במקום 3♥

    # ── תגובה לפתיחה חלשה: 1.5 QT (10 HCP) → פס ─────────────────────────────
    # יד 385: S עם 1.5 QT (A♠ + K♦) → פס (צריך 3+ QT ל-3M, 4+ QT + 15 נק' ל-4M)
    ('פתיחה חלשה 2♥: 1.5 QT → פס (לא 3♥/4♥)',
     _make_hand('54','AK9843','J6','T82'),          # 8 HCP, 6 לב → 2♥ חלשה
     _make_hand('A9','J72','KT843','Q75'),           # 10 HCP, 1.5 QT → פס
     'N', ['2♥','פס','פס','פס'], 0),

    # ── תגובה לפתיחה חלשה: 3 QT (13 HCP) → 3M ───────────────────────────────
    # AK♠(2QT) + KQ♦(1QT) = 3 QT → 3♥
    ('פתיחה חלשה 2♥: 3 QT → 3♥',
     _make_hand('54','AK9843','J6','T82'),          # 8 HCP, 6 לב → 2♥ חלשה
     _make_hand('AK7','J72','KQ3','754'),            # 13 HCP, 3 QT → 3♥
     'N', ['2♥','פס','3♥','פס','פס','פס'], 0),

    # ── תגובה לפתיחה חלשה: 15+ HCP + 3 תמיכה → 4M ─────────────────────────
    ('פתיחה חלשה 2♠: 15 HCP + 3 תמיכה → 4♠',
     _make_hand('AJ9854','32','K76','54'),          # 10 HCP, 6 ספייד → 2♠ חלשה
     _make_hand('KQ7','AK5','AJ3','9632'),          # 16 HCP, 3 ספייד
     'N', ['2♠','פס','4♠','פס','פס','פס'], 0),

    # ── E/W כזוג הלומד — בדיקות dealer=E / dealer=W ──────────────────────────
    # פורמט: (שם, {'N':יד,'E':יד,'S':יד,'W':יד}, דילר, אוקציה, שגיאות_צפויות)

    ('E/W: מזרח פותח 1♥→W תומך 2♥→E מזמין 3♥→W עונה פס (16+6)',
     {'N': _NSN,
      'E': _make_hand('A2','AKJ54','Q432','Q2'),    # 16 HCP
      'S': _NSS,
      'W': _make_hand('J54','Q76','J876','Q54')},   # 6 HCP
     'E', ['1♥','פס','2♥','פס','3♥','פס','פס','פס'], 0),

    ('E/W: מזרח פותח 1NT→W טרנספר ♥→E משלים→W פס (16+7, חלש)',
     {'N': _NSN,
      'E': _make_hand('AQ3','KJ4','Q873','KJ5'),    # 16 HCP
      'S': _NSS,
      'W': _make_hand('K54','J8732','854','Q4')},    # 7 HCP, 5♥
     'E', ['1NT','פס','2♦','פס','2♥','פס','פס','פס'], 0),

    ('E/W: מערב פותח 1♠→E תומך 3♠→W גיים ישיר 4♠ (15+13)',
     {'N': _NSN,
      'E': _make_hand('Q76','AJ4','Q54','QJ76'),    # 13 HCP
      'S': _NSS,
      'W': _make_hand('AKJ54','K32','K32','32')},   # 15 HCP
     'W', ['1♠','פס','3♠','פס','4♠','פס','פס','פס'], 0),

    # ── 2♣ חזקה — החריג היחיד לכפייה לגיים ───────────────────────────────────
    # 2♣→2♦ שלילי→2NT (23-24 מאוזן) מול 0-2 נק' = פס.
    # לפני התיקון המשיב הכריז 3NT, הפותח קרא בזה ערכים והמשיך ל-6NT.
    ('2♣: 2♣→2♦→2NT→פס (23+0, אין גיים — הפס היחיד אחרי 2♣)',
     {'N': _make_hand('AKQ4','AK3','K54','A32'),    # 23 HCP, מאוזן
      'E': _make_hand('J986','QJT','QJT9','QJ'),
      'S': _make_hand('75','98764','3','98765'),    # 0 HCP
      'W': _make_hand('T32','52','A8762','KT4')},
     'N', ['2♣','פס','2♦','פס','2NT','פס','פס','פס'], 0),

    # ── סטיימן אחרי 2♣ (כלל יצחק: 2♣→2♦→2NT→3♣ סטיימן) ──────────────────────
    ('2♣: 2♣→2♦→2NT→3♣ סטיימן→3♠→4♠ (23+3, fit 4-4 ב-♠)',
     {'N': _make_hand('AKQ4','AK3','K54','A32'),    # 23 HCP, 4 ספיידים
      'E': _make_hand('T98','J97','AQJ','KQJT'),
      'S': _make_hand('J765','Q84','T98','976'),    # 3 HCP, 4 ספיידים
      'W': _make_hand('32','T652','7632','854')},
     'N', ['2♣','פס','2♦','פס','2NT','פס','3♣','פס',
           '3♠','פס','4♠','פס','פס','פס'], 0),

    # המשיב מוגבל ל-0-6 אחרי 2♦ שלילי, ו-2NT מראה 23-24. מקסימום 30 —
    # אין סלאם. לפני התיקון הפותח קפץ ל-6NT דרך הכלל הגנרי (resp2=='3NT').
    ('2♣: 2♣→2♦→2NT→3NT→פס (23+3, אין מיגור רביעייה — גיים ותו לא)',
     {'N': _make_hand('AKQ4','AK3','K54','A32'),    # 23 HCP
      'E': _make_hand('T98','J97','AQJ','KQJT'),
      'S': _make_hand('J76','Q84','T987','976'),    # 3 HCP, אין רביעייה במיגור
      'W': _make_hand('532','T652','632','854')},
     'N', ['2♣','פס','2♦','פס','2NT','פס','3NT','פס','פס','פס'], 0),

    # ── 4NT כמותי דורש יד מאוזנת ──────────────────────────────────────────────
    # לפני התיקון מערב הכריז 4NT כמותי עם חוסר בהרט — ועוד בסדרה שמזרח בדיוק
    # הראה — ומזרח פסס עם 14. 33 נק' והסלאם הוחמץ. עכשיו מערב מתאר 2♠.
    ('1♠: 1♠→2♥→2♠→3NT→6NT (19+14, מערב עם חוסר לא מכריז 4NT כמותי)',
     {'W': _make_hand('AKQT8','','AQ42','KJ63'),    # 19 HCP, חוסר ב-♥
      'N': _make_hand('7','KT854','JT7','8542'),
      'E': _make_hand('95','AJ632','K6','AQT7'),    # 14 HCP
      'S': _make_hand('J6432','Q97','9853','9')},
     'W', ['1♠','פס','2♥','פס','2♠','פס','3NT','פס',
           '6NT','פס','פס','פס'], 0),

    # ── פותח מינור עם 19, המשיב חוזר על סדרתו ברמה 2 → 3NT ────────────────────
    # כלל יצחק. לפני התיקון הפותח פסס עם 19 והזוג נעצר ב-2♥ עם 26 נק'.
    ('1♦: 1♦→1♥→1♠→2♥→3NT (19+7, פותח עם 19 לא פוסס)',
     {'W': _make_hand('KQJ5','A8','AQT82','K3'),    # 19 HCP, עוצרים בכל סדרה
      'N': _make_hand('87632','Q96','K','AJ76'),
      'E': _make_hand('A','K7543','9543','T42'),    # 7 HCP
      'S': _make_hand('T94','JT2','J76','Q985')},
     'W', ['1♦','פס','1♥','פס','1♠','פס','2♥','פס',
           '3NT','פס','פס','פס'], 0),

    # ── RKCB אחרי תמיכה פשוטה (כלל יצחק: עם 19 שואלים לאסים, לא סוגרים 4♥) ──
    # תמיכה פשוטה = 12-15. 19+15=34 → סלאם אפשרי, חייבים לשאול.
    # 5♠ = 2 קלפי מפתח + מלכת השליט. יחד 4 מתוך 5 (חסר ♦A) → 6♥.
    ('1♦: 1♦→1♥→2♥→4NT→5♠→6♥ (19+14, RKCB אחרי תמיכה פשוטה)',
     {'W': _make_hand('AT4','Q984','Q765','AQ'),    # 14 HCP, תמיכה 4 ב-♥
      'N': _make_hand('J932','32','AT9','8542'),
      'E': _make_hand('KQ','AK76','KJ4','KT73'),    # 19 HCP
      'S': _make_hand('8765','JT5','832','J96')},
     'W', ['1♦','פס','1♥','פס','2♥','פס','4NT','פס',
           '5♠','פס','6♥','פס','פס','פס'], 0),

    # ── 4NT כמותי אחרי 1מינור→3NT (כלל יצחק: 12-13 פס, 14+ → 6NT) ────────────
    # 18 מאוזן אין לו פתיחה שמתארת אותו (1NT=15-17), אז הוא נכנס ב-1♣.
    # לפני התיקון הוא פסס על 3NT עם 18 והזוג פספס סלם ב-33.
    ('1♣: 1♣→3NT→4NT→6NT (18+15, משיב מקסימום מקבל)',
     {'E': _make_hand('42','KJ82','AJ5','AKQ2'),    # 18 HCP, מאוזן
      'S': _make_hand('J8653','6','T9764','97'),
      'W': _make_hand('AKT','AT','K32','JT654'),    # 15 HCP — מקסימום
      'N': _make_hand('Q97','Q97543','Q8','83')},
     'E', ['1♣','פס','3NT','פס','4NT','פס','6NT','פס','פס','פס'], 0),
]


def _run_regression(cfg_used, verbose=False):
    """מריץ את כל בדיקות הרגרסיה. מחזיר (עברו, נכשלו)."""
    passed = failed = 0
    for entry in REGRESSION_TESTS:
        if isinstance(entry[1], dict):
            # פורמט חדש: (שם, hands_dict, דילר, אוקציה, שגיאות_צפויות)
            name, hands, dealer, auction_bids, exp_err = entry
        else:
            # פורמט ישן: (שם, יד_N, יד_S, דילר, אוקציה, שגיאות_צפויות)
            name, n_hand, s_hand, dealer, auction_bids, exp_err = entry
            hands = {'N': n_hand, 'S': s_hand, 'E': _EWE, 'W': _EWW}
        try:
            analyses, summary = analyze_auction(hands, dealer, auction_bids, cfg_used)
            actual = summary['ns_errors']
            ok     = (actual == exp_err)
        except Exception as e:
            print(f'  [ERROR] {name}: {e}')
            failed += 1
            continue

        if ok:
            passed += 1
            print(f'  [OK]   {name}')
        else:
            failed += 1
            print(f'  [FAIL] {name}')
            print(f'         שגיאות: {actual}  (צפוי: {exp_err})')
            if verbose:
                print(format_analysis(analyses, summary, hands))

    return passed, failed


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, '.')
    from bridge_teacher import cfg as _cfg
    cfg_demo = dict(_cfg)
    cfg_demo.update({'majorLen': 5, 'ntMin': 15, 'ntMax': 17, 'minorLen': 3})

    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print('=' * 66)
    print(f'בדיקות רגרסיה — מנוע ניתוח הכרזות ({len(REGRESSION_TESTS)} בדיקות)')
    print('=' * 66)

    passed, failed = _run_regression(cfg_demo, verbose=verbose)

    print()
    print('=' * 66)
    if failed == 0:
        print(f'כל {passed} הבדיקות עברו בהצלחה!')
    else:
        print(f'{passed}/{passed+failed} עברו — {failed} נכשלו.')
    print('=' * 66)

    sys.exit(0 if failed == 0 else 1)
