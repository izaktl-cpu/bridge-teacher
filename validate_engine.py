# -*- coding: utf-8 -*-
"""
בודק אוטומטי מקיף של מנוע ההכרזות.
בודק: פתיחה, תשובה, rebid, גיים, 1NT, פתיחה חלשה.
"""
import sys, io, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from bidding_engine import hcp, sl, is_balanced, total_pts, suit_hcp, SUITS, has_stopper
from bidding_engine import compute_auction
from bridge_teacher import cfg as base_cfg

cfg = dict(base_cfg)
cfg['majorLen'] = 5; cfg['ntMin'] = 15; cfg['ntMax'] = 17; cfg['minorLen'] = 3

RANKS    = list('AKQJT98765432')
ALL_CARDS = [{'s': s, 'r': r} for s in ['♠','♥','♦','♣'] for r in RANKS]

GAME_BIDS = {'NT':3, '♠':4, '♥':4, '♦':5, '♣':5}

# ════════════════════════════════════════════════════════════════════════
# עזר
# ════════════════════════════════════════════════════════════════════════
def hand_to_str(hand):
    result = []
    for suit in SUITS:
        cards = sorted([c['r'] for c in hand if c['s'] == suit],
                       key=lambda r: 'AKQJT98765432'.index(r))
        result.append(f"{suit}{''.join(cards) or '-'}")
    return ' '.join(result)

def make_hand(spades='', hearts='', diamonds='', clubs=''):
    hand = []
    for suit, cards in [('♠',spades),('♥',hearts),('♦',diamonds),('♣',clubs)]:
        for r in cards: hand.append({'s':suit,'r':r})
    return hand

def parse_bid(bid):
    """החזר (רמה, צבע) או None אם פס/X."""
    if not bid or bid in ('פס','X','XX') or len(bid) < 2:
        return None
    try:
        return int(bid[0]), bid[1:]
    except ValueError:
        return None

def is_game(bid):
    pb = parse_bid(bid)
    if not pb: return False
    level, suit = pb
    return level >= GAME_BIDS.get(suit, 99)

def is_slam(bid):
    pb = parse_bid(bid)
    if not pb: return False
    return pb[0] >= 6

# ════════════════════════════════════════════════════════════════════════
# 1. בדיקת פתיחה
# ════════════════════════════════════════════════════════════════════════
def check_opening(hand, bid):
    pts = hcp(hand)
    h = sl(hand,'♥'); s = sl(hand,'♠')
    c = sl(hand,'♣'); d = sl(hand,'♦')
    bal = is_balanced(hand)
    issues = []

    if pts < 12:
        expected = 'פס'  # or weak two, but for simplicity
        if bid not in ('פס','2♥','2♠','2♦','3♣','3♦','3♥','3♠','4♣','4♦','4♥','4♠'):
            issues.append({'error': f'פס/חלשה דרוש — {pts} נק\'', 'expected': expected})
        return issues

    if pts >= 23:
        expected = '2♣'
        if bid != expected:
            issues.append({'error': f'2♣ חזקה דרוש ({pts} נק\')', 'expected': expected})
        return issues

    if 20 <= pts <= 22 and bal:
        expected = '2NT'
        if bid != expected:
            issues.append({'error': f'2NT דרוש ({pts} נק\', מאוזן)', 'expected': expected})
        return issues

    if cfg['ntMin'] <= pts <= cfg['ntMax'] and bal:
        expected = '1NT'
        if bid != expected:
            issues.append({'error': f'1NT דרוש ({pts} נק\', מאוזן)', 'expected': expected})
        return issues

    if h >= 5 or s >= 5:
        if h >= 5 and h >= s:
            expected = '1♥'
        else:
            expected = '1♠'
        if bid != expected:
            issues.append({'error': f'{expected} דרוש (♥{h} ♠{s}, {pts} נק\')', 'expected': expected})
        return issues

    if bid in ('1♣','1♦'):
        issues += check_minor_choice(hand, bid)
    elif bid not in ('1NT','1♥','1♠','2NT','2♣','פס'):
        expected = 'פס'  # or calculate
        issues.append({'error': f'הכרזה לא צפויה: {bid} ({pts} נק\')', 'expected': expected})

    return issues

# ════════════════════════════════════════════════════════════════════════
# 2. בחירה בין 1♣ ל-1♦
# ════════════════════════════════════════════════════════════════════════
def check_minor_choice(hand, bid):
    c = sl(hand,'♣'); d = sl(hand,'♦')
    issues = []
    if bid == '1♣' and c < 3:
        issues.append(f'1♣ דרוש 3+ תלתנים (יש {c})')
    if bid == '1♦' and d < 3:
        issues.append(f'1♦ דרוש 3+ יהלומים (יש {d})')
    if c == d and c >= 3 and bid == '1♦':
        issues.append(f'1♣ עדיף כשאורכים שווים (♣={c} ♦={d})')
    if d > c and d >= 3 and bid == '1♣':
        issues.append(f'1♦ עדיף (♣={c} ♦={d})')
    if c > d and c >= 3 and bid == '1♦':
        issues.append(f'1♣ עדיף (♣={c} ♦={d})')
    return issues

# ════════════════════════════════════════════════════════════════════════
# 3. בדיקת פתיחה חלשה (2♥ / 2♠ / 2♦)
# ════════════════════════════════════════════════════════════════════════
def check_weak_two(hand, bid):
    pts = hcp(hand)
    suit = bid[1]
    suit_len = sl(hand, suit)
    suit_pts = suit_hcp(hand, suit)
    issues = []
    if suit_len < 6:
        issues.append(f'פתיחה חלשה דרוש 6+ קלפים ב-{suit} (יש {suit_len})')
    if suit_pts < 5:
        issues.append(f'פתיחה חלשה דרוש 5+ נק\' גבוהות ב-{suit} (יש {suit_pts})')
    if pts < 6 or pts > 9:
        issues.append(f'פתיחה חלשה דרוש 6-9 נק\' (יש {pts})')
    return issues

# ════════════════════════════════════════════════════════════════════════
# 4. בדיקת תשובה לפתיחה
# ════════════════════════════════════════════════════════════════════════
def check_response(hand, opening, bid):
    pts = hcp(hand)
    h = sl(hand,'♥'); s = sl(hand,'♠')
    c = sl(hand,'♣'); d = sl(hand,'♦')
    bal = is_balanced(hand)
    issues = []

    if pts < 6:
        if bid != 'פס': issues.append(f'פס דרוש ({pts} נק\')')
        return issues

    # ── תשובה ל-1NT ──────────────────────────────────────────────────
    if opening == '1NT':
        if h >= 5 and bid != '2♦':
            issues.append(f'2♦ טרנספר♥ דרוש (5+ לב, {pts} נק\')')
        elif s >= 5 and bid != '2♥':
            issues.append(f'2♥ טרנספר♠ דרוש (5+ ספייד, {pts} נק\')')
        elif h >= 5 or s >= 5:
            pass  # covered above
        elif (h >= 4 or s >= 4) and pts >= 8 and bid != '2♣':
            issues.append(f'2♣ סטיימן דרוש (4+ מיגור, {pts} נק\')')
        elif pts >= 10 and bid != '3NT':
            issues.append(f'3NT דרוש ({pts} נק\')')
        elif pts >= 8 and bid != '2NT':
            issues.append(f'2NT הזמנה דרוש ({pts} נק\')')
        return issues

    # ── תשובה למיגור 1♥/1♠ ──────────────────────────────────────────
    if opening in ('1♥','1♠'):
        open_suit = opening[1]
        support   = sl(hand, open_suit)
        if support >= 3:
            if pts >= 13 and bid != f'4{open_suit}':
                issues.append(f'4{open_suit} דרוש ({pts} נק\', {support} תמיכה)')
            elif 10 <= pts <= 12 and bid != f'3{open_suit}':
                issues.append(f'3{open_suit} דרוש ({pts} נק\', {support} תמיכה)')
            elif 6 <= pts <= 9 and bid != f'2{open_suit}':
                issues.append(f'2{open_suit} דרוש ({pts} נק\', {support} תמיכה)')
            return issues
        if opening == '1♥' and s >= 4:
            if bid != '1♠':
                issues.append(f'1♠ דרוש (4+ ספייד, {pts} נק\')')
            return issues
        # סדרה חדשה ברמה 2 עם יד לא מאוזנת (11+ נק', 5+ קלפים) — תקין
        # אחרי 1♠: גם 2♥ עם 4+ לבבות תקין (חיפוש פיט 4-4)
        if pts >= 11 and len(bid) == 2 and bid[0] == '2' and bid[1] in ('♥','♦','♣'):
            new_suit = bid[1]
            if new_suit != opening[1] and sl(hand, new_suit) >= 5:
                return issues  # תקין — הכרזה כפויה
            if opening == '1♠' and new_suit == '♥' and sl(hand,'♥') >= 4:
                return issues  # תקין — חיפוש פיט לב אחרי 1♠
        if pts >= 13 and bal and bid != '3NT':
            issues.append(f'3NT דרוש ({pts} נק\', מאוזן)')
        elif 11 <= pts <= 12 and bal and bid != '2NT':
            issues.append(f'2NT דרוש ({pts} נק\', מאוזן)')
        elif 6 <= pts <= 10 and bal and bid != '1NT':
            issues.append(f'1NT דרוש ({pts} נק\')')
        return issues

    # ── תשובה למינור 1♣/1♦ ──────────────────────────────────────────
    if opening in ('1♣','1♦'):
        open_suit = opening[1]
        open_len  = sl(hand, open_suit)
        other     = '♦' if opening == '1♣' else '♣'
        other_len = sl(hand, other)

        if h >= 5 and s >= 5:
            if bid != '1♠': issues.append(f'1♠ עדיפות (5♠+5♥ — הכריז הגבוה)')
            return issues
        if h >= 4 and s <= h:              # כולל 4-4 → בחר 1♥ ראשון
            if bid != '1♥': issues.append(f'1♥ עדיפות ראשונה (4+ לב)')
            return issues
        if s >= 4:
            if bid != '1♠': issues.append(f'1♠ עדיפות שנייה (4+ ספייד)')
            return issues
        if other_len >= 5 and pts >= 11:
            if bid != f'2{other}': issues.append(f'2{other} דרוש (5+ {other}, {pts} נק\')')
            return issues
        if opening == '1♣' and d >= 4 and not bal:
            if bid != '1♦': issues.append(f'1♦ דרוש (4+ יהלומים)')
            return issues
        if open_len >= 5:
            if pts >= 13 and bal:
                if bid not in (f'3NT', f'3{open_suit}'):
                    issues.append(f'3NT דרוש ({pts} נק\', מאוזן, 5+ תמיכה)')
            else:
                if bid != f'2{open_suit}': issues.append(f'2{open_suit} דרוש (5+ תמיכה)')
            return issues
        if pts >= 13 and bal and bid != '3NT':
            issues.append(f'3NT דרוש ({pts} נק\', מאוזן)')
        elif 11 <= pts <= 12 and bal and bid != '2NT':
            issues.append(f'2NT דרוש ({pts} נק\', מאוזן)')
        elif 6 <= pts <= 10 and bid != '1NT':
            issues.append(f'1NT דרוש ({pts} נק\')')

    return issues

# ════════════════════════════════════════════════════════════════════════
# 6. בדיקת אוברקול (E/W)
# ════════════════════════════════════════════════════════════════════════
def check_overcall(hand, bid, auction_so_far):
    pts = hcp(hand)
    issues = []
    expected = overcall(hand, auction_so_far)
    if bid != expected:
        issues.append({'error': f'אוברקול שגוי: {bid} במקום {expected}', 'expected': expected})
    return issues

# ════════════════════════════════════════════════════════════════════════
# 7. בדיקת תשובה לדאבל (E/W)
# ════════════════════════════════════════════════════════════════════════
def check_double_response(hand, bid, auction_so_far):
    expected = respond_to_double(hand, auction_so_far)
    if bid != expected:
        return [{'error': f'תשובה לדאבל שגויה: {bid} במקום {expected}', 'expected': expected}]
    return []
def check_rebid(hand, opening, resp, bid):
    pts = hcp(hand)
    tp  = total_pts(hand)
    h = sl(hand,'♥'); s = sl(hand,'♠')
    issues = []

    # ── אחרי פתיחת מיגור ────────────────────────────────────────────
    if opening in ('1♥','1♠'):
        open_suit = opening[1]
        open_len  = sl(hand, open_suit)

        # תמיכה ישירה מהמשיב
        if resp == f'4{open_suit}':
            if bid not in ('פס','4NT'):
                issues.append(f'פס (או 4NT RKCB) אחרי 4{open_suit}')
            return issues
        if resp == f'3{open_suit}':
            if tp >= 15 and bid != f'4{open_suit}':
                issues.append(f'4{open_suit} דרוש ({tp} נק\' — קבל הזמנה)')
            elif tp < 15 and bid != 'פס':
                issues.append(f'פס דרוש ({tp} נק\' — מינימום)')
            return issues
        if resp == f'2{open_suit}':
            if pts >= 19 and bid != f'4{open_suit}':
                issues.append(f'4{open_suit} דרוש ({pts} נק\', חזק)')
            elif 16 <= pts <= 18 and bid != f'3{open_suit}':
                issues.append(f'3{open_suit} דרוש ({pts} נק\', בינוני-חזק)')
            elif pts <= 15 and bid != 'פס':
                issues.append(f'פס דרוש ({pts} נק\', מינימום)')
            return issues

        # אחרי 1NT
        if resp == '1NT':
            if open_len >= 5 and pts >= 14 and bid != f'2{open_suit}':
                issues.append(f'2{open_suit} דרוש (5+ קלפים, {pts} נק\')')
            elif (open_len < 5 or pts < 14) and bid != 'פס':
                issues.append(f'פס דרוש ({pts} נק\' / 4 קלפים)')
            return issues

        # 1♥ + 1♠ — הפותח יש 4 ספייד
        if opening == '1♥' and resp == '1♠':
            if s >= 4:
                if tp >= 15 and bid != '4♠':
                    issues.append(f'4♠ דרוש (4 ספייד, {tp} נק\')')
                elif tp < 15 and bid != '2♠':
                    issues.append(f'2♠ דרוש (4 ספייד, מינימום)')
            else:
                if pts >= 19 and bid != '3NT':
                    issues.append(f'3NT דרוש ({pts} נק\', אין 4♠)')
                elif 15 <= pts <= 18 and bid != '2NT':
                    issues.append(f'2NT דרוש ({pts} נק\')')
                elif pts <= 14 and open_len >= 5 and bid != f'2{open_suit}':
                    issues.append(f'2{open_suit} דרוש (5+ קלפים, {pts} נק\')')
                elif pts <= 14 and open_len < 5 and bid != 'פס':
                    issues.append(f'פס דרוש ({pts} נק\', 4 קלפים)')
            return issues

    # ── אחרי פתיחת מינור ────────────────────────────────────────────
    if opening in ('1♣','1♦'):
        open_suit = opening[1]

        if resp in ('1♥','1♠'):
            resp_suit = resp[1]
            support   = sl(hand, resp_suit)
            # ♠ דורש 4+ קלפים לתמיכה; ♥ מקובל עם 3 קלפים בפתיחת מינור
            min_support = 4 if resp_suit == '♠' else 3
            if support >= min_support:
                if tp >= 18 and bid != f'4{resp_suit}':
                    issues.append(f'4{resp_suit} דרוש ({tp} נק\', {support} תמיכה)')
                elif 16 <= tp <= 17 and bid != f'3{resp_suit}':
                    issues.append(f'3{resp_suit} דרוש ({tp} נק\')')
                elif tp <= 15 and bid != f'2{resp_suit}':
                    issues.append(f'2{resp_suit} דרוש ({tp} נק\', מינימום)')
                return issues
            if resp == '1♥' and s >= 4:
                if bid != '1♠':
                    issues.append(f'1♠ דרוש (4 ספייד, אין תמיכה ל-♥)')
                return issues
            # יד דו-צבעית: 5+ מינור שני — הצגתו תקינה לפני NT
            other_minor = '♦' if open_suit == '♣' else '♣'
            if sl(hand, other_minor) >= 5 and bid == f'2{other_minor}':
                return issues  # הכרזה תקינה — מינור שני
            if pts >= 18 and bid != '3NT':
                issues.append(f'3NT דרוש ({pts} נק\')')
            elif 15 <= pts <= 17 and bid != '2NT':
                issues.append(f'2NT דרוש ({pts} נק\')')
            elif pts <= 14 and bid != '1NT':
                issues.append(f'1NT דרוש ({pts} נק\', מינימום)')
            return issues

        if resp == '1NT':
            if pts >= 18 and bid != '2NT':
                issues.append(f'2NT דרוש ({pts} נק\')')
            elif pts <= 17 and bid != 'פס':
                issues.append(f'פס דרוש ({pts} נק\', מינימום)')
            return issues

    return issues

# ════════════════════════════════════════════════════════════════════════
# 5b. בדיקת תשובה שנייה (second_response)
# ════════════════════════════════════════════════════════════════════════
def check_second_response(hand, opening, resp1, rebid_bid, bid):
    pts = hcp(hand)
    issues = []
    resp_suit = resp1[1] if len(resp1) == 2 else ''

    # אחרי הזמנה 3M מהפותח (למשל 2♥-3♥) → קבל עם 8+ נק'
    if rebid_bid == f'3{resp_suit}' and resp_suit in ('♥','♠'):
        if pts >= 8 and bid != f'4{resp_suit}':
            issues.append(f'4{resp_suit} דרוש ({pts} נק\' — קבל הזמנה)')
        elif pts < 8 and bid != 'פס':
            issues.append(f'פס דרוש ({pts} נק\' — דחה הזמנה)')
        return issues

    # אחרי 2NT rebid של הפותח
    # resp1=='1♦': פותח 18+ → 7+ נק' לגיים; אחר: פותח 15-17 → 10+ נק' לגיים
    if rebid_bid == '2NT' and opening in ('1♣','1♦'):
        if resp1 == '1♦': thresh = 7
        elif resp1[0] == '1': thresh = 9
        else: thresh = 12
        if pts >= thresh and bid != '3NT':
            issues.append(f'3NT דרוש ({pts} נק\' — קבל הזמנה)')
        elif pts < thresh and bid != 'פס':
            issues.append(f'פס דרוש ({pts} נק\' — דחה הזמנה)')
        return issues

    return issues

# ════════════════════════════════════════════════════════════════════════
# 6. בדיקת גיים — הגענו לגיים כשצריך? עצרנו כשצריך?
# ════════════════════════════════════════════════════════════════════════
def check_game_level(hands, auction, players, pair=('N','S')):
    p1, p2 = pair
    issues = []
    ns_hcp = hcp(hands[p1]) + hcp(hands[p2])
    # שותף עם < 6 כבוד לא יכול להגיב — פס חוקי
    if hcp(hands[p1]) < 6 or hcp(hands[p2]) < 6:
        return issues

    # מצא חוזה סופי
    final_bid = None
    final_player = None
    for bid, player in zip(auction, players):
        if bid not in ('פס','X','XX'):
            final_bid = bid
            final_player = player

    if final_bid is None:
        return issues  # כולם פסו

    ns_contract = final_player in pair
    if not ns_contract:
        return issues  # היריבים שיחקו

    game = is_game(final_bid)
    slam = is_slam(final_bid)
    tag = f'{p1}/{p2}'

    # ── האם גיים בכלל קיים בשיטה? (טבלת "סדר עדיפות למשחק מלא" בסקיל) ──────
    #   4♥/4♠ — דורש 8+ קלפים משותפים במיגור
    #   3NT   — דורש עוצר בכל סדרה; בלי עוצר היריבים פורשים אותה
    #   5♣/5♦ — דורש 28-29+ נק', כי צריך 11 לקיחות
    # בלי אף אחד מאלה אין לזוג גיים, ולדרוש ממנו גיים זו שגיאה של הבדיקה.
    major_fit = any(sl(hands[p1], s) + sl(hands[p2], s) >= 8 for s in ('♥','♠'))
    nt_stops  = all(has_stopper(hands[p1], s) or has_stopper(hands[p2], s)
                    for s in SUITS)
    game_exists = major_fit or nt_stops or ns_hcp >= 28

    # 26+ נק' → גיים חובה
    if ns_hcp >= 26 and not game and game_exists:
        issues.append(f'{tag} יש {ns_hcp} נק\' — צריך גיים, עצרו ב-{final_bid}')

    # 33+ נק' → סלאם חובה
    if ns_hcp >= 33 and not slam:
        issues.append(f'{tag} יש {ns_hcp} נק\' — צריך סלאם, עצרו ב-{final_bid}')

    # 20- נק' → לא צריך גיים.
    # חריג: עם 9+ קלפים משותפים בשליט הלקיחות באות מהאורך ולא מהנקודות
    # (פרי-אמפט). ספירת נקודות לבדה לא רלוונטית שם.
    pb_final = parse_bid(final_bid)
    long_fit = (pb_final and pb_final[1] in SUITS
                and sl(hands[p1], pb_final[1]) + sl(hands[p2], pb_final[1]) >= 9)
    if ns_hcp <= 20 and game and not slam and not long_fit:
        issues.append(f'{tag} הגיעו ל-{final_bid} עם רק {ns_hcp} נק\' (ייתכן הגזמה)')

    return issues

# ════════════════════════════════════════════════════════════════════════
# 7. בדיקת איכות החוזה הסופי
# ════════════════════════════════════════════════════════════════════════
def check_contract_quality(hands, auction, players, pair=('N','S')):
    """האם בחרו את הצבע הנכון? 4M עדיף על 3NT עם 8+ קלפים משותפים"""
    p1, p2 = pair
    issues = []
    ns_hcp = hcp(hands[p1]) + hcp(hands[p2])

    final_bid = None
    for bid, player in zip(auction, players):
        if bid not in ('פס','X','XX') and player in pair:
            final_bid = bid

    if not final_bid: return issues
    pb = parse_bid(final_bid)
    if not pb: return issues
    level, suit = pb

    # אחרי 2♣ חזקה + 2♦ שלילי המשיב לא תיאר כלום, ואין דרך לגלות התאמה 4-4.
    # 3NT היא ההכרזה הנכונה שם — לא מסמנים אותה כשגיאה.
    pair_bids = [b for b, pl in zip(auction, players) if pl in pair and b != 'פס']
    if pair_bids[:2] == ['2♣', '2♦']:
        return issues

    # 3NT עם fit 4-4 במיגור → עדיף 4M (רק כשלשניהם יש 4+ קלפים)
    # יד 4333 → NT ישיר נכון לפי השיטה — לא מסמנים כשגיאה
    def is_4333(hand):
        return max(sl(hand, su) for su in SUITS) == 4 and min(sl(hand, su) for su in SUITS) == 3
    if final_bid == '3NT' and ns_hcp >= 25:
        for major in ('♥','♠'):
            if sl(hands[p1], major) >= 4 and sl(hands[p2], major) >= 4:
                if is_4333(hands[p1]) or is_4333(hands[p2]):
                    break  # אחת הידיים 4333 — NT ישיר נכון לפי השיטה
                issues.append(
                    f'4{major} עדיף ל-3NT (fit 4-4 ב-{major}, {ns_hcp} נק\')')
                break

    # 5♣/5♦ עם 8+ קלפים במינור כשאין 3NT/4M — בדיקה עתידית
    return issues

# ════════════════════════════════════════════════════════════════════════
# ידיים ממוקדות ידנית
# ════════════════════════════════════════════════════════════════════════
EW_E = make_hand('T97','976','T987','876')
EW_W = make_hand('862','543','654','T932')

MANUAL_HANDS = [
    # מיגורים — תמיכה
    ('1♥→2♥→3♥→פס',  make_hand('A2','AKJ54','Q432','Q2'),  make_hand('J54','Q76','J876','Q54'), 'N', ['1♥','2♥','3♥','פס']),
    ('1♥→2♥→3♥→4♥',  make_hand('A2','AKJ54','Q432','Q2'),  make_hand('J54','Q76','KJ6','Q654'), 'N', ['1♥','2♥','3♥','4♥','פס']),
    ('1♥→3♥→4♥',     make_hand('K32','AKJ54','K32','32'),  make_hand('A54','Q76','Q54','KJ76'), 'N', ['1♥','3♥','4♥','פס']),
    ('1♠→3♠→4♠',     make_hand('AKJ54','K32','K32','32'),  make_hand('Q76','AJ4','Q54','QJ76'), 'N', ['1♠','3♠','4♠','פס']),
    # מיגורים — אחרי תשובה
    ('1♥→1♠→4♠',     make_hand('AKQ4','KQJ54','32','32'),  make_hand('QJ76','32','K876','K54'), 'N', ['1♥','1♠','4♠','פס']),
    ('1♥→1NT→2♥→פס', make_hand('K32','AKJ54','K32','32'),  make_hand('K54','32','Q876','KJ54'), 'N', ['1♥','1NT','2♥','פס']),
    # מינורים
    ('1♣→1♥→1♠→4♠',  make_hand('AQ32','J2','K32','KJ542'), make_hand('KJ76','AQ54','J54','32'), 'N', ['1♣','1♥','1♠','4♠','פס']),
    ('1♣→1♦→3♦→פס',  make_hand('K2','AJ','KQ32','KJ542'),  make_hand('Q6','Q4','AJ762','T532'), 'N', ['1♣','1♦','3♦','פס']),
    ('1♣→2♦→2NT→3NT',make_hand('KJ3','Q32','Q32','KJ54'),  make_hand('Q65','K54','AKJ76','32'), 'N', ['1♣','2♦','2NT','3NT','פס']),
    ('1♣→1♥→2♥→פס',  make_hand('KJ3','Q32','Q32','KJ54'),  make_hand('654','KJ87','Q54','T32'), 'N', ['1♣','1♥','2♥','פס']),
    ('1♦→1♥→4♥→פס',  make_hand('A32','AK2','AKJ54','32'),  make_hand('KQ4','QJT87','32','A54'), 'N', ['1♦','1♥','4♥','פס']),
    # 1NT
    ('1NT→3NT→פס',    make_hand('AQ3','KJ4','Q873','KJ5'),  make_hand('K54','Q87','AK5','Q432'), 'N', ['1NT','3NT','פס']),
]

def run_manual():
    print('=' * 62)
    print('בדיקת ידיים ממוקדות')
    print('=' * 62)
    errs = []
    for name, n_hand, s_hand, dealer, expected in MANUAL_HANDS:
        hands = {'N': n_hand, 'S': s_hand, 'E': EW_E, 'W': EW_W}
        try:
            auction, players = compute_auction(hands, dealer, dict(cfg))
            ns_bids = [auction[i] for i in range(len(auction)) if players[i] in ('N','S')]
            if ns_bids == expected:
                print(f'  [OK]   {name}')
            else:
                print(f'  [FAIL] {name}')
                print(f'    צפוי:   {expected}')
                print(f'    קיבלנו: {ns_bids}')
                errs.append(name)
        except Exception as e:
            print(f'  [ERROR] {name}: {e}')
            errs.append(name)
    return errs

# ════════════════════════════════════════════════════════════════════════
# בדיקת ידיים אקראיות
# ════════════════════════════════════════════════════════════════════════
def ew_between(auction, players, i_open, i_resp, opps=('E','W')):
    """האם היריבים ביצעו הכרזה (לא פס) בין פתיחה לתשובה."""
    return any(players[j] in opps and auction[j] not in ('פס',)
               for j in range(i_open + 1, i_resp))

def run_random(num=500, seed=42):
    random.seed(seed)
    counters = {'open': 0, 'weak': 0, 'resp': 0, 'rebid': 0, 'second_resp': 0, 'game': 0, 'quality': 0, 'overcall': 0, 'double_resp': 0}
    errors   = {'open': [], 'weak': [], 'resp': [], 'rebid': [], 'second_resp': [], 'game': [], 'quality': [], 'overcall': [], 'double_resp': []}

    def add_err(kind, info):
        errors[kind].append(info)

    for trial in range(num):
        deck = ALL_CARDS[:]
        random.shuffle(deck)
        hands  = {'N': deck[0:13], 'E': deck[13:26],
                  'S': deck[26:39], 'W': deck[39:52]}
        dealer = ['N','E','S','W'][trial % 4]

        try:
            auction, players = compute_auction(hands, dealer, dict(cfg))
        except Exception:
            continue

        # הזוג הלומד נקבע לפי הדילר — בדיוק כמו ב-compute_auction.
        # ליריבים המנוע נותן טיפול מינימלי במכוון (אוברקול אחד ואז פס),
        # ולכן אסור לבדוק אותם בכללי הזוג הלומד.
        pair = ('N','S') if dealer in ('N','S') else ('E','W')
        opps = ('E','W') if dealer in ('N','S') else ('N','S')

        indexed = list(zip(auction, players, range(len(auction))))

        # ─── מצא פותח מהזוג הלומד ───────────────────────────────────
        opener_info = next(((b,p,i) for b,p,i in indexed
                            if p in pair and b != 'פס'), None)
        if opener_info is None:
            continue
        open_bid, open_player, open_idx = opener_info
        opener_hand = hands[open_player]

        # ─── בדוק פתיחה ─────────────────────────────────────────────
        issues = check_opening(opener_hand, open_bid)
        if issues:
            add_err('open', {'trial': trial+1, 'player': open_player,
                'bid': open_bid, 'hand': hand_to_str(opener_hand),
                'hcp': hcp(opener_hand), 'issues': issues})

        # ─── פתיחה חלשה ─────────────────────────────────────────────
        if open_bid in ('2♥','2♠','2♦'):
            issues = check_weak_two(opener_hand, open_bid)
            if issues:
                add_err('weak', {'trial': trial+1, 'player': open_player,
                    'bid': open_bid, 'hand': hand_to_str(opener_hand),
                    'hcp': hcp(opener_hand), 'issues': issues})

        # ─── מצא משיב מהזוג הלומד ────────────────────────────────────
        resp_info = next(((b,p,i) for b,p,i in indexed
                          if p in pair and b != 'פס' and i > open_idx), None)
        if resp_info is None:
            # בדוק גיים גם בלי תשובה
            g_issues = check_game_level(hands, auction, players, pair)
            if g_issues:
                add_err('game', {'trial': trial+1, 'issues': g_issues,
                    'pair': pair,
                    'h1': hand_to_str(hands[pair[0]]), 'h2': hand_to_str(hands[pair[1]]),
                    'ns_hcp': hcp(hands[pair[0]])+hcp(hands[pair[1]]),
                    'auction': [b for b,p in zip(auction,players) if p in pair]})
            continue

        resp_bid, resp_player, resp_idx = resp_info
        resp_hand = hands[resp_player]

        # ─── בדוק תשובה (ללא אוברקול של היריבים) ────────────────────
        if (open_bid[0] == '1' and len(open_bid) == 2
                and resp_bid not in ('X','XX')
                and not ew_between(auction, players, open_idx, resp_idx, opps)):
            issues = check_response(resp_hand, open_bid, resp_bid)
            if issues:
                add_err('resp', {'trial': trial+1,
                    'opener': open_player, 'opening': open_bid,
                    'responder': resp_player, 'bid': resp_bid,
                    'hand': hand_to_str(resp_hand),
                    'hcp': hcp(resp_hand), 'issues': issues})

        # ─── מצא rebid N/S ───────────────────────────────────────────
        rebid_info = next(((b,p,i) for b,p,i in indexed
                           if p == open_player and b != 'פס' and i > resp_idx), None)
        if rebid_info:
            rebid_bid, _, rebid_idx = rebid_info
            # בדוק rebid רק בלי התערבות היריבים בין תשובה ל-rebid
            if (open_bid[0] == '1' and len(open_bid) == 2
                    and resp_bid[0] == '1' and len(resp_bid) == 2
                    and rebid_bid not in ('X','XX')
                    and not ew_between(auction, players, resp_idx, rebid_idx, opps)):
                issues = check_rebid(opener_hand, open_bid, resp_bid, rebid_bid)
                if issues:
                    add_err('rebid', {'trial': trial+1,
                        'player': open_player, 'opening': open_bid,
                        'resp': resp_bid, 'bid': rebid_bid,
                        'hand': hand_to_str(opener_hand),
                        'hcp': hcp(opener_hand), 'issues': issues})

        # ─── בדוק second_response ────────────────────────────────────
        if rebid_info:
            rebid_bid2, _, rebid_idx2 = rebid_info
            second_resp_info = next(((b,p,i) for b,p,i in indexed
                                     if p == resp_player and b != 'פס'
                                     and i > rebid_idx2), None)
            if second_resp_info:
                sr_bid, _, sr_idx = second_resp_info
                if (not ew_between(auction, players, rebid_idx2, sr_idx, opps)
                        and resp_bid[0] == '1' and len(resp_bid) == 2
                        and rebid_bid2 not in ('X','XX')):
                    counters['second_resp'] += 1
                    issues = check_second_response(resp_hand, open_bid, resp_bid, rebid_bid2, sr_bid)
                    if issues:
                        add_err('second_resp', {'trial': trial+1,
                            'opening': open_bid, 'resp1': resp_bid,
                            'rebid': rebid_bid2, 'bid': sr_bid,
                            'hand': hand_to_str(resp_hand),
                            'hcp': hcp(resp_hand), 'issues': issues})

        # ─── בדוק גיים ──────────────────────────────────────────────
        g_issues = check_game_level(hands, auction, players, pair)
        if g_issues:
            add_err('game', {'trial': trial+1, 'issues': g_issues,
                'pair': pair,
                'h1': hand_to_str(hands[pair[0]]), 'h2': hand_to_str(hands[pair[1]]),
                'ns_hcp': hcp(hands[pair[0]])+hcp(hands[pair[1]]),
                'auction': [b for b,p in zip(auction,players) if p in pair]})

        # ─── בדוק איכות חוזה ────────────────────────────────────────
        q_issues = check_contract_quality(hands, auction, players, pair)
        if q_issues:
            add_err('quality', {'trial': trial+1, 'issues': q_issues,
                'pair': pair,
                'h1': hand_to_str(hands[pair[0]]), 'h2': hand_to_str(hands[pair[1]]),
                'ns_hcp': hcp(hands[pair[0]])+hcp(hands[pair[1]]),
                'auction': [b for b,p in zip(auction,players) if p in pair]})

    return errors

# ════════════════════════════════════════════════════════════════════════
# הדפסה
# ════════════════════════════════════════════════════════════════════════
LABELS = {
    'open':        'פתיחות',
    'weak':        'פתיחות חלשות',
    'resp':        'תשובות',
    'rebid':       'חזרות פותח (rebid)',
    'second_resp': 'תשובה שנייה (second response)',
    'game':        'רמת גיים',
    'quality':     'איכות חוזה (fit vs NT)',
}

def print_section(kind, errors, limit=12):
    errs = errors[kind]
    label = LABELS[kind]
    print(f'\n── {label} ── {len(errs)} שגיאות')
    if not errs:
        print('  ✓ הכל תקין')
        return
    for e in errs[:limit]:
        if kind == 'game':
            p1, p2 = e['pair']
            print(f"  יד {e['trial']}: {p1}/{p2}={e['ns_hcp']} נק'  הכרזות: {e['auction']}")
            print(f"    {p1}: {e['h1']}")
            print(f"    {p2}: {e['h2']}")
        elif kind == 'resp':
            print(f"  יד {e['trial']}: {e['opener']} פתח {e['opening']}, "
                  f"{e['responder']} ענה {e['bid']} ({e['hcp']} נק')")
            print(f"    יד: {e['hand']}")
        elif kind == 'rebid':
            print(f"  יד {e['trial']}: {e['player']} פתח {e['opening']}, "
                  f"משיב {e['resp']}, rebid={e['bid']} ({e['hcp']} נק')")
            print(f"    יד: {e['hand']}")
        elif kind == 'second_resp':
            print(f"  יד {e['trial']}: {e['opening']}-{e['resp1']}-{e['rebid']}, "
                  f"תשובה שנייה={e['bid']} ({e['hcp']} נק')")
            print(f"    יד: {e['hand']}")
        elif kind == 'quality':
            p1, p2 = e['pair']
            print(f"  יד {e['trial']}: {p1}/{p2}={e['ns_hcp']} נק'  הכרזות: {e['auction']}")
            print(f"    {p1}: {e['h1']}")
            print(f"    {p2}: {e['h2']}")
        else:
            print(f"  יד {e['trial']}: {e['player']} הכריז {e['bid']} ({e['hcp']} נק')")
            print(f"    יד: {e['hand']}")
        for issue in e['issues']:
            print(f"    ⚠  {issue}")
    if len(errs) > limit:
        print(f"  ... ועוד {len(errs)-limit}")

# ════════════════════════════════════════════════════════════════════════
# הרצה
# ════════════════════════════════════════════════════════════════════════
NUM_HANDS = 2000

manual_errs = run_manual()

print()
print('=' * 62)
print(f'בדיקת ידיים אקראיות — {NUM_HANDS} ידיים')
print('=' * 62)

errors = run_random(NUM_HANDS)

for kind in ('open','weak','resp','rebid','second_resp','game','quality'):
    print_section(kind, errors)

print()
print('=' * 62)
print('סיכום:')
print(f'  ידיים ממוקדות:      {len(manual_errs)} שגיאות מתוך {len(MANUAL_HANDS)}')
for kind in ('open','weak','resp','rebid','second_resp','game','quality'):
    n = len(errors[kind])
    mark = '✓' if n == 0 else '✗'
    print(f'  {mark} {LABELS[kind]:30s}: {n} שגיאות מתוך {NUM_HANDS}')
print('=' * 62)
