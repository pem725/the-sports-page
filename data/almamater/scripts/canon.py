import json, csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wiki import fetch
D = pathlib.Path(__file__).resolve().parent
t={x['school']:x for x in json.load(open(D/'cache/teams.json'))}
ss=sorted({r['school'] for r in csv.DictReader(open(D/'seasons.csv'))})
override = {"Miami":"Miami Hurricanes football","Miami (OH)":"Miami RedHawks football","Hawai'i":"Hawaii Rainbow Warriors football",
 "App State":"Appalachian State Mountaineers football","UL Monroe":"Louisiana–Monroe Warhawks football","Louisiana":"Louisiana Ragin' Cajuns football",
 "San José State":"San Jose State Spartans football","Florida International":"FIU Panthers football","Centenary (LA)":"Centenary Gentlemen football",
 "California-Santa Barbara":"UC Santa Barbara Gauchos football","Washington St. Louis":"Washington University Bears football",
 "Saint Mary's (CA)":"Saint Mary's Gaels football","Sam Houston":"Sam Houston Bearkats football","New York University":"NYU Violets football",
 "Hampden Sydney":"Hampden–Sydney Tigers football","Hardin Simmons":"Hardin–Simmons Cowboys football","Detroit Mercy":"Detroit Titans football",
 "Carlisle":"Carlisle Indians football","Georgia Pre-Flight":"Georgia Pre-Flight Skycrackers football","Iowa Pre-Flight":"Iowa Pre-Flight Seahawks football",
 "North Carolina Pre-Flight":"North Carolina Pre-Flight Cloudbusters football","Great Lakes Navy":"Great Lakes Navy Bluejackets football",
 "Colorado School of Mines":"Colorado Mines Orediggers football","Western Colorado":"Western Colorado Mountaineers football","West Texas":"West Texas A&M Buffaloes football",
 "Washington and Lee":"Washington and Lee Generals football","Washington & Jefferson":"Washington & Jefferson Presidents football"}
cand = {s: override.get(s, f"{s} {t[s]['mascot']} football" if s in t else s+" football") for s in ss}
res = fetch(list(cand.values()))
out = {}
for s,c in cand.items():
    r=res[c]; out[s]=r['title'] if r['text'] else None
    if not r['text']: print("MISSING", s, c)
json.dump(out, open(D/'canon.json','w'), indent=1)
