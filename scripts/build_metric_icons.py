"""Icons for the Bometer and The Stack.

Every mark is checked at 96px AND 24px, because an icon that only works large is
not an icon. Three drafts failed that test and were rebuilt: a flatline made of
six thin bars turned to mush, a single rule read as a dash rather than a page,
and a three-part "scale ladder" was unreadable small. The survivors use at most
two elements and no text -- a numeral at 24px is a smudge.
"""
import os, math
NAVY="#051954"; STEEL="#2c4a6e"; RUST="#b83a1e"; GOLD="#c9962a"; MUT="#6b5e4a"; CRM="#f5f0e8"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"assets","icons")
os.makedirs(OUT, exist_ok=True)

def wrap(body, vb=64):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb} {vb}" width="{vb}" height="{vb}">'
            + body + '</svg>')

def gauge(frac, needle_col=RUST, label=True):
    """Classic dial: snooze on the left, nail-biter on the right."""
    cx,cy,r=32,40,24
    p=[]
    # arc
    def pt(t):  # t 0..1 across a 180-degree sweep
        a=math.pi*(1-t); return cx+r*math.cos(a), cy-r*math.sin(a)
    x0,y0=pt(0); x1,y1=pt(1)
    p.append(f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{STEEL}" stroke-width="4.5" stroke-linecap="round"/>')
    # ticks
    for t in (0,.25,.5,.75,1):
        a=math.pi*(1-t)
        p.append(f'<line x1="{cx+(r-7)*math.cos(a):.1f}" y1="{cy-(r-7)*math.sin(a):.1f}" x2="{cx+(r-3)*math.cos(a):.1f}" y2="{cy-(r-3)*math.sin(a):.1f}" stroke="{MUT}" stroke-width="1.6"/>')
    a=math.pi*(1-frac)
    p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+(r-6)*math.cos(a):.1f}" y2="{cy-(r-6)*math.sin(a):.1f}" stroke="{needle_col}" stroke-width="3.4" stroke-linecap="round"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="{NAVY}"/>')
    return "".join(p)

def week(filled):
    """Six games, the unit a fan actually lives. Filled = still in doubt."""
    p=[]; w=15; g=3.5; x0=(64-(3*w+2*g))/2
    for i in range(6):
        col=i%3; row=i//3
        x=x0+col*(w+g); y=16+row*(w+g)
        on = i < filled
        p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{w}" rx="2.5" '
                 f'fill="{RUST if on else "none"}" stroke="{RUST if on else MUT}" stroke-width="2"/>')
    return "".join(p)

def stack(n, tree=False):
    """Sheets in profile. n sheets drawn; tree adds a trunk behind."""
    p=[]
    if tree:
        p.append(f'<rect x="29.5" y="38" width="5" height="16" rx="1.5" fill="{NAVY}"/>')
        p.append(f'<circle cx="32" cy="26" r="15" fill="{NAVY}"/>')
        p.append(f'<circle cx="21" cy="33" r="8.5" fill="{NAVY}"/>')
        p.append(f'<circle cx="43" cy="33" r="8.5" fill="{NAVY}"/>')
        return "".join(p)
    if n==1:
        p.append(f'<path d="M20,12 H37 L46,21 V52 H20 Z" fill="none" stroke="{NAVY}" stroke-width="2.6" stroke-linejoin="round"/>')
        p.append(f'<path d="M37,12 V21 H46" fill="none" stroke="{NAVY}" stroke-width="2.6" stroke-linejoin="round"/>')
        return "".join(p)
    base=52; h=4.2
    for i in range(n):
        y=base-i*h
        sk=1.6*((i%2)-0.5)
        p.append(f'<rect x="{16+sk:.1f}" y="{y-h+1:.1f}" width="32" height="{h-0.8:.1f}" rx="1" fill="none" stroke="{NAVY}" stroke-width="1.9"/>')
    return "".join(p)

def flatline():
    """Three weeks, one height, and a dashed line saying the level never moves.
    Six thin bars turned to mush at 24px; three fat ones survive."""
    p=[]; base=48; top=22
    for x in (12,27,42):
        p.append(f'<rect x="{x}" y="{top}" width="11" height="{base-top}" rx="1.6" fill="{STEEL}"/>')
    p.append(f'<line x1="6" y1="{top}" x2="58" y2="{top}" stroke="{RUST}" stroke-width="3.4" stroke-dasharray="7 4" stroke-linecap="round"/>')
    p.append(f'<line x1="6" y1="{base}" x2="58" y2="{base}" stroke="{NAVY}" stroke-width="2.6"/>')
    return "".join(p)

def ladder():
    """The scale in one mark: a sheet, and the tree it came from. Anything more
    than two elements stops reading at 24px."""
    p=[f'<path d="M8,20 H22 L29,27 V50 H8 Z" fill="none" stroke="{NAVY}" stroke-width="2.6" stroke-linejoin="round"/>']
    p.append(f'<path d="M22,20 V27 H29" fill="none" stroke="{NAVY}" stroke-width="2.6" stroke-linejoin="round"/>')
    p.append(f'<rect x="45" y="38" width="4.5" height="14" rx="1.4" fill="{NAVY}"/>')
    p.append(f'<circle cx="47.2" cy="28" r="11" fill="{NAVY}"/>')
    return "".join(p)

ICONS={
 "stack-ladder":       ladder(),
 "bometer-dial-low":   gauge(0.18),
 "bometer-dial-mid":   gauge(0.50),
 "bometer-dial-high":  gauge(0.88),
 "bometer-flatline":   flatline(),
 "fanweek-0of6":       week(0),
 "fanweek-2of6":       week(2),
 "fanweek-5of6":       week(5),
 "stack-page":         stack(1),
 "stack-ream":         stack(7),
 "stack-tree":         stack(0, tree=True),
}
for n,b in ICONS.items():
    open(os.path.join(OUT,n+".svg"),"w").write(wrap(b))
print(f"{len(ICONS)} icons")
