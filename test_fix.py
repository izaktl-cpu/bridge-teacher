# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\bridge-teacher1')
from bidding_engine import compute_auction, hcp

cfg = {'majorLen':5,'ntMin':15,'ntMax':17,'minorLen':3}

def make_hand(spades='', hearts='', diamonds='', clubs=''):
    hand = []
    for suit, cards in [('♠',spades),('♥',hearts),('♦',diamonds),('♣',clubs)]:
        for r in cards:
            hand.append({'s':suit,'r':r})
    return hand

# הדוגמה מהצילום
north = make_hand(spades='7', hearts='AKQ32', diamonds='AQ76', clubs='KT5')
south = make_hand(spades='AKQ', hearts='T8', diamonds='K9532', clubs='AQ8')
east  = make_hand(spades='JT9', hearts='J9764', diamonds='4', clubs='J964')
west  = make_hand(spades='865432', hearts='5', diamonds='JT8', clubs='732')

hands = {'N': north, 'E': east, 'S': south, 'W': west}

print(f"N: {hcp(north)} כבוד | S: {hcp(south)} כבוד | סה\"כ: {hcp(north)+hcp(south)}")

auction = compute_auction(hands, 'N', cfg)
print("הכרזה:", ' - '.join(auction))
