#!/usr/bin/env python3
"""Prediction-market prices for the World Series, from Kalshi and Polymarket.

    python3 scripts/fetch_markets.py            # writes data/markets-ws.json
    python3 scripts/fetch_markets.py --dry-run

BOTH ARE OPEN. Neither needs a key for read access, which is worth knowing
because both sit behind a login in a browser:

  Polymarket  gamma-api.polymarket.com/events?tag_slug=mlb    -- prices inline
  Kalshi      api.elections.kalshi.com/trade-api/v2           -- see the catch

THE KALSHI CATCH, so nobody re-derives it. The /markets LIST endpoint returns
every club with last_price, yes_bid and yes_ask all set to null. It looks like
the data is gated. It is not: the SINGLE-market endpoint /markets/{ticker}
returns a full two-sided quote without any credential. So the price of thirty
clubs costs thirty calls rather than one. The series ticker is KXMLB, titled
"World Series"; KXMLBWS exists and is empty.

NEITHER QUOTES ODDS OR A SPREAD. This is the thing worth understanding about
them. A sportsbook sells you American odds (-150) or a spread (-3.5), both of
which bake in the house margin and neither of which is a probability. These two
sell a binary contract that pays $1 if the thing happens, so the PRICE IS THE
PROBABILITY, in cents, directly. No conversion, no de-vigging.

You can see the difference by adding a market up. A bookmaker's futures board
sums to 115-130% -- that overround is the margin. These two sum to about 101%,
because nobody is taking the other side as a business; buyers and sellers are
matched, and the small excess is the bid-ask spread rather than a fee.
"""
import argparse
import datetime
import json
import os
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "markets-ws.json")
HDR = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
GAMMA = "https://gamma-api.polymarket.com"

# The two venues abbreviate differently; map both onto one club name.
ALIAS = {
    "Los Angeles D": "Dodgers", "Los Angeles Dodgers": "Dodgers",
    "Los Angeles A": "Angels", "Los Angeles Angels": "Angels",
    "New York Y": "Yankees", "New York Yankees": "Yankees",
    "New York M": "Mets", "New York Mets": "Mets",
    "Chicago C": "Cubs", "Chicago Cubs": "Cubs",
    "Chicago WS": "White Sox", "Chicago White Sox": "White Sox",
    "Milwaukee": "Brewers", "Milwaukee Brewers": "Brewers",
    "Tampa Bay": "Rays", "Tampa Bay Rays": "Rays",
    "Atlanta": "Braves", "Atlanta Braves": "Braves",
    "Philadelphia": "Phillies", "Philadelphia Phillies": "Phillies",
    "Boston": "Red Sox", "Boston Red Sox": "Red Sox",
    "Houston": "Astros", "Houston Astros": "Astros",
    "Cleveland": "Guardians", "Cleveland Guardians": "Guardians",
    "Seattle": "Mariners", "Seattle Mariners": "Mariners",
    "Detroit": "Tigers", "Detroit Tigers": "Tigers",
    "Toronto": "Blue Jays", "Toronto Blue Jays": "Blue Jays",
    "Texas": "Rangers", "Texas Rangers": "Rangers",
    "Baltimore": "Orioles", "Baltimore Orioles": "Orioles",
    "Kansas City": "Royals", "Kansas City Royals": "Royals",
    "Minnesota": "Twins", "Minnesota Twins": "Twins",
    "Athletics": "Athletics", "Oakland Athletics": "Athletics",
    "San Diego": "Padres", "San Diego Padres": "Padres",
    "San Francisco": "Giants", "San Francisco Giants": "Giants",
    "Arizona": "Diamondbacks", "Arizona Diamondbacks": "Diamondbacks",
    "Colorado": "Rockies", "Colorado Rockies": "Rockies",
    "St. Louis": "Cardinals", "St. Louis Cardinals": "Cardinals",
    "Cincinnati": "Reds", "Cincinnati Reds": "Reds",
    "Pittsburgh": "Pirates", "Pittsburgh Pirates": "Pirates",
    "Washington": "Nationals", "Washington Nationals": "Nationals",
    "Miami": "Marlins", "Miami Marlins": "Marlins",
}
norm = lambda s: ALIAS.get((s or "").strip(), (s or "").strip())


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=45))


def cents(v):
    """Kalshi has returned both cents and dollars across field names."""
    if v is None:
        return None
    v = float(v)
    return v / 100 if v > 1 else v


def kalshi():
    out = {}
    ms = get(f"{KALSHI}/markets?series_ticker=KXMLB&limit=60&status=open").get("markets", [])
    for m in ms:
        try:
            d = get(f"{KALSHI}/markets/{m['ticker']}")["market"]
        except Exception:
            continue
        bid = cents(d.get("yes_bid_dollars") or d.get("yes_bid"))
        ask = cents(d.get("yes_ask_dollars") or d.get("yes_ask"))
        mid = (bid + ask) / 2 if bid is not None and ask is not None else cents(d.get("last_price"))
        if mid is None:
            continue
        out[norm(d.get("yes_sub_title"))] = dict(
            bid=bid, ask=ask, mid=round(mid, 4),
            spread=round(ask - bid, 4) if (bid is not None and ask is not None) else None)
        time.sleep(0.05)
    return out


def polymarket():
    out, meta = {}, {}
    for e in get(f"{GAMMA}/events?closed=false&limit=60&tag_slug=mlb"):
        if "World Series" not in (e.get("title") or ""):
            continue
        meta = dict(volume=float(e.get("volume") or 0), liquidity=float(e.get("liquidity") or 0),
                    title=e.get("title"))
        for m in e.get("markets", []):
            try:
                p = float(json.loads(m["outcomePrices"])[0])
            except Exception:
                continue
            nm = (m.get("groupItemTitle") or m.get("question", ""))
            out[norm(nm)] = dict(price=round(p, 4),
                                 bid=float(m["bestBid"]) if m.get("bestBid") else None,
                                 ask=float(m["bestAsk"]) if m.get("bestAsk") else None)
        break
    return out, meta


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    k = kalshi()
    p, pmeta = polymarket()
    both = sorted(set(k) & set(p), key=lambda t: -p[t]["price"])
    ks, ps = sum(v["mid"] for v in k.values()), sum(v["price"] for v in p.values())

    print(f"  Kalshi {len(k)} clubs, book sums to {ks*100:.1f}%")
    print(f"  Polymarket {len(p)} clubs, book sums to {ps*100:.1f}%"
          f"  (volume ${pmeta.get('volume',0):,.0f})")
    print(f"  matched on both: {len(both)}\n")
    print(f"  {'club':<16}{'Kalshi':>9}{'Polymkt':>9}{'gap':>8}{'K spread':>10}")
    tot = 0.0
    for t in both[:12]:
        g = (k[t]["mid"] - p[t]["price"]) * 100
        tot += abs(g)
        print(f"  {t:<16}{k[t]['mid']*100:>8.1f}%{p[t]['price']*100:>8.1f}%{g:>+8.1f}"
              f"{(k[t]['spread'] or 0)*100:>9.1f}c")
    gaps = [abs(k[t]["mid"] - p[t]["price"]) * 100 for t in both]
    print(f"\n  mean absolute disagreement across {len(both)} clubs: {sum(gaps)/len(gaps):.2f} points")
    print(f"  largest: {max(both, key=lambda t: abs(k[t]['mid']-p[t]['price']))}"
          f" {max(gaps):.1f} points")

    if a.dry_run:
        print("\n  dry run, nothing written"); return
    json.dump(dict(fetched=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                   note="Binary contracts priced in probability, not odds or spreads",
                   kalshi=dict(series="KXMLB", book_sum=round(ks, 4), clubs=k),
                   polymarket=dict(book_sum=round(ps, 4), meta=pmeta, clubs=p)),
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT}")


if __name__ == "__main__":
    main()
