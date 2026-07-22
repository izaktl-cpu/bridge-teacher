import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import webbrowser
import tempfile
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Constants ──────────────────────────────────────────────────────────────────
SUITS  = ['♠','♥','♦','♣']
RANKS  = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']
HCP_VAL = {'A':4,'K':3,'Q':2,'J':1}
SUIT_CLS = {'♠':'sp','♥':'he','♦':'di','♣':'cl'}
PARTNER  = {'N':'S','S':'N','E':'W','W':'E'}
NAMES    = {'N':'צפון (N)','E':'מזרח (E)','S':'דרום (S)','W':'מערב (W)'}

MAX_TRIES = 200000
_WS_MODE = False   # דגל מצב דף-עבודה: מפעיל פילטרים נוספים (תמיכה≤2 מול NT, תקרת 6, בלי סינגלטון K/Q). לא חל על פנלים ידניים.

STRENGTH_OPENER     = {'חלש 12-14':(12,14),'בינוני 15-17':(15,17),'חזק 18-21':(18,21)}
STRENGTH_RESP       = {'פס 0-5':(0,5),'חלש 6-9':(6,9),'בינוני 10-12':(10,12),'חזק 13+':(13,16)}
STRENGTH_RESP_NT    = {'חלש 0-7':(0,7),'בינוני 8-9':(8,9),'חזק 10+':(10,15),
                       'הזמנת סלאם 16-17':(16,17),'ג׳רבר 18+':(18,22)}
STRENGTH_RESP_MINOR = {'חלש 6-10':(6,10),'בינוני 11-12':(11,12),'חזק 13+':(13,16)}

# ── Config ─────────────────────────────────────────────────────────────────────
cfg = {'majorLen':5,'ntMin':15,'ntMax':17,'minorLen':3}

# ── Lesson definitions ─────────────────────────────────────────────────────────
# (label, n_open_key, n_suit, n_strength_key, s_strength, s_resp_type, s_resp_suit)
LESSON_GROUPS = [
    ('1NT', [
        ('פס',              'nt', None, None, 'חלש 0-7',         None,      None),
        ('סטיימן גיים',    'nt', None, None, 'חזק 10+',         'stayman', '♥'),
        ('סטיימן הזמנה',  'nt', None, None, 'בינוני 8-9',      'stayman', '♥'),
        ('טרנספר ♥',      'nt', None, None, 'חלש 0-7',         'trans-h', '♥'),
        ('טרנספר ♠',      'nt', None, None, 'חלש 0-7',         'trans-s', '♠'),
        ('3NT',             'nt', None, None, 'חזק 10+',         '2nt',     None),
    ]),
    ('מיגורים', [
        ('1♥→2♥',  'major','♥', None,         'חלש 6-9',     'support','♥'),
        ('1♥→3♥',  'major','♥', None,         'בינוני 10-12','support','♥'),
        ('1♥→4♥',  'major','♥', None,         'חזק 13+',     'support','♥'),
        ('1♥→1NT', 'major','♥', None,         'חלש 6-9',     '1nt',    None),
        ('1♥→2NT', 'major','♥', None,         'בינוני 10-12','2nt',    None),
        ('1♥→3NT', 'major','♥', None,         'חזק 13+',     '2nt',    None),
        ('1♠→2♠',  'major','♠', None,         'חלש 6-9',     'support','♠'),
        ('1♠→3♠',  'major','♠', None,         'בינוני 10-12','support','♠'),
        ('1♠→4♠',  'major','♠', None,         'חזק 13+',     'support','♠'),
        ('1♠→1NT', 'major','♠', None,         'חלש 6-9',     '1nt',    None),
        ('1♠→2NT', 'major','♠', None,         'בינוני 10-12','2nt',    None),
        ('1♠→3NT', 'major','♠', None,         'חזק 13+',     '2nt',    None),
    ]),
    ('מינורים', [
        ('1♣→1♥',  'minor','♣', None, 'חלש 6-10',    '1h',  '♥'),
        ('1♣→1♠',  'minor','♣', None, 'חלש 6-10',    '1s',  '♠'),
        ('1♣→1NT', 'minor','♣', None, 'חלש 6-10',    '1nt', None),
        ('1♣→2NT', 'minor','♣', None, 'בינוני 11-12','2nt', None),
        ('1♣→3NT', 'minor','♣', None, 'חזק 13+',     '2nt', None),
        ('1♦→1♥',  'minor','♦', None, 'חלש 6-10',    '1h',  '♥'),
        ('1♦→1♠',  'minor','♦', None, 'חלש 6-10',    '1s',  '♠'),
        ('1♦→1NT', 'minor','♦', None, 'חלש 6-10',    '1nt', None),
        ('1♦→2NT', 'minor','♦', None, 'בינוני 11-12','2nt', None),
        ('1♦→3NT', 'minor','♦', None, 'חזק 13+',     '2nt', None),
    ]),
    ('סלאם', [
        ('1NT→4♣ ג׳רבר', 'nt',   None, None,         'ג׳רבר 18+',        '2nt',     None),
        ('1NT→4NT',       'nt',   None, None,         'הזמנת סלאם 16-17', '2nt',     None),
        ('1♥→4♥ RKCB',  'major', '♥',  'חזק 18-21', 'חזק 13+',           'support', '♥'),
        ('1♠→4♠ RKCB',  'major', '♠',  'חזק 18-21', 'חזק 13+',           'support', '♠'),
    ]),
    ('פתיחות 2 חלשות', [
        ('2♥ → פס',  'weak2', '♥', None, 'חלש 6-9',     None,      None),
        ('2♥ → 4♥',  'weak2', '♥', None, 'בינוני 10-12','support', '♥'),
        ('2♠ → פס',  'weak2', '♠', None, 'חלש 6-9',     None,      None),
        ('2♠ → 4♠',  'weak2', '♠', None, 'בינוני 10-12','support', '♠'),
    ]),
    ('2♣ חזקה', [
        ('2♣ → 2♦ שלילי', '2club', None, None, None,       None,  None),
        ('2♣ → 2♥ חיובי', '2club', None, None, 'בינוני 10-12', '1h',  '♥'),
        ('2♣ → 2♠ חיובי', '2club', None, None, 'בינוני 10-12', '1s',  '♠'),
    ]),
    ('2NT (20-22)', [
        ('2NT → 3NT',       '2nt_op', None, None, 'בינוני 10-12', '2nt',     None),
        ('2NT → סטיימן',   '2nt_op', None, None, 'בינוני 10-12', 'stayman', '♥'),
        ('2NT → טרנספר ♥', '2nt_op', None, None, 'חלש 6-9',      'trans-h', '♥'),
        ('2NT → טרנספר ♠', '2nt_op', None, None, 'חלש 6-9',      'trans-s', '♠'),
    ]),
]

# ── Worksheet panel (new design) ────────────────────────────────────────────────
# מבנה טור-אחד לפי הסדר שסוכם עם יצחק. כל כפתור מחזיק *רשימת תרחישים* בכוחות
# מעורבים (טאפל = כמו LESSON_GROUPS בלי label). לחיצה מחוללת N לוחות שמתפרשים
# על התרחישים (התלמיד מחליט). כותרת = ('h', title); כפתור = ('b', labelspec, scenarios)
# כאשר labelspec הוא מחרוזת או ('split', heb, latin) (latin נעוץ שמאלה).
_NAT_NT   = [('nt',None,None,'חלש 0-7',None,None),
             ('nt',None,None,'בינוני 8-9','2nt',None),
             ('nt',None,None,'חזק 10+','2nt',None)]
_STAYMAN  = [('nt',None,None,'בינוני 8-9','stayman','♥'),
             ('nt',None,None,'בינוני 8-9','stayman','♠'),
             ('nt',None,None,'חזק 10+','stayman','♥'),
             ('nt',None,None,'חזק 10+','stayman','♠')]
_TRANSFER = [('nt',None,None,'חלש 0-7','trans-h','♥'),
             ('nt',None,None,'חלש 0-7','trans-s','♠'),
             ('nt',None,None,'בינוני 8-9','trans-h','♥'),
             ('nt',None,None,'בינוני 8-9','trans-s','♠'),
             ('nt',None,None,'חזק 10+','trans-h','♥'),
             ('nt',None,None,'חזק 10+','trans-s','♠')]
_2NT_ALL  = [('2nt_op',None,None,'בינוני 10-12','2nt',None),
             ('2nt_op',None,None,'בינוני 10-12','stayman','♥'),
             ('2nt_op',None,None,'חלש 6-9','trans-h','♥'),
             ('2nt_op',None,None,'חלש 6-9','trans-s','♠')]
_MAJ_SUPP = [('major',None,None,'פס 0-5',None,None),
             ('major',None,None,'חלש 6-9','support',None),
             ('major',None,None,'בינוני 10-12','support',None),
             ('major',None,None,'חזק 13+','support',None)]
_MAJ_NT   = [('major',None,None,'חלש 6-9','1nt',None),
             ('major',None,None,'בינוני 10-12','2nt',None),
             ('major',None,None,'חזק 13+','2nt',None)]
_MIN_MAJ  = [('minor',None,None,'חלש 6-10','1h','♥'),
             ('minor',None,None,'חלש 6-10','1s','♠')]
_MIN_NT   = [('minor',None,None,'חלש 6-10','1nt',None),
             ('minor',None,None,'בינוני 11-12','2nt',None),
             ('minor',None,None,'חזק 13+','2nt',None)]
_MIN_SUPP = [('minor',None,None,'חלש 6-10','supp-minor',None),
             ('minor',None,None,'בינוני 11-12','supp-minor',None)]
_SLAM_SUIT= [('major','♥','חזק 18-21','חזק 13+','support','♥'),
             ('major','♠','חזק 18-21','חזק 13+','support','♠')]
_SLAM_NT  = [('nt',None,None,'הזמנת סלאם 16-17','2nt',None),
             ('nt',None,None,'ג׳רבר 18+','2nt',None)]
_2CLUB    = [('2club',None,None,None,None,None),
             ('2club',None,None,'בינוני 10-12','1h','♥'),
             ('2club',None,None,'בינוני 10-12','1s','♠')]
_WEAK2    = [('weak2','♥',None,'חלש 6-9',None,None),
             ('weak2','♥',None,'בינוני 10-12','support','♥'),
             ('weak2','♠',None,'חלש 6-9',None,None),
             ('weak2','♠',None,'בינוני 10-12','support','♠')]

_NT_SPLIT = ('split', 'תשובות ב', 'NT')
WORKSHEET_PANEL = [
    ('h', '1NT'),
    ('b', _NT_SPLIT,   _NAT_NT),
    ('b', 'סטיימן',    _STAYMAN),
    ('b', 'טרנספר',    _TRANSFER),
    ('h', '2NT'),
    ('b', 'כל התשובות', _2NT_ALL),
    ('h', 'מיגורים'),
    ('b', 'תמיכה במיגור', _MAJ_SUPP),
    ('b', _NT_SPLIT,      _MAJ_NT),
    ('h', 'מינורים'),
    ('b', 'תשובות במיגור', _MIN_MAJ),
    ('b', _NT_SPLIT,       _MIN_NT),
    ('b', 'תמיכה במינור',  _MIN_SUPP),
    ('h', 'סלאם'),
    ('b', 'סלאם בצבע',        _SLAM_SUIT),
    ('b', ('split','סלאם ב','NT'), _SLAM_NT),
    ('h', '2♣ חזקה'),
    ('b', 'כל התשובות', _2CLUB),
    ('h', 'פתיחות חלשות'),
    ('b', 'כל התשובות', _WEAK2),
]

# ── Player state ───────────────────────────────────────────────────────────────
def init_state():
    return dict(mode='free', hcpMin=0, hcpMax=37, type='free', commands='',
                strengthKey=None, openKey=None, openSuit=None, openType=None,
                respStrength=None, respType=None, respSuit=None)

pState = {p: init_state() for p in 'NESW'}

# ── Hand engine ────────────────────────────────────────────────────────────────
def create_deck():
    return [{'s':s,'r':r} for s in SUITS for r in RANKS]

def shuffle(deck):
    d = deck[:]
    random.shuffle(d)
    return d

def hcp(hand):
    return sum(HCP_VAL.get(c['r'],0) for c in hand)

def sorted_len(hand):
    return sorted([sum(1 for c in hand if c['s']==s) for s in SUITS], reverse=True)

def check_type(hand, t):
    if not t or t=='free': return True
    sl = sorted_len(hand)
    if t=='balanced': return sl in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]
    return True

def parse_commands(text):
    if not text.strip(): return []
    import re
    cmds = []
    for part in text.split('|'):
        part = part.strip()
        if not part: continue
        m = re.match(r'^(\d+)\+major$', part)   # N+major = 5+ בהרט או ספייד
        if m:
            cmds.append({'t':'majorlen','n':int(m.group(1))})
            continue
        m = re.match(r'^(\d+)\+minor$', part)   # N+minor = N+ בקלב או דיאמונד
        if m:
            cmds.append({'t':'minorlen','n':int(m.group(1))})
            continue
        m = re.match(r'^(\d+)(\+)?\s*([♠♥♦♣])$', part)
        if m:
            cmds.append({'t':'len','suit':m.group(3),'n':int(m.group(1)),'plus':bool(m.group(2))})
            continue
        m = re.match(r'^(\d+)-([♠♥♦♣])$', part)   # maxlen: n-suit = at most n cards
        if m:
            cmds.append({'t':'maxlen','suit':m.group(2),'n':int(m.group(1))})
            continue
        m = re.match(r'^([♠♥♦♣])>=([♠♥♦♣])$', part)
        if m:
            cmds.append({'t':'longer','s1':m.group(1),'s2':m.group(2)})
            continue
        if part == 'no5major':
            cmds.append({'t':'no5major'}); continue
        if part == 'not-balanced':
            cmds.append({'t':'not-balanced'}); continue
        if part == 'not-1nt':   # אקול: פוסל יד מאוזנת רק אם ה-HCP בטווח ה-1NT
            cmds.append({'t':'not-1nt'}); continue
        if part == 'major-longest':   # המיגור הארוך ≥ שני המינורים
            cmds.append({'t':'major-longest'}); continue
        m = re.match(r'^minorover([♣♦])$', part)   # אקול: מיגור רביעייה+ רק אם המינור ארוך ממש
        if m:
            cmds.append({'t':'minorover','suit':m.group(1)}); continue
        if part == 'minorover-gen':   # אקול, מינור גנרי: אותו כלל על המינור הארוך
            cmds.append({'t':'minorover-gen'}); continue
        if part == 'two4card':
            cmds.append({'t':'two4card'}); continue
        if part == 'no4major':
            cmds.append({'t':'no4major'}); continue
        if part == 'minor-club':
            cmds.append({'t':'minor-club'}); continue
        if part == 'minor-diamond':
            cmds.append({'t':'minor-diamond'}); continue
        m = re.match(r'^hcp(\d+)\+([♠♥♦♣])$', part)
        if m:
            cmds.append({'t':'suit-hcp','suit':m.group(2),'min':int(m.group(1))})
    return cmds

def check_commands(hand, cmds):
    for c in cmds:
        if c['t']=='len':
            length = sum(1 for x in hand if x['s']==c['suit'])
            if c['plus']:
                if length < c['n']: return False
            else:
                if length != c['n']: return False
        elif c['t']=='longer':
            l1 = sum(1 for x in hand if x['s']==c['s1'])
            l2 = sum(1 for x in hand if x['s']==c['s2'])
            if l1 < l2: return False
        elif c['t']=='no5major':
            if sum(1 for x in hand if x['s']=='♥') >= 5: return False
            if sum(1 for x in hand if x['s']=='♠') >= 5: return False
        elif c['t']=='not-balanced':
            sl = sorted([sum(1 for x in hand if x['s']==s) for s in SUITS], reverse=True)
            if sl in [[4,3,3,3],[4,4,3,2],[5,3,3,2]]: return False
        elif c['t']=='not-1nt':
            sl = sorted([sum(1 for x in hand if x['s']==s) for s in SUITS], reverse=True)
            if sl in [[4,3,3,3],[4,4,3,2],[5,3,3,2]] and cfg['ntMin'] <= hcp(hand) <= cfg['ntMax']:
                return False
        elif c['t']=='two4card':
            if sum(1 for s in SUITS if sum(1 for x in hand if x['s']==s) >= 4) < 2: return False
        elif c['t']=='maxlen':
            if sum(1 for x in hand if x['s']==c['suit']) > c['n']: return False
        elif c['t']=='majorlen':
            hh = sum(1 for x in hand if x['s']=='♥')
            ss = sum(1 for x in hand if x['s']=='♠')
            if max(hh, ss) < c['n']: return False
        elif c['t']=='minorlen':
            cl = sum(1 for x in hand if x['s']=='♣')
            di = sum(1 for x in hand if x['s']=='♦')
            if max(cl, di) < c['n']: return False
        elif c['t']=='minorover-gen':
            cl = sum(1 for x in hand if x['s']=='♣')
            di = sum(1 for x in hand if x['s']=='♦')
            ml = max(cl, di)
            for maj in ('♥','♠'):
                jl = sum(1 for x in hand if x['s']==maj)
                if jl >= 4 and ml <= jl: return False   # מיגור רביעייה+ ≥ המינור → פותחים מיגור
        elif c['t']=='major-longest':
            hh = sum(1 for x in hand if x['s']=='♥')
            ss = sum(1 for x in hand if x['s']=='♠')
            di = sum(1 for x in hand if x['s']=='♦')
            cl = sum(1 for x in hand if x['s']=='♣')
            if max(hh, ss) < max(di, cl): return False
        elif c['t']=='minorover':
            ml = sum(1 for x in hand if x['s']==c['suit'])
            for maj in ('♥','♠'):
                jl = sum(1 for x in hand if x['s']==maj)
                if jl >= 4 and ml <= jl:   # מיגור רביעייה+ שאינו קצר מהמינור → פותחים מיגור
                    return False
        elif c['t']=='no4major':
            if sum(1 for x in hand if x['s']=='♥') >= 4: return False
            if sum(1 for x in hand if x['s']=='♠') >= 4: return False
        elif c['t']=='minor-club':
            cl = sum(1 for x in hand if x['s']=='♣')
            di = sum(1 for x in hand if x['s']=='♦')
            # ♣>♦, OR ♣=♦=3
            if not (cl > di or (cl == di == 3)): return False
        elif c['t']=='minor-diamond':
            cl = sum(1 for x in hand if x['s']=='♣')
            di = sum(1 for x in hand if x['s']=='♦')
            if not (di > cl): return False  # מנוע פותח 1♦ רק כאשר ♦>♣
        elif c['t']=='suit-hcp':
            suit_pts = sum(HCP_VAL.get(x['r'],0) for x in hand if x['s']==c['suit'])
            if suit_pts < c['min']: return False
    return True

def _suit_len(hand, suit):
    return sum(1 for c in hand if c['s'] == suit)

def nt_responder_dealable(opener_hand, resp_hand):
    """מול פתיחת 1NT — יד משיב עם קלף בודד או חוסר, בלי התאמה במיגור,
    ו-10+ נקודות. אין לה הכרזה טובה בשיטה, ולכן לא מחלקים יד כזאת."""
    if min(_suit_len(resp_hand, s) for s in SUITS) > 1:
        return True                      # אין קוצר — יד רגילה
    if hcp(resp_hand) < 10:
        return True
    # התאמה במיגור = 8+ קלפים משותפים
    if any(_suit_len(opener_hand, s) + _suit_len(resp_hand, s) >= 8
           for s in ('♥','♠')):
        return True
    return False

def deal_one_board():
    constraints = {}
    for p in 'NESW':
        st = pState[p]
        cmds = parse_commands(st['commands'])
        constraints[p] = {'type':st['type'],'min':st['hcpMin'],'max':st['hcpMax'],'cmds':cmds}

    deck = create_deck()
    for _ in range(MAX_TRIES):
        d = shuffle(deck)
        h = {'N':d[0:13],'E':d[13:26],'S':d[26:39],'W':d[39:52]}
        ok = True
        for p in 'NESW':
            ph = h[p]; c = constraints[p]
            if not check_type(ph, c['type']): ok=False; break
            if hcp(ph)<c['min'] or hcp(ph)>c['max']: ok=False; break
            if not check_commands(ph, c['cmds']): ok=False; break
        # מצא את הפותח בפועל לפי pState
        opener_p  = next((p for p in 'NESW' if pState[p]['mode'] == 'opener'), 'N')
        partner_p = PARTNER[opener_p]
        is_weak2  = pState[opener_p].get('openType') == 'weak2'
        if ok and pState[opener_p].get('openKey') == 'nt' \
                and not nt_responder_dealable(h[opener_p], h[partner_p]):
            ok = False
        # מיגור גנרי: המשיב חייב תמיכה במיגור שהפותח פתח בפועל (לכל לוח בנפרד)
        if ok and pState[opener_p].get('openKey') == 'major' \
                and not pState[opener_p].get('openSuit') \
                and pState[partner_p].get('mode') == 'responder' \
                and pState[partner_p].get('respType') == 'support':
            oh = h[opener_p]
            hh = sum(1 for x in oh if x['s']=='♥')
            ss = sum(1 for x in oh if x['s']=='♠')
            opener_major = '♠' if ss >= hh else '♥'   # הארוך; שוויון → ♠ (הגבוה)
            if sum(1 for x in h[partner_p] if x['s']==opener_major) < 3:
                ok = False
        # מיגור גנרי + משיב 1NT: אין תמיכה רביעייה במיגור הפותח, ואין מיגור רביעייה
        # גבוה יותר (מעל 1♥ עם 4 ספייד מכריזים 1♠; מעל 1♠ הרט מותר — אין 1-לבל)
        if ok and pState[opener_p].get('openKey') == 'major' \
                and not pState[opener_p].get('openSuit') \
                and pState[partner_p].get('mode') == 'responder' \
                and pState[partner_p].get('respType') == '1nt':
            oh = h[opener_p]; rh = h[partner_p]
            hh = sum(1 for x in oh if x['s']=='♥')
            ss = sum(1 for x in oh if x['s']=='♠')
            om = '♠' if ss >= hh else '♥'
            if sum(1 for x in rh if x['s']==om) >= (3 if _WS_MODE else 4):  # WS: תמיכה 3+ פוסלת
                ok = False
            elif om == '♥' and sum(1 for x in rh if x['s']=='♠') >= 4:  # היה מכריז 1♠
                ok = False
        # מיגור גנרי + משיב 2NT (דף-עבודה בלבד): ללא תמיכה (≤2) בסדרת הפותח בפועל
        if _WS_MODE and ok and pState[opener_p].get('openKey') == 'major' \
                and not pState[opener_p].get('openSuit') \
                and pState[partner_p].get('mode') == 'responder' \
                and pState[partner_p].get('respType') == '2nt':
            oh = h[opener_p]; rh = h[partner_p]
            hh = sum(1 for x in oh if x['s']=='♥')
            ss = sum(1 for x in oh if x['s']=='♠')
            om = '♠' if ss >= hh else '♥'
            if sum(1 for x in rh if x['s']==om) >= 3:
                ok = False
        # מינור גנרי: המשיב-תמיכה חייב 5+ במינור שהפותח פתח בפועל (המינור הארוך)
        if ok and pState[opener_p].get('openKey') == 'minor' \
                and not pState[opener_p].get('openSuit') \
                and pState[partner_p].get('mode') == 'responder' \
                and pState[partner_p].get('respType') == 'supp-minor':
            oh = h[opener_p]
            cl = sum(1 for x in oh if x['s']=='♣')
            di = sum(1 for x in oh if x['s']=='♦')
            opener_minor = '♦' if di > cl else '♣'   # better minor; שוויון → ♣
            if sum(1 for x in h[partner_p] if x['s']==opener_minor) < 5:
                ok = False
        # תקרת אורך סדרה 6, ואין סינגלטון K/Q — בכל 4 הידיים (דף-עבודה בלבד)
        if _WS_MODE and ok:
            for p in 'NESW':
                for s in SUITS:
                    cs = [x for x in h[p] if x['s']==s]
                    if len(cs) > 6 or (len(cs) == 1 and cs[0]['r'] in ('K','Q')):
                        ok = False; break
                if not ok: break
        if ok and (is_weak2 or max(hcp(h[opener_p]), hcp(h[partner_p])) >= 12): return h
    return None

# ── Recompute state ────────────────────────────────────────────────────────────
def recompute_opener(p):
    st = pState[p]
    sMin, sMax = STRENGTH_OPENER.get(st['strengthKey'], (12, 21))

    if st['openKey']=='nt':
        st['type']='balanced'; st['hcpMin']=cfg['ntMin']; st['hcpMax']=cfg['ntMax']
        st['commands']=''; return

    if st['openKey'] in ('major','minor'):
        minLen = cfg['majorLen'] if st['openKey']=='major' else cfg['minorLen']
        st['type']='free'; st['hcpMin']=sMin; st['hcpMax']=sMax
        # אקול (NT חלש 12-14): מאוזן 15+ פותח סדרה, לכן מחריגים רק מאוזן שבטווח 1NT.
        # שיטה רגילה (NT חזק 15-17): 'not-balanced' כמו קודם — ללא שינוי.
        bal = 'not-1nt' if cfg['ntMin'] == 12 else 'not-balanced'
        if st['openKey']=='minor':
            if st['openSuit']:                       # מינור ספציפי (רשימת השיעורים)
                mc = st['openSuit']
                tag = 'minor-diamond' if mc=='♦' else 'minor-club'
                cmd = f"{minLen}+{mc}|{tag}|no5major|{bal}"
                if cfg['majorLen'] == 4:
                    # אקול (מיגור 4): מיגור רביעייה לפני מינור. פותח מינור יקבל
                    # מיגור רביעייה רק אם המינור ארוך ממש (5+). כולל 4-4 → מיגור.
                    cmd += f"|minorover{mc}"
            else:                                    # מינור גנרי — פותח את המינור הארוך
                cmd = f"{minLen}+minor|no5major|{bal}"
                if cfg['majorLen'] == 4:
                    cmd += "|minorover-gen"
            st['commands'] = cmd
        elif st['openSuit']:
            # מיגור ספציפי (מרשימת השיעורים)
            # 4-{other}: מונע 5♥+5♠ שיוביל לפתיחה בצבע הלא-נכון
            # {suit}>=♦/♣: פותחים מיגור רק אם הוא ≥ המינורים (אחרת פותחים מינור ארוך יותר)
            s = st['openSuit']; other = '♠' if s=='♥' else '♥'
            st['commands'] = f"{minLen}+{s}|{bal}|4-{other}|{s}>=♦|{s}>=♣"
        else:
            # מיגור גנרי: 5+ באחד המיגורים והמיגור הארוך ≥ המינורים
            st['commands'] = f"{minLen}+major|{bal}|major-longest"
        return

    if st['strengthKey']:
        st['type']='free'; st['hcpMin']=sMin; st['hcpMax']=sMax
        st['commands']=''; return

    st['type']='free'; st['hcpMin']=0; st['hcpMax']=37; st['commands']=''

def nt_resp_label(k):
    """תווית כוח-משיב ל-1NT לפי השיטה — הטווחים נגזרים מ-25 נק' לגיים.
    רגיל 15-17: 0-7 / 8-9 / 10+ · אקול 12-14: 0-10 / 11-12 / 13+."""
    game = 25 - cfg['ntMin']; inv = 25 - cfg['ntMax']
    return {'חלש 0-7':   f'חלש 0-{inv-1}',
            'בינוני 8-9': f'בינוני {inv}-{game-1}',
            'חזק 10+':    f'חזק {game}+'}.get(k, k)


def recompute_responder(p):
    st = pState[p]
    partner_suit = pState[PARTNER[p]]['openSuit']
    rs = st['respStrength']
    if rs in STRENGTH_RESP_NT:
        # ספי תגובה ל-1NT נגזרים מ-25 נק' משותפות לגיים:
        #   גיים (3NT) = 25 - ntMin   → 10 בחזק 15-17 / 13 באקול 12-14
        #   הזמנה (2NT) = 25 - ntMax  → 8 בחזק / 11 באקול
        game = 25 - cfg['ntMin']
        inv  = 25 - cfg['ntMax']
        NT_RESP_DYN = {'חלש 0-7': (0, inv - 1),
                       'בינוני 8-9': (inv, game - 1),
                       'חזק 10+': (game, 15),
                       'הזמנת סלאם 16-17': (16, 17),
                       'ג׳רבר 18+': (18, 22)}
        hMin, hMax = NT_RESP_DYN[rs]
    else:
        hMin, hMax = (STRENGTH_RESP_MINOR.get(rs) or
                      STRENGTH_RESP.get(rs, (0, 37)))

    t='free'; cmds=''
    rt = st['respType']
    open_type = st.get('openType','')

    if rt=='support':      cmds = f"3+{partner_suit}" if partner_suit else ''
    elif rt=='supp-minor': cmds = f"5+{partner_suit}" if partner_suit else ''
    elif rt=='1nt':
        t='balanced'
        if partner_suit == '♥':   cmds='2-♥|3-♠'
        elif partner_suit == '♠': cmds='2-♠'
        elif partner_suit in ('♣','♦'): cmds='no4major|4-♣|4-♦'  # מונע 2♣/2♦ עם 5 קלפים
        elif open_type == 'minor': cmds='no4major'   # מינור גנרי: 1NT מכחיש מיגור רביעייה (יכריז אותו)
        else:                     cmds=''            # מיגור גנרי: מטופל בתיאום ב-deal_one_board
    elif rt=='1h':
        if open_type == 'minor':  cmds='4+♥|3-♠'
        elif open_type == '2club': cmds='5+♥|4-♠'  # 2♣: חיובי עם 5 קלפים
        else:                      cmds='4+♥'
    elif rt=='1s':
        if open_type == 'minor':  cmds='4+♠|3-♥'
        elif open_type == '2club': cmds='5+♠'
        else:                      cmds='4+♠'
    elif rt=='2c':       cmds='4+♣'
    elif rt=='2d':       cmds='4+♦'
    elif rt=='trans-h':  cmds='5+♥|4-♠'  # מונע 5♠ שיגרום לטרנספר ♠ במקום ♥
    elif rt=='trans-s':  cmds='5+♠|4-♥'  # מונע 5♥ שיגרום לטרנספר ♥ במקום ♠
    elif rt=='2nt':
        t='balanced'
        if open_type not in ('2nt_op', 'nt'):
            hMin = max(hMin, 11)  # 2NT מעל פתיחת סדרה = 11+; מעל 1NT הטווח נגזר מ-25
        if partner_suit == '♥':
            cmds='2-♥|3-♠'
        elif partner_suit == '♠':
            cmds='2-♠|3-♥'
        elif partner_suit in ('♣','♦'):
            cmds='no4major|4-♦|4-♣'  # מונע 2♦/2♣ במקום 2NT
        else:
            cmds='no4major'
    elif rt=='stayman':  cmds=f"4+{st['respSuit'] or '♥'}|two4card|no5major"
    elif rt is None and open_type == 'nt':
        t='balanced'; cmds='no4major'

    st['type']=t; st['hcpMin']=hMin; st['hcpMax']=hMax; st['commands']=cmds

# ── Print HTML ─────────────────────────────────────────────────────────────────
def board_html(hands, num, dealer, cfg_snap, bi=0):
    eff_dealer = dealer if (dealer and dealer != '—') else ['N','E','S','W'][(num-1)%4]
    dl = f' &nbsp;|&nbsp; Dealer: {eff_dealer}'
    rows = '<tr><td></td><td></td><td></td><td></td></tr>' * 5
    # תאי הידיים ריקים עם מזהים; JS ממלא מ-BOARDS ומאפשר החלפת קלפים (קליק-קליק)
    return f'''<div class="board">
      <div class="board-header">Board {num}{dl}</div>
      <div class="hand-grid">
        <div class="cell-n"><div class="hl" id="h-{bi}-N"></div></div>
        <div class="cell-w"><div id="h-{bi}-W"></div></div>
        <div class="cell-c"><div class="compass-wrap"><div class="compass-circle"></div>
          <span class="cn">N</span><span class="cw">W</span><span class="ce">E</span><span class="cs">S</span>
        </div></div>
        <div class="cell-e"><div id="h-{bi}-E"></div></div>
        <div class="cell-s"><div class="hl" id="h-{bi}-S"></div></div>
      </div>
      <table class="score-table">
        <thead><tr><th>N</th><th>E</th><th>S</th><th>W</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''

CSS = """
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:Arial,sans-serif; font-size:14px; background:#fff; }
/* על המסך: זרימה חופשית (שורות לפי תוכן) כדי שלוחות לא ידרסו זה את זה בעריכה.
   הגובה הקבוע ל-A4 חל רק בהדפסה (ב-@media print למטה). */
.page { width:180mm; margin:5mm auto; display:grid;
        grid-template-columns:1fr 1fr; gap:5mm; align-items:start; }
.board { border:1.5px solid #333; border-radius:3px; padding:6px; background:#fff; }
.board-header { text-align:center; font-size:12px; font-weight:bold;
                border-bottom:1px solid #bbb; padding-bottom:3px; margin-bottom:4px; }
.hand-grid { display:grid; direction:ltr;
             grid-template-areas:". north ." "west center east" ". south .";
             grid-template-columns:1fr 62px 1fr; grid-template-rows:auto auto auto;
             align-items:center; margin-top:-7px; }
.cell-n { grid-area:north; text-align:center; padding:3px 0; transform:translateY(8px); }
.cell-s { grid-area:south; text-align:center; padding:3px 0; transform:translateY(-8px); }
.cell-w { grid-area:west;  text-align:left; padding:4px 6px 4px 2px; transform:translateX(23px); }
.cell-e { grid-area:east;  text-align:left; padding:4px 2px 4px 6px; }
.cell-c { grid-area:center; display:flex; align-items:center; justify-content:center; padding:4px 0; }
.cell-n .hl, .cell-s .hl { display:inline-block; text-align:left; }
.sr  { display:block; line-height:1.5; white-space:nowrap; font-size:15px; font-weight:bold; }
.sp  { color:#111; font-weight:bold; } .he { color:#cc1111; font-weight:bold; }
.di  { color:#cc1111; font-weight:bold; } .cl { color:#111; font-weight:bold; }
.compass-wrap { width:58px; height:58px; position:relative; display:flex;
                align-items:center; justify-content:center; }
.compass-circle { width:54px; height:54px; border:2px solid #1a4a2e; border-radius:6px;
                  position:absolute;
                  background:radial-gradient(ellipse at 40% 35%,#4aaa5a 0%,#2d8a3e 55%,#1a5a28 100%);
                  box-shadow:inset 0 2px 8px rgba(255,255,255,0.15),
                             inset 0 -3px 8px rgba(0,0,0,0.35), 2px 3px 7px rgba(0,0,0,0.4); }
.cn,.cs,.cw,.ce { position:absolute; font-size:12px; font-weight:bold; line-height:1;
                  z-index:1; color:#fff; text-shadow:0 1px 3px rgba(0,0,0,0.6); }
.cn { top:5px;    left:50%; transform:translateX(-50%); }
.cs { bottom:5px; left:50%; transform:translateX(-50%); }
.cw { left:5px;   top:50%;  transform:translateY(-50%); }
.ce { right:5px;  top:50%;  transform:translateY(-50%); }
.hcp-badge { display:block; font-size:10px; font-weight:bold; color:#1a4a2e;
             background:#e8f0d8; border:1px solid #9ab87a; border-radius:3px;
             text-align:center; margin-top:2px; padding:0 3px; width:fit-content; }
.score-table { border-collapse:collapse; width:100%; table-layout:fixed; margin-top:5px; }
.score-table th, .score-table td { border:1px solid #555; width:25%; height:18px; line-height:18px; text-align:center; vertical-align:middle; padding:0; font-size:11px; font-weight:bold; box-sizing:border-box; }
.score-table th { background:#eee; }
.pbtn { display:block; margin:8px auto 12px; padding:8px 28px; font-size:13pt;
        background:#1a4a2e; color:#f0e6c8; border:none; border-radius:8px; cursor:pointer; }
.toolbar { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin:10px auto 4px; }
.toolbar .pbtn { display:inline-block; margin:0; padding:8px 20px; }
.hint { text-align:center; color:#555; font-size:12px; margin:-4px auto 10px; }
.card { cursor:pointer; padding:0 0.5px; border-radius:3px; }
.card.sel { background:#f2c14e; box-shadow:0 0 0 1px #b8860b; }
@media print {
  .page { height:255mm; grid-template-rows:1fr 1fr; align-items:stretch; page-break-after:always; }
  .pbtn, .hint, .toolbar { display:none; }
  .card { cursor:default; }
  .card.sel { background:none; box-shadow:none; }
  .compass-circle { background:#fff !important; box-shadow:none !important; border-color:#333 !important; }
  .cn,.cs,.cw,.ce { color:#000 !important; text-shadow:none !important; }
  @page { size:A4 portrait; margin:5mm; }
}
"""

# ── JS להחלפת קלפים בפלט ההדפסה (קליק-קליק) ──────────────────────────────────
SWAP_JS = r"""
const SUITS=['♠','♥','♦','♣'];
const RANKS=['A','K','Q','J','T','9','8','7','6','5','4','3','2'];
const CLS={'♠':'sp','♥':'he','♦':'di','♣':'cl'};
const HCPV={A:4,K:3,Q:2,J:1};
let sel=null;
function renderHand(bi,pl){
  const hand=BOARDS[bi][pl];
  let html='',pts=0;
  for(const s of SUITS){
    const cs=hand.filter(c=>c[0]===s).sort((a,b)=>RANKS.indexOf(a[1])-RANKS.indexOf(b[1]));
    const inner=cs.length?cs.map(function(c){
      return '<span class="card" data-bi="'+bi+'" data-pl="'+pl+'" data-s="'+s+'" data-r="'+c[1]+'">'+c[1]+'</span>';
    }).join(''):'—';
    html+='<span class="sr"><span class="'+CLS[s]+'">'+s+'</span> '+inner+'</span>';
  }
  for(const c of hand){pts+=HCPV[c[1]]||0;}
  html+='<span class="hcp-badge">'+pts+'</span>';
  document.getElementById('h-'+bi+'-'+pl).innerHTML=html;
}
function renderAll(){for(let bi=0;bi<BOARDS.length;bi++){for(const pl of ['N','E','S','W'])renderHand(bi,pl);}}
function clearSel(){const e=document.querySelector('.card.sel');if(e)e.classList.remove('sel');sel=null;}
document.addEventListener('click',function(ev){
  const el=ev.target.closest('.card');
  if(!el)return;
  const bi=+el.dataset.bi,pl=el.dataset.pl,s=el.dataset.s,r=el.dataset.r;
  if(!sel){sel={bi:bi,pl:pl,s:s,r:r};el.classList.add('sel');return;}
  if(sel.bi!==bi){clearSel();return;}                 // רק באותו לוח
  if(sel.pl===pl){                                     // אותה יד
    const same=(sel.s===s&&sel.r===r);
    clearSel();
    if(!same){sel={bi:bi,pl:pl,s:s,r:r};el.classList.add('sel');}
    return;
  }
  const A=BOARDS[bi][sel.pl],B=BOARDS[bi][pl];
  const ai=A.findIndex(function(c){return c[0]===sel.s&&c[1]===sel.r;});
  const bj=B.findIndex(function(c){return c[0]===s&&c[1]===r;});
  const t=A[ai];A[ai]=B[bj];B[bj]=t;
  const p1=sel.pl;sel=null;
  renderHand(bi,p1);renderHand(bi,pl);
});
renderAll();
"""

# ── JS פלט מאוחד: LIN / BBO / סטריפים — הכול מתוך BOARDS הערוך (אחרי הזזות) ──────
# נמל של lin_export / handviewer_page ל-JS, כדי שהזזת קלף בדף העריכה תשתקף בכל
# הפלטים. DLR = דילר תקין (נופל ל-N אם ריק). רץ אחרי SWAP_JS (SUITS/RANKS/CLS משותפים).
OUTPUT_JS = r"""
const DLR = /[NESW]/i.test(DEALER) ? DEALER.toUpperCase() : 'N';
const LIN_DEALER = {S:1, W:2, N:3, E:4};
function linHand(hand){
  const M=[['♠','S'],['♥','H'],['♦','D'],['♣','C']]; let out='';
  for(const pair of M){
    const rs=hand.filter(c=>c[0]===pair[0]).map(c=>c[1])
                 .sort((a,b)=>RANKS.indexOf(a)-RANKS.indexOf(b));
    out+=pair[1]+rs.join('');
  }
  return out;
}
function linExport(){
  const n=BOARDS.length, d=LIN_DEALER[DLR]||3;
  let head='vg|,,P,1,'+n+',Team 1,0,Team 2,0|'
    +'rs|'+','.repeat(2*n-1)+'|'
    +'pw|'+','.repeat(4*n-1)+'|'
    +'mp|'+','.repeat(2*n-1)+'|'
    +'bn|'+Array.from({length:n},(_,i)=>i+1).join(',')+'|pg||';
  const lines=[head];
  for(let i=1;i<=n;i++){
    const b=BOARDS[i-1];
    const hands=[b.S,b.W,b.N].map(linHand).join(',');
    const prefix=(i===1)?'mn||':'';
    lines.push(prefix+'pn|,,,|qx|o'+i+',BOARD '+i+'|rh||ah|Board '+i
      +'|md|'+d+hands+'|sv|0|sa|0|pg||');
  }
  return lines.join('\n')+'\n';
}
function downloadText(fn,text,mime){
  const blob=new Blob([text],{type:mime||'text/plain;charset=utf-8'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download=fn;
  document.body.appendChild(a); a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href); a.remove();},1000);
}
function saveLIN(){ downloadText('boards.lin', linExport(), 'text/plain'); }

function hvUrl(bi){
  const b=BOARDS[bi];
  const parts=['N','E','S','W'].map(function(p){return p.toLowerCase()+'='+linHand(b[p]).toLowerCase();});
  parts.push('d='+DLR.toLowerCase());
  return HV_BASE+'?'+parts.join('&');
}
function openBBO(){
  let blocks='';
  for(let bi=0;bi<BOARDS.length;bi++){
    const url=hvUrl(bi);
    blocks+='<section><h2>לוח <bdi>'+(bi+1)+'</bdi>'
      +'<span class="d">דילר <bdi>'+DLR+'</bdi></span>'
      +'<a href="'+url+'" target="_blank" rel="noopener">פתח לבד ↗</a></h2>'
      +'<iframe src="'+url+'" loading="lazy"></iframe></section>';
  }
  const doc='<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
    +'<meta name="viewport" content="width=device-width,initial-scale=1">'
    +'<title>לוחות ל-BBO HandViewer</title><style>'
    +'body{margin:0;font-family:Arial,sans-serif;background:#123;color:#eee;padding:12px}'
    +'h1{font-size:20px;margin:8px 4px}'
    +'section{background:#0a3d24;border-radius:10px;margin:0 0 22px;padding:10px}'
    +'h2{font-size:17px;margin:2px 4px 10px;display:flex;align-items:center;gap:14px}'
    +'.d{font-size:13px;color:#8fd0a8;font-weight:normal}'
    +'h2 a{margin-inline-start:auto;font-size:13px;color:#9cf;text-decoration:none}'
    +'iframe{width:100%;height:78vh;border:0;border-radius:6px;background:#0a3d24}'
    +'</style></head><body><h1>לוחות ל-BBO HandViewer — <bdi>'+BOARDS.length+'</bdi> לוחות</h1>'
    +blocks+'</body></html>';
  const w=window.open('','_blank');
  if(w){w.document.write(doc); w.document.close();}
  else alert('חוסם החלונות מנע פתיחה. אפשר חלונות קופצים לדף זה.');
}

function stripHand(bi,pl){
  const hand=BOARDS[bi][pl]; let html='';
  for(const s of SUITS){
    const cs=hand.filter(c=>c[0]===s)
                 .sort((a,b)=>RANKS.indexOf(a[1])-RANKS.indexOf(b[1]))
                 .map(c=>c[1]).join('');
    html+='<span class="ln"><span class="'+CLS[s]+'">'+s+'</span> '+(cs||'—')+'</span>';
  }
  return html;
}
const WIND={N:'צפון',E:'מזרח',S:'דרום',W:'מערב'};
function openStrips(){
  let rows='';
  for(let bi=0;bi<BOARDS.length;bi++){
    let cols='';
    for(const pl of ['N','E','S','W'])
      cols+='<div class="pos"><div class="pl"><span class="bd">לוח <bdi>'+(bi+1)+'</bdi></span>'
            +'<span class="dline"><span class="dir">'+WIND[pl]+'</span>'
            +(pl===DLR?'<span class="dlr">דילר</span>':'')+'</span></div>'
            +stripHand(bi,pl)+'</div>';
    rows+='<div class="strip">'+cols+'</div>';
  }
  const css='body{font-family:Arial,sans-serif;margin:0;padding:4mm;color:#111}'
    +'.tb{margin:0 0 6mm}'
    +'.tb button{background:#1a4a2e;color:#f0e6c8;border:none;border-radius:6px;padding:7px 20px;font-size:13pt;cursor:pointer}'
    +'.strip{display:flex;justify-content:flex-end;gap:11mm;direction:ltr;border:1px solid #333;'
    +'border-radius:4px;padding:8px 12px;margin-bottom:5mm;page-break-inside:avoid}'
    +'.pos{min-width:130px}'
    +'.pl{direction:rtl;text-align:center;border-bottom:1px solid #ccc;margin-bottom:4px;padding-bottom:3px}'
    +'.bd{display:block;font-size:14px;font-weight:bold;color:#1a4a2e;line-height:1.25}'
    +'.dline{display:block;line-height:1.3}'
    +'.dir{font-size:16px;font-weight:bold;color:#1a4a2e}'
    +'.dlr{font-size:12px;font-weight:bold;color:#fff;background:#1a4a2e;'
    +'border-radius:3px;padding:0 7px;margin-inline-start:6px;display:inline-block}'
    +'.ln{display:block;font-size:19px;font-weight:bold;white-space:nowrap;line-height:1.55}'
    +'.sp,.cl{color:#111}.he,.di{color:#c11}'
    +'@media print{.tb{display:none}}@page{size:A4 portrait;margin:6mm}';
  const doc='<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
    +'<title>סטריפים</title><style>'+css+'</style></head><body>'
    +'<div class="tb"><button onclick="window.print()">🖨 הדפס סטריפים</button></div>'
    +rows+'</body></html>';
  const w=window.open('','_blank');
  if(w){w.document.write(doc); w.document.close();}
  else alert('חוסם החלונות מנע פתיחה. אפשר חלונות קופצים לדף זה.');
}
"""

# ── ייצוא LIN (BBO / ברידג' קומפוזר) ──────────────────────────────────────────
# פורמט LIN Classic. אומת מול קבצי ברידג' קומפוזר של יצחק:
#   D:\הוראת הברידג\ברידג' קומפיוזר גלם\*.lin  (70 לוחות, 10 קבצים)
#
#   md|<ספרת דילר><דרום>,<מערב>,<צפון>   — מזרח מחושב מהשאריות ולא נכתב
#   כותרת: rs = 2×לוחות שדות, pw = 4×לוחות, mp = 2×לוחות
#   sv|0| = אף אחד לא פגיע. האפליקציה לא מנהלת פגיעוּת, ו-0 הוא הערך
#           שמופיע ב-54 מתוך 70 הלוחות של יצחק.
#   חלוקה בלבד — בלי מכרז (mb|) ובלי משחק (pc|), כמו בכל הקבצים שלו.
LIN_DEALER = {'S': 1, 'W': 2, 'N': 3, 'E': 4}

def lin_hand(hand):
    """יד אחת: S<דרגות>H<דרגות>D<דרגות>C<דרגות>, מהגבוה לנמוך."""
    out = []
    for suit, letter in (('♠','S'), ('♥','H'), ('♦','D'), ('♣','C')):
        ranks = sorted((c['r'] for c in hand if c['s'] == suit), key=RANKS.index)
        out.append(letter + ''.join(ranks))
    return ''.join(out)

def lin_export(boards, dealer):
    """מחרוזת LIN מלאה לכל הלוחות שבמאגר."""
    n = len(boards)
    d = LIN_DEALER.get(dealer, 3)
    head = (f'vg|,,P,1,{n},Team 1,0,Team 2,0|'
            f'rs|{"," * (2*n - 1)}|'
            f'pw|{"," * (4*n - 1)}|'
            f'mp|{"," * (2*n - 1)}|'
            f'bn|{",".join(str(i) for i in range(1, n+1))}|pg||')
    lines = [head]
    for i, h in enumerate(boards, start=1):
        hands  = ','.join(lin_hand(h[p]) for p in ('S','W','N'))
        prefix = 'mn||' if i == 1 else ''
        lines.append(f'{prefix}pn|,,,|qx|o{i},BOARD {i}|rh||ah|Board {i}|'
                     f'md|{d}{hands}|sv|0|sa|0|pg||')
    return '\n'.join(lines) + '\n'

# ── קישור BBO HandViewer ──────────────────────────────────────────────────────
# לפי התיעוד הרשמי: https://www.bridgebase.com/tools/hvdoc.html
#   handviewer.html?n=..&e=..&s=..&w=..&d=..
#   כל יד = רצף אותיות קטנות s<דרגות>h<דרגות>d<דרגות>c<דרגות> (בלי פסיקים),
#   בדיוק הפורמט של lin_hand() אבל lowercase. דוגמה רשמית:
#     ?s=sakqhakqdakqcakqj&d=w&a=3hpp
#   d = דילר: n/e/s/w.  ידיים בלבד, בלי a= (מכרז) — התלמיד מכריז בעצמו.
HV_BASE = 'https://www.bridgebase.com/tools/handviewer.html'

def handviewer_url(board, dealer):
    """קישור HandViewer ללוח בודד — ארבע הידיים, בלי מכרז."""
    parts = [f'{p.lower()}={lin_hand(board[p]).lower()}'
             for p in ('N', 'E', 'S', 'W')]
    parts.append(f'd={dealer.lower()}')
    return HV_BASE + '?' + '&'.join(parts)

def handviewer_page(boards, dealer):
    """דף HTML שמרכז את כל הלוחות — כל לוח במסגרת גדולה + קישור ישיר.
    נפתח בדפדפן, וניתן לשמור ולשלוח לתלמידים."""
    blocks = []
    for i, b in enumerate(boards, start=1):
        url = handviewer_url(b, dealer)
        blocks.append(
            f'<section>'
            f'<h2>לוח {i}<span class="d">דילר {dealer}</span>'
            f'<a href="{url}" target="_blank" rel="noopener">פתח לבד ↗</a></h2>'
            f'<iframe src="{url}" loading="lazy"></iframe>'
            f'</section>')
    return (
        '<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>לוחות ל-BBO HandViewer</title><style>'
        'body{margin:0;font-family:Arial,sans-serif;background:#123;color:#eee;padding:12px}'
        'h1{font-size:20px;margin:8px 4px}'
        'section{background:#0a3d24;border-radius:10px;margin:0 0 22px;padding:10px}'
        'h2{font-size:17px;margin:2px 4px 10px;display:flex;align-items:center;gap:14px}'
        '.d{font-size:13px;color:#8fd0a8;font-weight:normal}'
        'h2 a{margin-inline-start:auto;font-size:13px;color:#9cf;text-decoration:none}'
        'iframe{width:100%;height:78vh;border:0;border-radius:6px;background:#0a3d24}'
        '</style></head><body>'
        f'<h1>לוחות ל-BBO HandViewer — {len(boards)} לוחות</h1>'
        + ''.join(blocks) +
        '</body></html>')

def open_print(boards, dealer):
    cfg_snap = dict(cfg)
    pages = ''
    for i in range(0, len(boards), 4):
        pages += '<div class="page">'
        for j in range(4):
            if i+j < len(boards):
                pages += board_html(boards[i+j], i+j+1, dealer, cfg_snap, bi=i+j)
        pages += '</div>'

    # נתוני הלוחות ל-JS: כל יד = רשימת [סדרה, דרגה]
    boards_data = [{p: [[c['s'], c['r']] for c in b[p]] for p in 'NESW'} for b in boards]
    boards_json = json.dumps(boards_data, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>לוחות</title>
<style>{CSS}</style></head>
<body>
<div class="toolbar">
  <button class="pbtn" onclick="window.print()">🖨 הדפס</button>
  <button class="pbtn" onclick="openStrips()">📄 סטריפים</button>
  <button class="pbtn" onclick="saveLIN()">💾 LIN</button>
  <button class="pbtn" onclick="openBBO()">🌐 BBO</button>
</div>
<div class="hint">לחצו קלף ואז קלף אחר באותו לוח כדי להחליף ביניהם. כל הפלטים משתמשים בלוחות שאחרי העריכה.</div>
{pages}
<script>
const BOARDS = {boards_json};
const DEALER = {json.dumps(dealer)};
const HV_BASE = {json.dumps(HV_BASE)};
{SWAP_JS}
{OUTPUT_JS}
</script>
</body></html>'''

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
    tmp.write(html)
    tmp.close()
    webbrowser.open(f'file:///{tmp.name}')

# ── Colors & Fonts ─────────────────────────────────────────────────────────────
THEMES = {
    'classic': {
        'BG': '#1a4a2e', 'BAR_BG': '#163d25', 'PAN_BG': '#f5eeff', 'PAN_BORDER': '#c8a84b',
        'GOLD': '#c8a84b', 'CREAM': '#f0e6c8',
        'PLAYER_COLORS': {'N':'#2255aa','S':'#cc2222','E':'#cc7700','W':'#228844'}
    },
    'light_green': {
        'BG': '#4a7a5a', 'BAR_BG': '#3c6645', 'PAN_BG': '#edf5e8', 'PAN_BORDER': '#9bb97f',
        'GOLD': '#8c9d67', 'CREAM': '#f4f7ed',
        'PLAYER_COLORS': {'N':'#2c6ca4','S':'#b03246','E':'#a86f3a','W':'#3b8a61'}
    },
    'bright_modern': {
        'BG': '#dbeafe', 'BAR_BG': '#bfdbfe', 'PAN_BG': '#f2ecfb', 'PAN_BORDER': '#d4af37',
        'GOLD': '#d4af37', 'CREAM': '#f8f5fb',
        'PLAYER_COLORS': {'N':'#2d4f8f','S':'#b53333','E':'#be6f2c','W':'#6b4dae'}
    }
}

CURRENT_THEME = THEMES['classic']
BG       = CURRENT_THEME['BG']
BAR_BG   = CURRENT_THEME['BAR_BG']
PAN_BG   = CURRENT_THEME['PAN_BG']
PAN_BORDER = CURRENT_THEME['PAN_BORDER']
GOLD     = CURRENT_THEME['GOLD']
CREAM    = CURRENT_THEME['CREAM']
PLAYER_COLORS = CURRENT_THEME['PLAYER_COLORS']
FONT     = ('Segoe UI', 12)
FONT_B   = ('Segoe UI', 13, 'bold')
FONT_SM  = ('Segoe UI', 11)
FONT_LG  = ('Segoe UI', 15, 'bold')

# ── Modern Lessons-Panel palette (deep green frame + lavender cards) ────────────
LP_BG      = BG            # רקע ירוק עמוק (כמו האפליקציה) — #1a4a2e
LP_HDR_BG  = BAR_BG        # פס כותרת קבוצה — ירוק כהה #163d25
LP_HDR_FG  = GOLD          # טקסט כותרת — זהב
LP_CARD    = '#e0d5f2'     # פני כפתור — לבנדר (גוון A)
LP_CARD_BD = '#bca9dd'     # מסגרת כרטיס עדינה
LP_TINT    = '#ffffff'     # hover — הבהרה ללבן
LP_INK     = '#1f3a2b'     # טקסט כפתור — ירוק כהה
LP_SEL     = GOLD          # כפתור נבחר — זהב (כמו המתגים באפליקציה)
LP_SEL_FG  = BG            # טקסט כפתור נבחר — ירוק כהה
LP_FONT    = 'Segoe UI Semibold'
LP_BTN_H   = 34            # גובה כפתור אחיד (טור אחד) — מאושר


def styled_btn(parent, text, cmd, active=False, resp=False, w=10):
    if active and resp:
        bg, fg = '#fde8de', '#8d3400'
    elif active:
        bg, fg = '#eadffd', '#2f1f57'
    elif resp:
        bg, fg = '#ffe9ea', '#8f2b31'
    else:
        bg, fg = '#f4eff8', '#2a1f3d'
    font = FONT_B if active else FONT_SM
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  font=font, relief='groove', cursor='hand2',
                  width=w, pady=3, activebackground=bg, activeforeground=fg)
    return b


def group_label(parent, text, bg, center=False):
    tk.Label(parent, text=text, bg=bg, fg='#5f4d7a',
             font=('Segoe UI', 9)).pack(anchor='center' if center else 'w', pady=(5,1))


# ── Lessons Panel ─────────────────────────────────────────────────────────────
class LessonsPanel(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title('דפי עבודה')
        self.configure(bg=LP_BG)
        self.resizable(False, True)
        self._active_btn = None
        self._build()
        self.update_idletasks()
        app.update_idletasks()
        screen_w = app.winfo_screenwidth()
        screen_h = app.winfo_screenheight()
        win_w, win_h = 340, min(640, screen_h - 80)
        x = screen_w - win_w - 20
        y = 40
        self.geometry(f'{win_w}x{win_h}+{x}+{y}')

    def _build(self):
        # פס הדגשה עליון: זהב דק
        tk.Frame(self, bg=GOLD, height=3).pack(fill='x')

        tk.Label(self, text='דפי עבודה  📄', bg=LP_BG, fg=GOLD,
                 font=(LP_FONT, 16, 'bold'), anchor='e').pack(
                 fill='x', padx=14, pady=(12, 8))

        outer = tk.Frame(self, bg=LP_BG)
        outer.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        canvas = tk.Canvas(outer, bg=LP_BG, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = tk.Frame(canvas, bg=LP_BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

        # טור אחד לפי WORKSHEET_PANEL: כותרות ('h') + כפתורי דפי-עבודה ('b')
        for item in WORKSHEET_PANEL:
            if item[0] == 'h':
                hdr = tk.Frame(inner, bg=LP_HDR_BG)
                hdr.pack(fill='x', pady=(8, 3))
                tk.Frame(hdr, bg=GOLD, width=4).pack(side='right', fill='y')
                tk.Label(hdr, text=item[1], bg=LP_HDR_BG, fg=LP_HDR_FG,
                         font=(LP_FONT, 12, 'bold'), anchor='e',
                         padx=12, pady=5).pack(fill='x')
            else:
                self._make_button(inner, item[1], item[2])

    def _make_button(self, parent, labelspec, scenarios):
        """כפתור דף-עבודה בגובה אחיד. labelspec = מחרוזת או ('split', עברית, לטינית)
        (הלטינית נעוצה שמאל — כי Tk BiDi לא שם NT משמאל). לחיצה → _make_worksheet."""
        card = tk.Frame(parent, bg=LP_CARD, height=LP_BTN_H,
                        highlightthickness=1, highlightbackground=LP_CARD_BD,
                        cursor='hand2')
        card.pack_propagate(False)
        card.pack(fill='x', pady=3)

        bgs = [card]; fgs = []
        if isinstance(labelspec, tuple) and labelspec[0] == 'split':
            box = tk.Frame(card, bg=LP_CARD); box.pack(expand=True)
            l_lat = tk.Label(box, text=labelspec[2], bg=LP_CARD, fg=LP_INK, font=(LP_FONT, 13))
            l_lat.pack(side='left')
            l_heb = tk.Label(box, text=labelspec[1], bg=LP_CARD, fg=LP_INK, font=(LP_FONT, 13))
            l_heb.pack(side='left', padx=(2, 0))
            bgs += [box, l_lat, l_heb]; fgs += [l_lat, l_heb]
        else:
            lbl = tk.Label(card, text=labelspec, bg=LP_CARD, fg=LP_INK, font=(LP_FONT, 13))
            lbl.pack(expand=True)
            bgs.append(lbl); fgs.append(lbl)

        parts = {'card': card, 'bgs': bgs, 'fgs': fgs}
        for w in bgs:
            w.bind('<Button-1>', lambda e, p=parts, sc=scenarios: self._apply(p, sc))
            w.bind('<Enter>',    lambda e, p=parts: self._hover(p, True))
            w.bind('<Leave>',    lambda e, p=parts: self._hover(p, False))

    def _set_colors(self, parts, bg, fg, border):
        for w in parts['bgs']: w.config(bg=bg)
        for w in parts['fgs']: w.config(fg=fg)
        parts['card'].config(highlightbackground=border)

    def _hover(self, parts, on):
        if on:
            self._set_colors(parts, LP_TINT, LP_INK, GOLD)
        else:
            self._set_colors(parts, LP_CARD, LP_INK, LP_CARD_BD)

    def _apply(self, parts, scenarios):
        # פלאש זהב קצר למשוב, ואז חלוקת דף העבודה (מוסיף למאגר)
        self._set_colors(parts, LP_SEL, LP_SEL_FG, LP_SEL)
        self.update_idletasks()
        self.after(140, lambda: self._set_colors(parts, LP_CARD, LP_INK, LP_CARD_BD))
        self.app._make_worksheet(scenarios)


# ── App ────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('🃏 Bridge Teacher — עזרה למורה')
        self.configure(bg=BG)
        self.resizable(True, True)
        self.after(0, lambda: self.state('zoomed'))
        self._board_buffer = []
        self._buffer_dealer = 'N'
        self._build_title()
        self._build_settings()
        self._build_panels()
        self._build_actions()

    def _build_title(self):
        tk.Label(self, text='🃏  Bridge Teacher — עזרה למורה',
                 bg=BG, fg=CREAM, font=('Segoe UI', 16, 'bold')).pack(pady=(12,4))

    def _build_settings(self):
        outer = tk.Frame(self, bg=BAR_BG, pady=8)
        outer.pack(fill='x', padx=12, pady=(0,8))
        bar = tk.Frame(outer, bg=BAR_BG)
        bar.pack(anchor='center')

        self._cfg_btns = {}

        def sep():
            tk.Label(bar, text='|', bg=BAR_BG, fg=CREAM).pack(side='left', padx=8)

        def cfg_btn(parent, text, key, value):
            def toggle():
                cfg[key] = value
                self._on_cfg()
                self._refresh_cfg_btns()
            b = tk.Button(parent, text=text, command=toggle,
                          font=FONT_SM, relief='groove', width=8, pady=3, cursor='hand2',
                          bg=PAN_BG, fg='#4f3d7a', activebackground='#ead9ff')
            self._cfg_btns[(key,value)] = b
            b.pack(side='left', padx=2)

        tk.Label(bar, text='מיגור:', bg=BAR_BG, fg=CREAM, font=FONT_B).pack(side='left', padx=(10,3))
        cfg_btn(bar, '5 קלפים', 'majorLen', 5)
        cfg_btn(bar, '4 קלפים', 'majorLen', 4)
        sep()
        tk.Label(bar, text='1NT:', bg=BAR_BG, fg=CREAM, font=FONT_B).pack(side='left', padx=(0,3))
        cfg_btn(bar, '15-17', 'nt', '15-17')
        cfg_btn(bar, '12-14', 'nt', '12-14')
        self._refresh_cfg_btns()

    def _refresh_cfg_btns(self):
        nt_val = '12-14' if cfg['ntMin']==12 else '15-17'
        active_map = {
            ('majorLen', cfg['majorLen']): True,
            ('nt', nt_val): True,
            ('minorLen', cfg['minorLen']): True,
        }
        for (key,val), btn in self._cfg_btns.items():
            active = active_map.get((key,val), False)
            if active:
                btn.config(bg=GOLD, fg=BG, font=FONT_B,
                           relief='flat', bd=0)
            else:
                btn.config(bg=PAN_BG, fg='#4f3d7a', font=FONT_SM,
                           relief='flat', bd=0)

    def _on_cfg(self):
        if cfg.get('nt')=='12-14': cfg['ntMin'],cfg['ntMax']=12,14
        else: cfg['ntMin'],cfg['ntMax']=15,17
        for p in 'NESW':
            if pState[p]['mode']=='opener': recompute_opener(p)
            elif pState[p]['mode']=='responder': recompute_responder(p)
        self._refresh_all()

    def _build_panels(self):
        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=12, pady=2)
        self.panels = {}
        for p,r,c in [('N',0,0),('E',0,1),('S',1,0),('W',1,1)]:
            pf = PlayerPanel(grid, p, self)
            pf.grid(row=r, column=c, padx=6, pady=6, sticky='nsew')
            self.panels[p] = pf

    def _build_actions(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(pady=(6,10))

        # ── Row 1: Deal + Boards + Dealer ──────────────────────────────────────
        row1 = tk.Frame(outer, bg=BG)
        row1.pack(pady=(0,4))

        tk.Button(row1, text='⚡  צור לוחות', command=self._deal,
                  bg=GOLD, fg='white', font=('Segoe UI',14,'bold'),
                  relief='flat', padx=24, pady=8,
                  activebackground='#a07830', activeforeground='white',
                  cursor='hand2').pack(side='left', padx=(0,8))

        tk.Label(row1, text='לוחות:', bg=BG, fg=CREAM, font=FONT).pack(side='left')
        self.var_boards = tk.IntVar(value=4)
        tk.Spinbox(row1, from_=1, to=36, textvariable=self.var_boards, width=4,
                   font=FONT, bg=CREAM, relief='flat').pack(side='left', padx=(3,14))

        tk.Label(row1, text='דילר:', bg=BG, fg=CREAM, font=FONT_B).pack(side='left', padx=(0,4))
        self.var_dealer = tk.StringVar(value='—')
        self._dealer_buttons = {}
        for v,t in [('—','ללא'),('N','צפון'),('E','מזרח'),('S','דרום'),('W','מערב')]:
            btn = styled_btn(row1, text=t, cmd=lambda v=v: self._set_dealer(v), active=False, w=9)
            btn.pack(side='left', padx=2)
            self._dealer_buttons[v] = btn
        self._refresh_dealer_buttons()

        # ── Row 2: Buffer + Print + Clear + Lessons + Auction + Reset ──────────
        row2 = tk.Frame(outer, bg=BG)
        row2.pack()

        self._buf_lbl = tk.Label(row2, text='0 לוחות', bg=BG, fg='#aaaaaa',
                                  font=FONT_SM, width=8)
        self._buf_lbl.pack(side='left', padx=(0,2))

        self._print_btn = tk.Button(row2, text='🖨 הדפס', command=self._print_buffer,
                  bg=BAR_BG, fg='#aaaaaa', font=FONT_B, relief='flat',
                  padx=10, pady=7, cursor='hand2', activebackground=PAN_BG, state='disabled')
        self._print_btn.pack(side='left', padx=2)

        self._lin_btn = tk.Button(row2, text='💾 LIN', command=self._export_lin,
                  bg=BAR_BG, fg='#aaaaaa', font=FONT_B, relief='flat',
                  padx=10, pady=7, cursor='hand2', activebackground=PAN_BG, state='disabled')
        self._lin_btn.pack(side='left', padx=2)

        self._bbo_btn = tk.Button(row2, text='🌐 BBO', command=self._export_handviewer,
                  bg=BAR_BG, fg='#aaaaaa', font=FONT_B, relief='flat',
                  padx=10, pady=7, cursor='hand2', activebackground=PAN_BG, state='disabled')
        self._bbo_btn.pack(side='left', padx=2)

        tk.Button(row2, text='🗑', command=self._clear_buffer,
                  bg=BAR_BG, fg=CREAM, font=FONT_B, relief='flat',
                  padx=6, pady=7, cursor='hand2', activebackground=PAN_BG).pack(side='left', padx=(2,14))

        tk.Button(row2, text='📚 שיעורים', command=self._open_lessons,
                  bg=BAR_BG, fg=CREAM, font=FONT_B, relief='flat',
                  padx=12, pady=7, cursor='hand2', activebackground=PAN_BG).pack(side='left', padx=2)

        tk.Button(row2, text='אפס', command=self._reset,
                  bg=BAR_BG, fg=CREAM, font=FONT_B, relief='flat',
                  highlightbackground=CREAM, highlightthickness=1,
                  padx=12, pady=7, cursor='hand2', activebackground=PAN_BG).pack(side='left', padx=2)

    def _refresh_dealer_buttons(self):
        current = self.var_dealer.get()
        for v, btn in self._dealer_buttons.items():
            active = (v == current)
            if active:
                btn.config(bg=GOLD, fg=BG, font=FONT_B)
            else:
                btn.config(bg=PAN_BG, fg='#4f3d7a', font=FONT_SM)

    def _set_dealer(self, dealer):
        self.var_dealer.set(dealer)
        self._refresh_dealer_buttons()

    def _deal(self):
        n = self.var_boards.get()
        dealer = self.var_dealer.get()

        # כשאין דילר מפורש — השתמש בפותח המוגדר (בד"כ N); אחרת הסבב N/E/S/W
        # גורם לבורד 2 לקבל dealer='E' → S מכריז לפני N → ההכרזה שגויה
        if dealer == '—':
            opener = next((p for p in ('N','S','E','W') if pState[p]['mode'] == 'opener'), 'N')
            dealer = opener

        # שותף הדילר מקבל 6-15 נק' אם לא הוגדר אחרת
        partner = PARTNER.get(dealer)
        restored = None
        if partner and pState[partner]['mode'] == 'free':
            restored = (pState[partner]['hcpMin'], pState[partner]['hcpMax'])
            pState[partner]['hcpMin'] = 6
            pState[partner]['hcpMax'] = 15

        boards = []
        for _ in range(n):
            h = deal_one_board()
            if h is None:
                if restored:
                    pState[partner]['hcpMin'], pState[partner]['hcpMax'] = restored
                messagebox.showerror('שגיאה', 'לא נמצאה חלוקה. נסה להקל על האילוצים.')
                return
            boards.append(h)

        if restored:
            pState[partner]['hcpMin'], pState[partner]['hcpMax'] = restored

        self._board_buffer.extend(boards)
        self._buffer_dealer = dealer
        self._update_buffer_ui()

    def _update_buffer_ui(self):
        n = len(self._board_buffer)
        if n == 0:
            self._buf_lbl.config(text='0 לוחות', fg='#aaaaaa')
            self._print_btn.config(state='disabled', fg='#aaaaaa')
            self._lin_btn.config(state='disabled', fg='#aaaaaa')
            self._bbo_btn.config(state='disabled', fg='#aaaaaa')
        else:
            self._buf_lbl.config(text=f'{n} לוחות', fg=GOLD)
            self._print_btn.config(state='normal', fg=CREAM)
            self._lin_btn.config(state='normal', fg=CREAM)
            self._bbo_btn.config(state='normal', fg=CREAM)

    def _export_lin(self):
        if not self._board_buffer:
            return
        path = filedialog.asksaveasfilename(
            title='ייצוא לוחות ל-LIN',
            defaultextension='.lin',
            initialfile='boards.lin',
            filetypes=[('LIN', '*.lin'), ('הכול', '*.*')])
        if not path:
            return
        try:
            text = lin_export(self._board_buffer, self._buffer_dealer)
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
        except Exception as e:
            messagebox.showerror('שגיאה', f'הייצוא נכשל.\n{e}')
            return
        # המאגר לא מתרוקן — כדי שאפשר יהיה גם לייצא וגם להדפיס את אותם לוחות
        messagebox.showinfo('ייצוא', f'{len(self._board_buffer)} לוחות נשמרו.')

    def _export_handviewer(self):
        if not self._board_buffer:
            return
        path = filedialog.asksaveasfilename(
            title='ייצוא לוחות ל-BBO HandViewer',
            defaultextension='.html',
            initialfile='boards-bbo.html',
            filetypes=[('דף HTML', '*.html'), ('הכול', '*.*')])
        if not path:
            return
        try:
            html = handviewer_page(self._board_buffer, self._buffer_dealer)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            webbrowser.open('file:///' + os.path.abspath(path).replace('\\', '/'))
        except Exception as e:
            messagebox.showerror('שגיאה', f'הייצוא נכשל.\n{e}')
            return
        # המאגר לא מתרוקן — כדי שאפשר גם לייצא וגם להדפיס את אותם לוחות

    def _print_buffer(self):
        if not self._board_buffer:
            return
        open_print(self._board_buffer, self._buffer_dealer)
        self._board_buffer = []
        self._update_buffer_ui()

    def _clear_buffer(self):
        self._board_buffer = []
        self._update_buffer_ui()

    def _open_lessons(self):
        if hasattr(self, '_lessons_win') and self._lessons_win and self._lessons_win.winfo_exists():
            self._lessons_win.lift()
            return
        self._lessons_win = LessonsPanel(self)

    def _setup_scenario(self, n_open, n_suit, n_str, s_str, s_type, s_suit):
        """מגדיר pST לתרחיש בודד (פותח N + משיב S) — ללא רענון UI/דילר.
        לב הלוגיקה המשותפת ל-_apply_lesson ול-_make_worksheet."""
        for p in 'NESW':
            pState[p] = init_state()

        n = pState['N']
        n['mode'] = 'opener'; n['openKey'] = n_open; n['openSuit'] = n_suit
        n['openType'] = n_open; n['strengthKey'] = n_str; n['_pendingSuit'] = None

        if n_open == 'weak2':
            n['hcpMin'] = 6;  n['hcpMax'] = 9
            n['type'] = 'free'; n['commands'] = f'6{n_suit}|hcp5+{n_suit}'  # בדיוק 6, 5 HCP בצבע
        elif n_open == '2club':
            n['hcpMin'] = 23; n['hcpMax'] = 37
            n['type'] = 'free'; n['commands'] = ''
        elif n_open == '2nt_op':
            n['hcpMin'] = 20; n['hcpMax'] = 22
            n['type'] = 'balanced'; n['commands'] = ''
        else:
            recompute_opener('N')

        s = pState['S']
        s['mode'] = 'responder'; s['openSuit'] = n_suit; s['openType'] = n_open
        s['respStrength'] = s_str; s['respType'] = s_type; s['respSuit'] = s_suit

        if n_open == '2club' and s_str is None:
            s['hcpMin'] = 0; s['hcpMax'] = 6  # מנוע: pts<=6 → 2♦ שלילי
            s['type'] = 'free'; s['commands'] = ''
        else:
            recompute_responder('S')

    def _apply_lesson(self, n_open, n_suit, n_str, s_str, s_type, s_suit):
        self._setup_scenario(n_open, n_suit, n_str, s_str, s_type, s_suit)
        # הערה: אין יותר הגבלת נקודות ל-E/W. ההגבלה (E/W≤8) הייתה שריד מעידן
        # ההכרזה האוטומטית (למנוע אוברקול/דאבל). מאחר שההכרזה האוטומטית הוסרה,
        # ההגבלה רק שברה חלוקה כשל-N/S מעט נקודות. היריבים מקבלים את השאר.
        self._set_dealer('N')
        self._refresh_all()

    def _make_worksheet(self, scenarios):
        """דף עבודה: מחלק N לוחות (הבורר) שמתפרשים על רשימת התרחישים בכוחות
        מעורבים — תרחיש שונה לכל לוח (מסתובב). מוסיף למאגר הקיים. פותח=N."""
        n_boards = self.var_boards.get()
        dealer = self.var_dealer.get()
        if dealer not in 'NESW':
            dealer = 'N'
        order = ['N', 'E', 'S', 'W']; off = order.index(dealer)
        # תרחישים מעורבים אקראית עם כיסוי מלא
        pool = []
        while len(pool) < n_boards:
            sc = list(scenarios); random.shuffle(sc); pool.extend(sc)
        boards = []
        global _WS_MODE
        _WS_MODE = True   # מפעיל את פילטרי דף-העבודה (תמיכה≤2, תקרת 6, בלי סינגלטון K/Q)
        try:
            for i in range(n_boards):
                n_open, n_suit, n_str, s_str, s_type, s_suit = pool[i]
                self._setup_scenario(n_open, n_suit, n_str, s_str, s_type, s_suit)
                h = None
                for _ in range(3):             # נסה שוב על תרחיש קשה לפני ויתור
                    h = deal_one_board()
                    if h is not None:
                        break
                if h is None:
                    messagebox.showerror('שגיאה', 'לא נמצאה חלוקה לאחד התרחישים. נסה שוב.')
                    return
                if off:   # סובב כך שהיד הפותחת (N) תשב במושב הדילר הנבחר
                    h = {seat: h[order[(k - off) % 4]] for k, seat in enumerate(order)}
                boards.append(h)
        finally:
            _WS_MODE = False

        self._board_buffer.extend(boards)
        self._buffer_dealer = dealer
        self._refresh_all()
        self._update_buffer_ui()

    def _reset(self):
        for p in 'NESW': pState[p] = init_state()
        self._refresh_all()

    def _refresh_all(self):
        for p in 'NESW': self.panels[p].refresh()


# ── Player Panel ───────────────────────────────────────────────────────────────
class PlayerPanel(tk.Frame):
    def __init__(self, parent, player, app):
        color = PLAYER_COLORS[player]
        super().__init__(parent, bg=PAN_BG,
                         highlightbackground=color, highlightthickness=3,
                         relief='raised', borderwidth=2,
                         width=370, height=250)
        self.pack_propagate(False)
        self.player = player
        self.app    = app
        self.color  = PLAYER_COLORS[player]
        self._draw_top_bar()
        self.body = tk.Frame(self, bg=PAN_BG)
        self.body.pack(fill='both', expand=True)
        self.refresh()

    def _draw_top_bar(self):
        bar = tk.Frame(self, bg=self.color, height=5)
        bar.pack(fill='x')
        header = tk.Frame(self, bg=PAN_BG)
        header.pack(fill='x', padx=8, pady=(4,0))
        tk.Label(header, text=NAMES[self.player], bg=PAN_BG, fg=self.color,
                 font=FONT_B).pack(side='left')
        self.role_lbl = tk.Label(header, text='חופשי', bg='#e7ddfb', fg='#4f3d7a',
                                  font=('Segoe UI',9), padx=6, pady=1)
        self.role_lbl.pack(side='right')

    def refresh(self):
        for w in self.body.winfo_children(): w.destroy()
        st = pState[self.player]

        # Update role tag
        if st['mode']=='opener':
            self.role_lbl.config(text='פותח', bg='#dfe7ff', fg=PLAYER_COLORS['N'])
        elif st['mode']=='responder':
            self.role_lbl.config(text='משיב', bg='#ffe7e7', fg=PLAYER_COLORS['S'])
        else:
            self.role_lbl.config(text='חופשי', bg='#e7ddfb', fg='#4f3d7a')

        if st['mode']=='responder':
            self._build_resp()
        else:
            self._build_opener()
        self._build_status()

    def _build_opener(self):
        p = self.player; st = pState[p]; b = self.body

        if st['openKey'] != 'nt':
            group_label(b, 'כוח', PAN_BG, center=True)
            row = tk.Frame(b, bg=PAN_BG); row.pack(anchor='center')
            for k in ['חלש 12-14','בינוני 15-17','חזק 18-21']:
                styled_btn(row, k, lambda k=k: self._set_strength(k),
                           active=st['strengthKey']==k, w=11).pack(side='left', padx=2, pady=1)

        group_label(b, 'פתיחה', PAN_BG, center=True)
        row2 = tk.Frame(b, bg=PAN_BG); row2.pack(anchor='center')
        styled_btn(row2, 'פתיחה במיגור', lambda: self._pick_suit('major'),
                   active=st['openKey']=='major', w=11).pack(side='left', padx=2)
        styled_btn(row2, 'פתיחה במינור', lambda: self._pick_suit('minor'),
                   active=st['openKey']=='minor', w=11).pack(side='left', padx=2)
        styled_btn(row2, 'פתיחה NT-1', lambda: self._apply_opening('nt', None),
                   active=st['openKey']=='nt', w=11).pack(side='left', padx=2)
        # מיגור ומינור — שניהם גנריים (בלי בורר צבע). לכן אין יותר בורר ♣/♦.

    def _build_resp(self):
        p = self.player; st = pState[p]; b = self.body
        partner_type = pState[PARTNER[p]]['openType']
        open_suit    = pState[PARTNER[p]]['openSuit']

        group_label(b, 'כוח משיב', PAN_BG, center=True)
        row = tk.Frame(b, bg=PAN_BG); row.pack(anchor='center')
        if partner_type in ('nt','2nt_op'):
            strength_keys = list(STRENGTH_RESP_NT.keys())
        elif partner_type == 'minor':
            strength_keys = list(STRENGTH_RESP_MINOR.keys())
        else:
            strength_keys = list(STRENGTH_RESP.keys())
        nt_kind = partner_type in ('nt','2nt_op')
        for k in strength_keys:
            lbl = nt_resp_label(k) if nt_kind else k
            styled_btn(row, lbl, lambda k=k: self._set_resp_strength(k),
                       active=st['respStrength']==k, resp=True, w=11).pack(side='left', padx=2)

        if partner_type:
            group_label(b, 'סוג תשובה', PAN_BG, center=True)
            row2 = tk.Frame(b, bg=PAN_BG); row2.pack(anchor='center')
            if partner_type=='major':
                supp_lbl = f'תמיכה {open_suit}' if open_suit else 'תמיכה במיגור'
                btns = [('support', supp_lbl, open_suit),
                        ('1nt','1NT',None)]
                if open_suit=='♥': btns.append(('1s','1♠','♠'))
            elif partner_type=='minor':
                supp_lbl = f'תמיכה {open_suit}' if open_suit else 'תמיכה במינור'
                btns = [('1h','1♥','♥'),('1s','1♠','♠'),('1nt','1NT',None),
                        ('supp-minor', supp_lbl, open_suit),('2nt','2NT',None)]
            elif partner_type in ('nt','2nt_op'):
                btns = [('2nt','2NT',None),('stayman','סטיימן','♥'),
                        ('trans-h','טרנספר ♥','♥'),('trans-s','טרנספר ♠','♠')]
            elif partner_type=='weak2':
                btns = [('support', f'תמיכה {open_suit}', open_suit)]
            else:
                btns = []   # 2club ועוד — נקבע דרך שיעורים
            for rt,lbl,suit in btns:
                styled_btn(row2, lbl, lambda rt=rt,s=suit: self._set_resp_type(rt,s),
                           active=st['respType']==rt, resp=True).pack(side='left', padx=2, pady=1)

        tk.Button(b, text='↩ חזור למצב פותח', command=self._clear_resp,
                  bg='#f6effb', fg='#5f4d78', font=('Segoe UI',10), relief='flat',
                  activebackground='#e8e0f8', cursor='hand2').pack(pady=(4,0))

    def _build_status(self):
        st = pState[self.player]; lbl = self._make_label()
        if st['mode']=='opener':     bg,fg = '#e8f0ff', PLAYER_COLORS['N']
        elif st['mode']=='responder' and lbl: bg,fg = '#ffe7e7', PLAYER_COLORS['S']
        else:                        bg,fg = '#efedfa', '#6f607b'
        tk.Label(self.body, text=lbl or 'לא הוגדר', bg=bg, fg=fg,
                 font=FONT_SM, anchor='e', padx=8, pady=4).pack(fill='x', padx=8, pady=(4,6))

    def _make_label(self):
        st = pState[self.player]
        if st['mode']=='opener':
            if st['openKey']=='nt':
                return f"פתיחה 1NT — {cfg['ntMin']}-{cfg['ntMax']} נקודות"
            if st['openKey']=='major' and not st['openSuit']:
                sMin,sMax = STRENGTH_OPENER.get(st['strengthKey'],(12,21))
                return f"פתיחה במיגור — {cfg['majorLen']}+ קלפים, {sMin}-{sMax} נק'"
            if st['openKey']=='minor' and not st['openSuit']:
                sMin,sMax = STRENGTH_OPENER.get(st['strengthKey'],(12,21))
                return f"פתיחה במינור — {cfg['minorLen']}+ קלפים, {sMin}-{sMax} נק'"
            if st['openKey'] in ('major','minor') and st['openSuit']:
                minLen = cfg['majorLen'] if st['openKey']=='major' else cfg['minorLen']
                sMin,sMax = STRENGTH_OPENER.get(st['strengthKey'],(12,21))
                return f"פתיחה {st['openSuit']} — {minLen}+ קלפים, {sMin}-{sMax} נק'"
            if st['strengthKey']:
                sMin,sMax = STRENGTH_OPENER[st['strengthKey']]
                return f"כוח פותח {sMin}-{sMax} נקודות"
        if st['mode']=='responder':
            rsv = st.get('respStrength')
            if rsv in STRENGTH_RESP_NT:
                rsv = nt_resp_label(rsv)
            parts = [x for x in [rsv, st.get('respType')] if x]
            return ' | '.join(parts)
        return ''

    # ── Actions ────────────────────────────────────────────────────────────────
    def _set_strength(self, key):
        st = pState[self.player]
        st['strengthKey'] = None if st['strengthKey']==key else key
        st['mode'] = 'opener' if (st['strengthKey'] or st['openKey']) else 'free'
        recompute_opener(self.player); self.refresh()

    def _pick_suit(self, suit_type):
        # מיגור ומינור — פתיחה גנרית ישירה, בלי לשאול איזו סדרה
        self._apply_opening(suit_type, None)

    def _apply_opening(self, open_type, suit):
        p = self.player; partner = PARTNER[p]; st = pState[p]
        st['openKey']=open_type; st['openSuit']=suit; st['openType']=open_type
        st['_pendingSuit']=None; st['mode']='opener'
        recompute_opener(p)
        pState[partner].update(init_state())
        pState[partner]['mode']='responder'
        pState[partner]['openSuit']=suit; pState[partner]['openType']=open_type
        # מיגור גנרי: המשיב מוגדר אוטומטית לתמיכה במיגור שהפותח יפתח
        if open_type == 'major' and suit is None:
            pState[partner]['respType'] = 'support'
        self.app._set_dealer(p)   # דילר = הפותח שנבחר
        self.refresh(); self.app.panels[partner].refresh()

    def _set_resp_strength(self, key):
        st = pState[self.player]
        st['respStrength'] = None if st['respStrength']==key else key
        recompute_responder(self.player); self.refresh()

    def _set_resp_type(self, rt, suit):
        st = pState[self.player]
        st['respType']=rt; st['respSuit']=suit
        recompute_responder(self.player); self.refresh()

    def _clear_resp(self):
        p = self.player; partner = PARTNER[p]
        pState[p] = init_state()
        for k in ('openKey','openSuit','openType','_pendingSuit'):
            pState[partner][k] = None
        pState[partner]['mode'] = 'free'
        recompute_opener(partner)
        self.refresh(); self.app.panels[partner].refresh()


if __name__ == '__main__':
    app = App()
    app.mainloop()
