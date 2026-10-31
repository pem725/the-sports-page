#!/usr/bin/env python3
"""Will baseball stop on December 1, 2026 -- and for how long?

The question (the editor, 2026-10-31): MLB's labor agreement expires December 1,
2026.  Owners have proposed a hard salary cap and floor with a 50/50 revenue
split from 2027; the union (interim executive director Bruce Meyer) rejects any
cap.  Give a specific probability of a work stoppage and of how long it lasts,
as a function of how far apart the two sides are, and say what is at stake.

Data, and only these:
  * Every collective-bargaining negotiation in MLB, the NFL, the NBA and the NHL
    that we could document, 1967-2026, one row each -- INCLUDING the ones that
    ended without a stoppage (a list of stoppages alone is survivorship).  The
    rows are curated by hand below (NEGOTIATIONS) from the sources named in each
    row's `sources` column; the script writes them to negotiations.csv.  Source
    codes are explained in SOURCE_KEY.  Wikipedia is a pointer; every stoppage's
    dates are checked against at least one independent source (CNN Editorial
    Research's "Pro Sports Lockouts and Strikes Fast Facts", the union's own
    history, BLS, contemporaneous AP/CP/CBS reporting), and MLB games-lost
    counts are re-derived from the Lahman Teams table (scheduled minus played).
  * U.S. Bureau of Labor Statistics, "Work stoppages involving 1,000 or more
    workers, 1993-present" (bls.gov/web/wkstp/monthly-listing.xlsx): begin and
    end dates of every major U.S. stoppage.  BLS blocks anonymous robots; a
    User-Agent naming a contact address is accepted.
  * Lahman Baseball Database, Teams table (attendance, home games), via the
    Chadwick Baseball Databank.  The chadwickbureau GitHub repo is gone; the
    mirror github.com/xorq-labs/baseballdatabank carries it through 2021 and the
    CRAN `Lahman` package (14.0.0) through 2025.  Cross-checked season by season
    against MLB's own attendance endpoint (statsapi.mlb.com/api/v1/attendance).
  * Money: MLB 2024 revenue $12.1B (Forbes, as reported by CBS Sports
    2025-01-27); 2026 opening-day salaries from the AP payroll study (942
    players, average $5,335,966); the cap proposal from AP (2026-05-28); the
    union's revenue-share claim from Meyer's 2026-06-01 briefing (MLBTR, FOS).
  NO CollegeFootballData calls, no secrets, no numbers taken from a search
  summary.  Everything fetched is cached under ~/.cache/sports-page/stoppages/.

Method
  * Population for P(stoppage): negotiations at the expiration (or reopener) of
    an agreement.  Excluded from the base rate and flagged: first-ever
    agreements, a mid-term strike (MLB 1981), court-settlement agreements that
    replaced no expiring contract (NFL 1993, NBA 1976), early extensions signed
    years ahead (NFL 1998/2002, NHL 2020/2025) -- these are reported as a
    sensitivity, since an early extension is also a negotiation without a
    stoppage.  "Stoppage" = any strike or lockout, including offseason ones that
    cost no games; "games stoppage" = one that cancelled regular-season games.
  * Distance (a), coded by a written rule BEFORE fitting, though by a coder who
    knew the outcomes (stated as a limit):  system = some side's opening demand
    would create a hard cap or fixed revenue split where none existed, turn a
    soft cap into a hard one, or create/abolish free agency or the reserve
    system; adjustment = changing parameters inside the existing system (shares,
    tax rates, thresholds, minimums, pensions, compensation rules); none = a
    renewal with no contested economic demand.  Borderline cases are flagged and
    re-run the other way as a sensitivity.
  * Distance (b): players' share of league revenue under the expiring deal minus
    the owners' first documented proposal, in percentage points.  "unknown"
    wherever a documented pair does not exist.  It exists only for stoppages
    (nobody publishes positions in deals that close quietly), so it can describe
    how long stoppages last, never whether one happens.
  * Wilson 95% intervals for every proportion.  Logistic fit with ONE predictor
    (system change), profile-likelihood 95% interval on the slope.
  * Durations: days = end - start (calendar days; sources quoting "inclusive"
    counts differ by one).  End = the day the stoppage formally ended
    (ratification / lifting of the lockout).
  * BLS hazard: Kaplan-Meier on calendar durations (end - start + 1, BLS end
    dates being the last day idle), ongoing stoppages censored, only stoppages
    BEGINNING 1993 or later (earlier ones in the file are there because they
    were still running in 1993 -- keeping them would over-sample long ones).
  * Forecast: P(stoppage) x P(duration > X | stoppage), uncertainty by Monte
    Carlo from Jeffreys Beta posteriors on each piece.

Traps handled (and reported in analysis.txt)
  * Survivorship: non-stoppage negotiations are rows, not footnotes.
  * Games-lost counts disagree across sources (1994-95: 938 CNN, 948 Wikipedia,
    ~920 from Lahman's scheduled-minus-played).  We report the derived figure.
  * The BLS file left-truncates (see above) and has no MLB/NBA/NHL rows: those
    bargaining units are under 1,000 workers.  Only the NFL 2011 lockout is in
    it, and its dates match.
  * 2021-22: two series were "cancelled" in March 2022 and then made up; zero
    regular-season games were lost (Lahman: all 30 clubs played 162).
  * Attendance after a stoppage is confounded (new parks, expansion, COVID in
    2020-21).  The comparison is descriptive, not causal.

Usage:
  python3 scripts/work_stoppages.py            # fetch if needed, analyze
  python3 scripts/work_stoppages.py --offline  # cache only
  python3 scripts/work_stoppages.py --seed 7 --draws 200000

Outputs: data/stoppages/negotiations.csv, analysis.txt, forecast.txt,
         attendance.csv, bls_hazard.csv
"""
import argparse, csv, datetime as dt, json, math, pathlib, random, re, shutil
import statistics, subprocess, sys, time, urllib.request, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "stoppages"
CACHE = pathlib.Path.home() / ".cache" / "sports-page" / "stoppages"
RAW = CACHE / "raw"
UA_CONTACT = "TheSportsPage-research/1.0 (ideas@thesportspage.net)"
BLS_URL = "https://www.bls.gov/web/wkstp/monthly-listing.xlsx"
TEAMS_URL = "https://raw.githubusercontent.com/xorq-labs/baseballdatabank/master/core/Teams.csv"
STATSAPI = "https://statsapi.mlb.com/api/v1/attendance?leagueId=%d&season=%d"
OFFLINE = False
D = dt.date

# ------------------------------------------------------------------ sources
SOURCE_KEY = {
    "WP": "English Wikipedia article on that dispute (pointer only; revision ids cached)",
    "WP-NFLPA": "Wikipedia, 'NFL Players Association' (history sections)",
    "WP-NFLCBA": "Wikipedia, 'NFL collective bargaining agreement'",
    "WP-MLBPA": "Wikipedia, 'Major League Baseball Players Association'",
    "WP-NBPA": "Wikipedia, 'National Basketball Players Association'",
    "WP-NBACAP": "Wikipedia, 'NBA salary cap' (history)",
    "WP-NHLCBA": "Wikipedia, 'NHL Collective Bargaining Agreement'",
    "CNN": "CNN Editorial Research, 'Pro Sports Lockouts and Strikes Fast Facts' "
           "(2021 and 2024 versions; abc17news.com/?p=1328194, keyt.com/?p=677174)",
    "NBPA": "National Basketball Players Association history, nbpa.com/about",
    "NHLPA": "NHLPA, 'Setting the Record Straight' (nhlpa.com/news/cba-myths-vs-facts), 2012",
    "CP2012": "Canadian Press via The Hockey News, July 2012 ('initial league proposal ... 46 per cent')",
    "NBCS2011": "NBC Sports ProBasketballTalk, 'NBA lockout: BRI is still the elephant in the room', Oct 2011",
    "CBS1994": "CBS Sports, '1994 MLB strike 20th anniversary: who was to blame' (owners' 1994 plan: share 56% -> 50%)",
    "AP2026": "Associated Press, 'MLB owners propose a salary cap for the first time since "
              "baseball's 1994-95 strike', 2026-05-28 (via wtop.com)",
    "MLBTR2026": "MLB Trade Rumors, 'MLBPA's Bruce Meyer comments on league's first economic proposal', 2026-06",
    "FOS2026": "Front Office Sports, 'MLBPA says owners' salary cap would cut player pay by $500M', 2026-06-01",
    "CBS2026": "CBS Sports, 'What Rob Manfred and the MLBPA said about salary cap fight', 2026-10-24",
    "BLS": "BLS work stoppages listing, monthly-listing.xlsx (NFL 2011 row)",
    "LAHMAN": "Lahman Teams table: scheduled minus played games (derived)",
}

# --------------------------------------------------------------- the table
# One row per negotiation.  Fields, in order:
#  id, league, expired (year the agreement expired / was reopened), expiry_date,
#  row_type, stoppage (Y/N/pending), stype, start, end, days_quoted,
#  games_cancelled, postseason_lost, timing, core_issue, dist_a, seeker,
#  borderline, sq_share, owner_open_share, gap_pp, gap_note, sources, notes
# row_type: expiration | reopener | first_agreement | midterm | settlement |
#           early_extension | pending
N_ = None
NEGOTIATIONS = [
 # ---------------------------------------------------------------- MLB
 ("MLB-1967", "MLB", 1967, "", "first_agreement", "N", "", N_, N_, N_, 0, "N", "",
  "first Basic Agreement (minimum salary $6,000 -> $10,000)", "n/a", "", "",
  N_, N_, N_, "", "WP-MLBPA", "first agreement; no prior contract expired; one source"),
 ("MLB-1969", "MLB", 1969, "1969-12-31", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "1970 agreement: grievance arbitration", "adjustment", "players", "",
  N_, N_, N_, "", "WP-MLBPA",
  "one source for the agreement; a spring-1969 pension-plan boycott is not counted as a stoppage by CNN's list of nine"),
 ("MLB-1972P", "MLB", 1972, "1972-03-31", "expiration", "Y", "strike", D(1972,4,1), D(1972,4,13), 13, 86, "N", "in-season",
  "pension-plan contributions", "adjustment", "players", "",
  N_, N_, N_, "", "WP;CNN;LAHMAN",
  "the benefit-plan agreement, not the Basic Agreement; Lahman shortfall 85 vs 86 quoted (normal rainouts muddy it)"),
 ("MLB-1972", "MLB", 1972, "1972-12-31", "expiration", "Y", "lockout", D(1973,2,8), D(1973,2,25), 17, 0, "N", "preseason",
  "salary arbitration", "adjustment", "owners", "",
  N_, N_, N_, "", "WP;CNN", ""),
 ("MLB-1975", "MLB", 1975, "1975-12-31", "expiration", "Y", "lockout", D(1976,3,1), D(1976,3,17), 17, 0, "N", "preseason",
  "free agency after the Messersmith-McNally decision", "system", "both", "",
  N_, N_, N_, "", "WP;CNN", "reserve system replaced by free agency"),
 ("MLB-1979", "MLB", 1979, "1979-12-31", "expiration", "Y", "strike", D(1980,4,1), D(1980,4,8), 8, 0, "N", "preseason",
  "free-agent compensation", "adjustment", "owners", "",
  N_, N_, N_, "", "WP;CNN", "last 8 days of spring training; compensation issue deferred to 1981"),
 ("MLB-1981", "MLB", 1980, "", "midterm", "Y", "strike", D(1981,6,12), D(1981,7,31), 50, 712, "N", "in-season",
  "free-agent compensation (reopened from 1980)", "adjustment", "owners", "",
  N_, N_, N_, "", "WP;CNN;LAHMAN",
  "MID-TERM strike: excluded from P(stoppage at expiration), included in durations; Lahman shortfall 712; split-season postseason added, not lost"),
 ("MLB-1984", "MLB", 1984, "1984-12-31", "expiration", "Y", "strike", D(1985,8,6), D(1985,8,7), 2, 2, "N", "in-season",
  "pension contributions, arbitration eligibility", "adjustment", "both", "",
  N_, N_, N_, "", "WP;CNN;LAHMAN",
  "games lost: WP 2 of 25 not made up; CNN 0; Lahman shortfall 3 incl. normal rainouts"),
 ("MLB-1989", "MLB", 1989, "1989-12-31", "expiration", "Y", "lockout", D(1990,2,15), D(1990,3,18), 32, 0, "N", "preseason",
  "owners' revenue-participation plan with a club salary cap (48% of gate+broadcast)", "system", "owners", "",
  N_, N_, N_, "owners proposed 48% of gate and broadcast revenue; players' existing share not documented",
  "WP;CNN;LAHMAN", "Opening Day moved a week; season extended, full 162 played (Lahman)"),
 ("MLB-1993", "MLB", 1993, "1993-12-31", "expiration", "Y", "strike", D(1994,8,12), D(1995,4,2), 232, 920, "Y", "in-season",
  "owners' salary cap, 50/50 revenue split, end of arbitration", "system", "owners", "",
  56, 50, 6, "CBS1994: 56% -> 50%; a 1994 NYT figure of 58% (seen only in a search summary, not confirmed) would make it 8",
  "WP;CNN;CBS1994;AP2026;LAHMAN",
  "games lost: CNN 938, WP 948, Lahman scheduled-minus-played 920 (668 in 1994 + 252 in 1995's 144-game schedule)"),
 ("MLB-2001", "MLB", 2001, "2001-11", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "revenue sharing, luxury tax, contraction", "adjustment", "owners", "",
  N_, N_, N_, "", "CNN;WP-MLBPA", "deal Aug 30, 2002, hours before a strike deadline; 2002 played on old terms"),
 ("MLB-2006", "MLB", 2006, "2006-12-19", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "renewal", "adjustment", "", "",
  N_, N_, N_, "", "WP-MLBPA", "agreed during the 2006 postseason; one source"),
 ("MLB-2011", "MLB", 2011, "2011-12-11", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "HGH testing, playoff expansion, Astros to AL", "adjustment", "", "",
  N_, N_, N_, "", "CNN", "signed Nov 22, 2011"),
 ("MLB-2016", "MLB", 2016, "2016-12-01", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "renewal", "adjustment", "", "",
  N_, N_, N_, "", "CNN", "deal Nov 30, 2016, hours before expiry"),
 ("MLB-2021", "MLB", 2021, "2021-12-01", "expiration", "Y", "lockout", D(2021,12,2), D(2022,3,10), 99, 0, "N", "offseason",
  "pre-arbitration pay, luxury tax, tanking", "adjustment", "both", "Y",
  N_, N_, N_, "", "WP;CNN;LAHMAN",
  "BORDERLINE: owners' first proposal set a $100M hard payroll minimum and narrower payroll ranges; 2 series cancelled Mar 1 then made up -- all 30 clubs played 162 (Lahman)"),
 ("MLB-2026", "MLB", 2026, "2026-12-01", "pending", "pending", "", N_, N_, N_, N_, "", "offseason",
  "owners' hard cap $245.3M / floor $171.2M, 50/50 split, centralized local media", "system", "owners", "",
  N_, 50, N_,
  "union: 2026 player share 'well over 50%' on MLB's own definitions; union says players would have made ~$500M less in 2026 under the plan (~4 points of $12.1B revenue, DERIVED, not a documented position)",
  "AP2026;MLBTR2026;FOS2026;CBS2026", "CBS (Oct 24) prints the cap as $243.5M; AP's $245.3M is used"),
 # ---------------------------------------------------------------- NFL
 ("NFL-1968", "NFL", 1968, "", "first_agreement", "Y", "strike+lockout", D(1968,7,3), D(1968,7,14), 11, 0, "N", "preseason",
  "first CBA: pension, minimum salaries", "n/a", "players", "",
  N_, N_, N_, "", "WP-NFLPA;WP-NFLCBA;CNN", "end Jul 14 (WP) vs Jul 15 (CNN); first agreement, excluded from base rate"),
 ("NFL-1970", "NFL", 1970, "", "expiration", "Y", "strike+lockout", D(1970,7,3), D(1970,8,3), N_, 0, "N", "preseason",
  "pension, minimums, injury arbitration (post-merger)", "adjustment", "players", "",
  N_, N_, N_, "", "WP-NFLPA;CNN",
  "start Jul 3 (WP-NFLPA) vs Jul 13 (CNN); WP-NFLCBA says 'four days' -- sources disagree, preseason games not lost"),
 ("NFL-1974", "NFL", 1974, "1974", "expiration", "Y", "strike", D(1974,7,1), D(1974,8,10), 41, 0, "N", "preseason",
  "'No Freedom, No Football': abolish Rozelle Rule, option clause, draft", "system", "players", "",
  N_, N_, N_, "", "WP-NFLPA;WP-NFLCBA;CNN", "players returned without a CBA; agreement only in 1977 after Mackey"),
 ("NFL-1982", "NFL", 1982, "1982-07-15", "expiration", "Y", "strike", D(1982,9,21), D(1982,11,16), 57, 98, "N", "in-season",
  "players' wage scale at 55% of gross revenue", "system", "players", "",
  N_, N_, N_, "players sought 55% of gross; owners' position was no fixed share -- no documented pair",
  "WP-NFLPA;WP-NFLCBA;CNN", "98 = 7 lost weeks x 14 games (16 -> 9 game season, 28 clubs), DERIVED; playoffs expanded, not lost"),
 ("NFL-1987", "NFL", 1987, "1987-08-31", "expiration", "Y", "strike", D(1987,9,22), D(1987,10,15), 24, 14, "N", "in-season",
  "free agency", "system", "players", "",
  N_, N_, N_, "", "WP-NFLPA;WP-NFLCBA;CNN",
  "1 week cancelled (14 games, DERIVED from 28 clubs); 3 weeks of replacement games counted; no CBA again until 1993"),
 ("NFL-1993", "NFL", 1993, "", "settlement", "N", "", N_, N_, N_, 0, "N", "",
  "salary cap tied to revenue + free agency (White settlement)", "system", "both", "",
  N_, N_, N_, "", "WP-NFLCBA", "no contract had expired (none in force since 1987); excluded from base rate"),
 ("NFL-1998", "NFL", 1998, "", "early_extension", "N", "", N_, N_, N_, 0, "N", "",
  "extension", "none", "", "", N_, N_, N_, "", "WP-NFLCBA", "early extension; one source"),
 ("NFL-2002", "NFL", 2002, "", "early_extension", "N", "", N_, N_, N_, 0, "N", "",
  "extension", "none", "", "", N_, N_, N_, "", "WP-NFLCBA", "early extension; one source"),
 ("NFL-2006", "NFL", 2006, "2007", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "more revenue counted in the cap; uncapped-year deadline", "adjustment", "players", "",
  N_, N_, N_, "", "WP-NFLCBA;CNN", "extended Mar 8, 2006 with the uncapped 2007 season looming"),
 ("NFL-2011", "NFL", 2011, "2011-03-11", "expiration", "Y", "lockout", D(2011,3,12), D(2011,7,25), 136, 0, "N", "offseason",
  "owners: extra $1B credit off the top, 18 games, rookie scale", "adjustment", "owners", "Y",
  57, N_, N_, "players had 57% of revenue after a ~$1B credit; owners' opening offer not documented as a share",
  "WP;CNN;BLS", "BORDERLINE (revenue-base restructure); only the Hall of Fame Game lost; BLS dates match"),
 ("NFL-2020", "NFL", 2020, "2021-03", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "17 games, share 47% -> 48%", "adjustment", "owners", "",
  N_, N_, N_, "", "WP-NFLCBA;WP-NFLPA", "signed March 2020, a season early"),
 # ---------------------------------------------------------------- NBA
 ("NBA-1967", "NBA", 1967, "", "first_agreement", "N", "", N_, N_, N_, 0, "N", "",
  "first agreement: exhibition pay, pension", "n/a", "players", "",
  N_, N_, N_, "", "NBPA", "first agreement; excluded"),
 ("NBA-1976", "NBA", 1976, "", "settlement", "N", "", N_, N_, N_, 0, "N", "",
  "Robertson settlement: option clause ended", "system", "players", "",
  N_, N_, N_, "", "NBPA;WP", "court settlement; excluded from base rate"),
 ("NBA-1983", "NBA", 1983, "", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "first salary cap tied to revenue share", "system", "owners", "",
  N_, N_, N_, "", "NBPA;WP-NBPA", "a SYSTEM CHANGE agreed without a stoppage"),
 ("NBA-1988", "NBA", 1988, "1987", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "players' antitrust suit against cap, draft, right of first refusal", "system", "players", "Y",
  N_, N_, N_, "", "NBPA", "BORDERLINE (players' demand pursued through a lawsuit); one source"),
 ("NBA-1994", "NBA", 1994, "1994-06", "expiration", "Y", "lockout", D(1995,7,1), D(1995,9,12), N_, 0, "N", "offseason",
  "luxury tax, rookie scale; union decertification fight", "adjustment", "owners", "",
  N_, N_, N_, "", "WP-NBPA;CNN;NBPA",
  "1994-95 played under a no-strike/no-lockout pledge; end Sep 12 (WP) vs Sep 18 (CNN)"),
 ("NBA-1996", "NBA", 1996, "1996-07", "reopener", "Y", "lockout", D(1996,7,9), D(1996,7,9), 0, 0, "N", "offseason",
  "division of new TV money", "adjustment", "players", "",
  N_, N_, N_, "", "CNN;WP", "lasted hours"),
 ("NBA-1998", "NBA", 1998, "1998-06-30", "reopener", "Y", "lockout", D(1998,7,1), D(1999,1,7), 204, 464, "N", "offseason",
  "owners: hard cap / maximum salaries", "system", "owners", "",
  57, N_, N_, "players took 57% of BRI vs 48% intended; owners' opening share not documented",
  "WP;CNN;NBPA", "end Jan 7 (CNN, ratified) vs Jan 20 (WP, signed); 464 = 29 clubs x 32 games / 2, matches NBPA"),
 ("NBA-2005", "NBA", 2005, "2005-06-30", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "age limit, drug testing, contract length", "adjustment", "owners", "",
  N_, N_, N_, "", "WP;NBPA", ""),
 ("NBA-2011", "NBA", 2011, "2011-06-30", "expiration", "Y", "lockout", D(2011,7,1), D(2011,12,8), 161, 240, "N", "offseason",
  "owners: hard cap, players' share 57% -> 47%", "system", "owners", "",
  57, 47, 10, "WP: owners proposed 57 -> 47, players countered 53; NBCS2011: owners 'started somewhere south of 44' (gap >= 13)",
  "WP;CNN;NBPA;NBCS2011", "240 = 30 clubs x 16 games / 2 (82 -> 66)"),
 ("NBA-2017", "NBA", 2017, "2017", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "renewal (mutual opt-out)", "adjustment", "", "",
  N_, N_, N_, "", "WP-NBACAP", "deal Dec 2016; one source"),
 ("NBA-2023", "NBA", 2023, "2023", "expiration", "N", "", N_, N_, N_, 0, "N", "",
  "second apron, tax changes", "adjustment", "owners", "",
  N_, N_, N_, "", "WP-NBACAP", "one source"),
 # ---------------------------------------------------------------- NHL
 ("NHL-1991", "NHL", 1991, "1991-09-15", "expiration", "Y", "strike", D(1992,4,1), D(1992,4,10), 10, 0, "N", "in-season",
  "playoff bonuses, licensing, free agency", "adjustment", "players", "",
  N_, N_, N_, "", "WP;CNN", "30 games postponed and rescheduled"),
 ("NHL-1993", "NHL", 1993, "1993-09-15", "expiration", "Y", "lockout", D(1994,10,1), D(1995,1,11), 103, 468, "N", "offseason",
  "owners: salary cap / payroll tax", "system", "owners", "",
  N_, N_, N_, "", "WP;CNN;WP-NHLCBA", "1993-94 played without a CBA; 468 = 26 clubs x 36 games / 2"),
 ("NHL-2004", "NHL", 2004, "2004-09-15", "expiration", "Y", "lockout", D(2004,9,16), D(2005,7,22), 310, 1230, "Y", "offseason",
  "owners: 'cost certainty' salary cap", "system", "owners", "",
  76, N_, N_, "players' salaries ~76% of revenue per the league-commissioned Levitt report (disputed by the union); owners' opening share not documented; settled at 54%",
  "WP;CNN;WP-NHLCBA", "entire season and Stanley Cup lost"),
 ("NHL-2012", "NHL", 2012, "2012-09-15", "expiration", "Y", "lockout", D(2012,9,16), D(2013,1,12), 119, 510, "N", "offseason",
  "players' share 57% -> 46%, contract limits", "adjustment", "owners", "",
  57, 46, 11, "CP2012/WP: 57 -> 46; NHLPA: 43 on the old revenue definition (gap 14)",
  "WP;CNN;WP-NHLCBA;CP2012;NHLPA", "framework kept, share cut; CNN quotes 526 games scheduled through Dec 30, WP 510 lost (30 x 34 / 2 = 510)"),
 ("NHL-2020", "NHL", 2020, "", "early_extension", "N", "", N_, N_, N_, 0, "N", "",
  "COVID extension", "none", "", "", N_, N_, N_, "", "WP-NHLCBA", "early extension"),
 ("NHL-2025", "NHL", 2025, "", "early_extension", "N", "", N_, N_, N_, 0, "N", "",
  "84 games, contract length", "adjustment", "", "", N_, N_, N_, "", "WP-NHLCBA", "agreed Jun 27, 2025, a year before expiry"),
]
FIELDS = ["id", "league", "expired", "expiry_date", "row_type", "stoppage", "stype", "start", "end",
          "days_quoted", "games_cancelled", "postseason_lost", "timing", "core_issue", "dist_a", "seeker",
          "borderline", "sq_share", "owner_open_share", "gap_pp", "gap_note", "sources", "notes"]
BASE_TYPES = {"expiration", "reopener"}

# ------------------------------------------------------------------ fetching
def _get(url, path, ua=UA_CONTACT):
    if path.exists():
        return path
    if OFFLINE:
        sys.exit("offline and not cached: %s" % path)
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    if data[:2] != b"PK" and path.suffix == ".xlsx":
        sys.exit("BLS returned HTML (blocked?) for %s" % url)
    path.write_bytes(data)
    time.sleep(1.0)
    return path

def fetch_all():
    RAW.mkdir(parents=True, exist_ok=True)
    (CACHE / "statsapi").mkdir(parents=True, exist_ok=True)
    _get(BLS_URL, RAW / "monthly-listing.xlsx")
    _get(TEAMS_URL, RAW / "Teams.csv")
    lah = RAW / "Teams_Rlahman.csv"
    if not lah.exists() and not OFFLINE and shutil.which("Rscript"):
        lib = CACHE / "Rlib"; lib.mkdir(exist_ok=True)
        subprocess.run(["Rscript", "-e",
            'install.packages("Lahman", lib="%s", repos="https://cloud.r-project.org", quiet=TRUE);'
            'library(Lahman, lib.loc="%s"); write.csv(Teams, "%s", row.names=FALSE)' % (lib, lib, lah)],
            check=False, capture_output=True)
    for yr in range(1975, 2026):
        for lg in (103, 104):
            p = CACHE / "statsapi" / ("att-%d-%d.json" % (lg, yr))
            if not p.exists():
                _get(STATSAPI % (lg, yr), p, ua="TheSportsPage-research/1.0 python-urllib")

# ------------------------------------------------------------- xlsx (stdlib)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
def read_xlsx(path):
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    rows = []
    for r in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter("{%s}row" % NS["m"]):
        row = {}
        for c in r.findall("m:c", NS):
            col = re.match(r"[A-Z]+", c.get("r")).group()
            ci = 0
            for ch in col:
                ci = ci * 26 + ord(ch) - 64
            v = c.find("m:v", NS); t = c.get("t")
            if t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is None:
                val = None
            elif t == "s":
                val = ss[int(v.text)]
            else:
                val = v.text
            row[ci - 1] = val
        if row:
            rows.append([row.get(k) for k in range(max(row) + 1)])
    return rows

def xl_date(s):
    return D(1899, 12, 30) + dt.timedelta(days=int(float(s)))

# -------------------------------------------------------------------- stats
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)

def fmt_p(k, n):
    p, lo, hi = wilson(k, n)
    return "%2d/%-2d = %s  (95%% %s-%s)" % (k, n, sig(p), sig(lo), sig(hi))

def sig(x, d=2):
    """At most two significant digits, as a percentage for probabilities."""
    if x != x:
        return "n/a"
    v = 100 * x
    if v == 0:
        return "0%"
    if v >= 99.5 and v < 100:
        return ">99%"
    if v < 1:
        return "%.1g%%" % v
    return "%s%%" % ("%.2g" % v if v < 100 else "100")

def sig_n(x, d=2):
    if x == 0:
        return "0"
    mag = math.floor(math.log10(abs(x)))
    r = round(x, -mag + d - 1)
    return ("%d" % r) if r >= 10 ** (d - 1) or r == int(r) else ("%.*f" % (max(0, -mag + d - 1), r))

def loglik(b0, b1, xs, ys):
    s = 0.0
    for x, y in zip(xs, ys):
        e = b0 + b1 * x
        s += y * e - math.log1p(math.exp(e)) if e < 30 else y * e - e
    return s

def best_b0(b1, xs, ys):
    b0 = 0.0
    for _ in range(60):
        g = h = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(b0 + b1 * x)))
            g += y - p; h -= p * (1 - p)
        if h == 0:
            break
        step = g / h
        b0 -= step
        if abs(step) < 1e-10:
            break
    return b0

def logistic_profile(xs, ys):
    """MLE of b1 with a profile-likelihood 95% interval (chi2_1 = 3.841)."""
    grid = [i / 100 for i in range(-800, 801)]
    prof = [(b1, loglik(best_b0(b1, xs, ys), b1, xs, ys)) for b1 in grid]
    b1hat, llmax = max(prof, key=lambda t: t[1])
    inside = [b for b, ll in prof if 2 * (llmax - ll) <= 3.841]
    return b1hat, best_b0(b1hat, xs, ys), min(inside), max(inside)

def km(durs, events):
    """Kaplan-Meier: returns sorted (t, S(t)) after each distinct event time."""
    data = sorted(zip(durs, events))
    N = len(data); at_risk = N; S = 1.0; out = [(0, 1.0)]; i = 0
    while i < N:
        t = data[i][0]; d = c = 0
        while i < N and data[i][0] == t:
            d += data[i][1]; c += 1 - data[i][1]; i += 1
        if d:
            S *= 1 - d / at_risk
            out.append((t, S))
        at_risk -= d + c
    return out

def S_at(curve, t):
    s = 1.0
    for tt, ss in curve:
        if tt <= t:
            s = ss
        else:
            break
    return s

def beta_draws(k, n, m, rng):
    return [rng.betavariate(k + 0.5, n - k + 0.5) for _ in range(m)]

def q(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, int(p * len(v)))]

# -------------------------------------------------------------------- build
def build_rows():
    rows = []
    for t in NEGOTIATIONS:
        r = dict(zip(FIELDS, t))
        if r["start"] and r["end"]:
            r["days"] = (r["end"] - r["start"]).days
        else:
            r["days"] = None
        rows.append(r)
    return rows

def write_csv(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    cols = FIELDS[:9] + ["days"] + FIELDS[9:]
    with open(OUT / "negotiations.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r[c] is None else r[c] for c in cols])

def load_bls():
    rows = read_xlsx(RAW / "monthly-listing.xlsx")
    out = []
    for r in rows[2:]:
        if not r or len(r) < 11 or not r[9] or not str(r[9]).replace(".", "").isdigit():
            continue
        start = xl_date(r[9])
        ongoing = not str(r[10] or "").replace(".", "").isdigit()
        end = None if ongoing else xl_date(r[10])
        out.append({"org": r[0], "start": start, "end": end, "workers": r[11]})
    asof = max(x["end"] or x["start"] for x in out)
    for x in out:
        x["event"] = 0 if x["end"] is None else 1
        x["dur"] = ((x["end"] or asof) - x["start"]).days + 1
    return out, asof

def load_attendance():
    lah = RAW / "Teams_Rlahman.csv"
    src = lah if lah.exists() else RAW / "Teams.csv"
    att = defaultdict(lambda: [0, 0, 0, 0])  # attendance, home games, games, clubs
    for r in csv.DictReader(open(src)):
        y = int(r["yearID"])
        if y < 1975:
            continue
        a = att[y]
        a[0] += int(float(r["attendance"] or 0)); a[1] += int(float(r["Ghome"] or 0))
        a[2] += int(float(r["G"])); a[3] += 1
    api = {}
    for y in att:
        tot = opens = 0; ok = True
        for lg in (103, 104):
            p = CACHE / "statsapi" / ("att-%d-%d.json" % (lg, y))
            if not p.exists():
                ok = False; continue
            for rec in json.loads(p.read_text()).get("records", []):
                tot += rec.get("attendanceTotalHome", 0) or 0
                opens += rec.get("openingsTotalHome", 0) or 0
        if ok:
            api[y] = (tot, opens)
    return att, api, src.name

# ----------------------------------------------------------------- analysis
def analyze(rows, args):
    L = []
    P = L.append
    base = [r for r in rows if r["row_type"] in BASE_TYPES]
    stop = lambda rs: sum(r["stoppage"] == "Y" for r in rs)
    games = lambda rs: sum(r["stoppage"] == "Y" and (r["games_cancelled"] or 0) > 0 for r in rs)

    P("WORK STOPPAGES IN THE FOUR MAJOR NORTH AMERICAN LEAGUES -- analysis")
    P("Generated by scripts/work_stoppages.py on %s.  Proportions: Wilson 95%% intervals." % dt.date.today())
    P("")
    P("1. COVERAGE")
    P("   %d negotiation rows (%d leagues).  Base population (agreement expired or was reopened): %d."
      % (len(rows), 4, len(base)))
    for lg in ("MLB", "NFL", "NBA", "NHL"):
        rs = [r for r in rows if r["league"] == lg]
        P("   %s: %2d rows, %s-%s; %d in base; stoppages in base %d" % (
            lg, len(rs), min(r["expired"] for r in rs), max(r["expired"] for r in rs),
            sum(r in base for r in rs), stop([r for r in rs if r in base])))
    excl = [r["id"] + "(" + r["row_type"] + ")" for r in rows if r["row_type"] not in BASE_TYPES]
    P("   Excluded from the base rate: " + ", ".join(excl))
    P("   KNOWN GAPS: NBA agreements of ~1970-1980 and NHL agreements of 1967-1990 (the Eagleson era)")
    P("   are not enumerated -- we could not document their dates.  None is known to have produced a")
    P("   stoppage (CNN and the NBPA both date each league's first stoppage to 1992/1995), so their")
    P("   absence BIASES THE BASE RATE UP.")
    P("")
    P("2. P(STOPPAGE AT EXPIRATION)")
    P("   any stoppage (incl. offseason, no games lost): " + fmt_p(stop(base), len(base)))
    P("   a stoppage that cancelled regular-season games: " + fmt_p(games(base), len(base)))
    ext = base + [r for r in rows if r["row_type"] == "early_extension"]
    P("   sensitivity, early extensions counted as no-stoppage negotiations: " + fmt_p(stop(ext), len(ext)))
    P("   by league:")
    for lg in ("MLB", "NFL", "NBA", "NHL"):
        rs = [r for r in base if r["league"] == lg]
        P("     %s  any %s   games %s" % (lg, fmt_p(stop(rs), len(rs)), fmt_p(games(rs), len(rs))))
    P("   by era (year the agreement expired):")
    for lab, f in (("pre-1995 ", lambda r: r["expired"] < 1995), ("1995-2025", lambda r: r["expired"] >= 1995)):
        rs = [r for r in base if f(r)]
        P("     %s any %s   games %s" % (lab, fmt_p(stop(rs), len(rs)), fmt_p(games(rs), len(rs))))
    P("   by distance (a):")
    for lev in ("system", "adjustment", "none"):
        rs = [r for r in base if r["dist_a"] == lev]
        if rs:
            P("     %-10s any %s   games %s" % (lev, fmt_p(stop(rs), len(rs)), fmt_p(games(rs), len(rs))))
    sysrows = [r for r in base if r["dist_a"] == "system"]
    P("     system-change negotiations: " + "; ".join("%s=%s" % (r["id"], r["stoppage"]) for r in sysrows))
    # sensitivity: borderline flipped
    flip = []
    for r in base:
        lev = r["dist_a"]
        if r["borderline"] == "Y":
            lev = "adjustment" if lev == "system" else "system"
        flip.append((lev, r))
    for lev in ("system", "adjustment"):
        rs = [r for l, r in flip if l == lev]
        P("     borderline cases flipped -> %-10s any %s" % (lev, fmt_p(stop(rs), len(rs))))
    # era x distance
    P("   distance x era (any stoppage):")
    for lev in ("system", "adjustment"):
        for lab, f in (("pre-1995", lambda r: r["expired"] < 1995), ("1995+", lambda r: r["expired"] >= 1995)):
            rs = [r for r in base if r["dist_a"] == lev and f(r)]
            if rs:
                P("     %-10s %-8s %s" % (lev, lab, fmt_p(stop(rs), len(rs))))
    # logistic
    xs = [1 if r["dist_a"] == "system" else 0 for r in base]
    for lab, ys in (("any stoppage", [1 if r["stoppage"] == "Y" else 0 for r in base]),
                    ("games stoppage", [1 if (r["stoppage"] == "Y" and (r["games_cancelled"] or 0) > 0) else 0 for r in base])):
        b1, b0, lo, hi = logistic_profile(xs, ys)
        p0 = 1 / (1 + math.exp(-b0)); p1 = 1 / (1 + math.exp(-(b0 + b1)))
        P("   logistic, %s ~ system change (n=%d): slope %.2f (profile 95%% %.2f to %.2f); odds ratio %s (95%% %s-%s)"
          % (lab, len(xs), b1, lo, hi, sig_n(math.exp(b1)), sig_n(math.exp(lo)), sig_n(math.exp(hi))))
        P("      fitted P = %s (adjustment/none) vs %s (system).  An interval this wide is the honest result:" % (sig(p0), sig(p1)))
        P("      the fit says the same thing as the two Wilson rows above and no more.")
    P("")
    # durations
    P("3. HOW LONG STOPPAGES LAST (days = end - start)")
    durrows = [r for r in rows if r["stoppage"] == "Y" and r["days"] is not None and r["row_type"] != "first_agreement"]
    def dstats(rs, lab):
        ds = sorted(r["days"] for r in rs)
        if not ds:
            return
        P("   %-34s n=%2d  median %s  range %d-%d" % (lab, len(ds), sig_n(statistics.median(ds)), ds[0], ds[-1]))
    dstats(durrows, "all stoppages (incl. MLB 1981)")
    for lev in ("system", "adjustment"):
        dstats([r for r in durrows if r["dist_a"] == lev], "distance = " + lev)
    dstats([r for r in durrows if r["stype"] == "lockout"], "lockouts")
    dstats([r for r in durrows if r["stype"] != "lockout"], "strikes")
    off = [r for r in durrows if r["timing"] in ("offseason", "preseason")]
    dstats(off, "began offseason/preseason")
    dstats([r for r in off if r["dist_a"] == "system"], "began off/preseason, system change")
    P("   every stoppage, longest first:")
    for r in sorted(durrows, key=lambda r: -r["days"]):
        P("     %-10s %-8s %-10s %4d days  quoted %-4s games lost %-5s %s" % (
            r["id"], r["stype"], r["dist_a"], r["days"], r["days_quoted"] if r["days_quoted"] is not None else "-",
            r["games_cancelled"], "POSTSEASON LOST" if r["postseason_lost"] == "Y" else ""))
    P("   Threshold exceedance given a stoppage:")
    for lab, rs in (("all", durrows), ("system change", [r for r in durrows if r["dist_a"] == "system"]),
                    ("off/preseason start", off)):
        P("     %-20s >75d %s | >115d %s | >232d %s" % (lab,
            fmt_p(sum(r["days"] > 75 for r in rs), len(rs)), fmt_p(sum(r["days"] > 115 for r in rs), len(rs)),
            fmt_p(sum(r["days"] > 232 for r in rs), len(rs))))
    P("")
    P("4. REVENUE GAP (b): players' share under the expiring deal minus owners' first documented proposal")
    gaps = [r for r in rows if r["gap_pp"] is not None]
    P("   %-10s %6s %6s %5s %6s  %s" % ("id", "SQ %", "owners", "gap", "days", "note"))
    for r in gaps:
        P("   %-10s %6s %6s %5s %6s  %s" % (r["id"], r["sq_share"], r["owner_open_share"], r["gap_pp"],
                                           r["days"] if r["days"] is not None else "-", r["gap_note"]))
    unk = [r["id"] for r in rows if r["stoppage"] == "Y" and r["gap_pp"] is None]
    P("   unknown for: " + ", ".join(unk))
    P("   With %d documented values the sample CANNOT support a fit (the brief's bar was ~6)." % len(gaps))
    done = sorted([r for r in gaps if r["days"] is not None], key=lambda r: r["gap_pp"])
    P("   Read plainly: gaps of %s points went with stoppages of %s days." % (
        ", ".join(str(r["gap_pp"]) for r in done), ", ".join(str(r["days"]) for r in done)))
    P("   The smallest documented gap had the longest stoppage.  Three points make no slope, but they are")
    P("   enough to say the revenue gap alone does not predict length.")
    if gaps:
        with open(OUT / "gap_days.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["id", "sq_share", "owner_open_share", "gap_pp", "days", "note"])
            for r in gaps:
                w.writerow([r["id"], r["sq_share"], r["owner_open_share"], r["gap_pp"], r["days"] or "", r["gap_note"]])
    P("   MLB 2026: owners 50%; union says players are 'well over 50%' on MLB's own definitions and would")
    P("   have earned ~$500M less in 2026 under the plan -- about 4 points of $12.1B (DERIVED, not a")
    P("   documented position).  If that holds, 2026 is the smallest documented gap of the four.")
    return L, base, durrows, off

def bls_section(bls, asof, durrows, L):
    P = L.append
    b = [x for x in bls if x["start"] >= D(1993, 1, 1)]
    curve = km([x["dur"] for x in b], [x["event"] for x in b])
    P("")
    P("5. THE GENERAL BASE RATE: BLS major work stoppages (1,000+ workers), U.S., begun 1993 or later")
    P("   n = %d (file current to %s; %d still ongoing, censored).  %d rows that began before 1993 dropped"
      % (len(b), asof, sum(1 - x["event"] for x in b), len(bls) - len(b)))
    P("   (left-truncation: they are in the file only because they were still running in 1993).")
    ds = sorted(x["dur"] for x in b if x["event"])
    P("   median %s days; 75th pct %s; 90th pct %s; longest %d" % (
        sig_n(statistics.median(ds)), sig_n(q(ds, .75)), sig_n(q(ds, .9)), ds[-1]))
    P("   Kaplan-Meier survival S(t) and the 30-day hazard (chance a stoppage that has lasted X days")
    P("   ends within the next 30):")
    rows = []
    for X in (0, 7, 14, 30, 60, 75, 90, 115, 150, 180, 232, 300, 365):
        s = S_at(curve, X); s30 = S_at(curve, X + 30)
        nrisk = sum(1 for x in b if x["dur"] > X)
        h = 1 - s30 / s if s > 0 else float("nan")
        rows.append((X, s, h, nrisk))
        P("     X=%3d  S(X)=%-6s  P(ends in next 30 | lasted X)=%-6s  at risk %d" % (X, sig(s), sig(h), nrisk))
    with open(OUT / "bls_hazard.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["days_lasted", "survival", "p_end_next_30", "n_at_risk"])
        for X, s, h, n in rows:
            w.writerow([X, round(s, 4), round(h, 4), n])
    nfl = [x for x in bls if "Football" in (x["org"] or "")]
    for x in nfl:
        P("   the only sports row in BLS: %s, %s to %s (matches the NFL 2011 lockout)" % (x["org"], x["start"], x["end"]))
    sd = sorted(r["days"] for r in durrows)
    pct = lambda d: sum(1 for x in ds if x <= d) / len(ds)
    P("   Sports vs BLS: sports median %s days vs BLS %s.  Where each sports stoppage would sit in the" %
      (sig_n(statistics.median(sd)), sig_n(statistics.median(ds))))
    P("   BLS distribution (share of BLS stoppages that were no longer):")
    for r in sorted(durrows, key=lambda r: -r["days"]):
        P("     %-10s %4d days -> BLS percentile %s" % (r["id"], r["days"], sig(pct(r["days"]))))
    above = sum(1 for d in sd if d > statistics.median(ds))
    P("   %d of %d sports stoppages ran longer than the BLS median." % (above, len(sd)))
    return curve, b

def forecast(rows, base, durrows, off, curve, args, L_an):
    rng = random.Random(args.seed)
    m = args.draws
    F = []
    P = F.append
    sysb = [r for r in base if r["dist_a"] == "system"]
    k_s, n_s = sum(r["stoppage"] == "Y" for r in sysb), len(sysb)
    k_a, n_a = sum(r["stoppage"] == "Y" for r in base), len(base)
    P("MLB 2026-27 FORECAST -- from scripts/work_stoppages.py, %s" % dt.date.today())
    P("Agreement expires 2026-12-01 (11:59pm ET).  Thresholds counted from a 2026-12-02 start:")
    P("  75 days  = ~Feb 15, 2027 (spring training reports)")
    P("  115 days = ~Mar 27, 2027 (Opening Day, regular-season games at risk)")
    P("  232 days = ~Jul 22, 2027 (the 1994-95 record)")
    P("MLB 2026 is coded distance (a) = SYSTEM CHANGE: the owners' opening demand is a hard cap where none exists.")
    P("Intervals: 95%%, Monte Carlo (%d draws) from Jeffreys Beta posteriors; at most two significant digits." % m)
    P("")
    ps_sys = beta_draws(k_s, n_s, m, rng)
    ps_all = beta_draws(k_a, n_a, m, rng)
    p, lo, hi = wilson(k_s, n_s)
    P("A. P(stoppage on or near Dec 1)")
    P("   history of system-change negotiations: %d of %d -> %s (Wilson 95%% %s-%s)" % (k_s, n_s, sig(p), sig(lo), sig(hi)))
    p2, lo2, hi2 = wilson(k_a, n_a)
    P("   all negotiations, for contrast:        %d of %d -> %s (Wilson 95%% %s-%s)" % (k_a, n_a, sig(p2), sig(lo2), sig(hi2)))
    P("   The history ignores what is already known this fall: a lockout is widely reported as expected")
    P("   (AP 2026-05-28; CBS 2026-10-24) and the owners' stated preference is an offseason lockout.  Read")
    P("   the historical figure as a floor on the editor's number, and section C as the main event.")
    P("")
    def block(label, dur_rows, pstop_draws):
        P(label)
        P("   %-30s %-22s %-22s" % ("", "given a stoppage", "unconditional"))
        out = {}
        for X, name in ((75, "reaches spring training"), (115, "cancels regular season"), (232, "passes 232-day record")):
            k = sum(r["days"] > X for r in dur_rows); n = len(dur_rows)
            pc = beta_draws(k, n, m, rng)
            un = [a * b for a, b in zip(pstop_draws, pc)]
            out[X] = (statistics.median(pc), q(pc, .025), q(pc, .975), statistics.median(un), q(un, .025), q(un, .975))
            P("   >%3dd %-24s %s (%s-%s) [%d/%d]   %s (%s-%s)" % (X, name, sig(out[X][0]), sig(out[X][1]), sig(out[X][2]),
                                                        k, n, sig(out[X][3]), sig(out[X][4]), sig(out[X][5])))
        return out
    P("B. Duration, from SPORTS history (empirical exceedance among past stoppages)")
    sys_d = [r for r in durrows if r["dist_a"] == "system"]
    s1 = block(" B1. system-change stoppages (n=%d)" % len(sys_d), sys_d, ps_sys)
    s2 = block(" B2. all stoppages (n=%d)" % len(durrows), durrows, ps_sys)
    s3 = block(" B3. stoppages that began in the offseason/preseason, like this one (n=%d)" % len(off), off, ps_sys)
    P("")
    P("C. Duration, from the BLS hazard (n=%d U.S. stoppages since 1993)" % args._nbls)
    for X, name in ((75, "reaches spring training"), (115, "cancels regular season"), (232, "passes 232-day record")):
        s = S_at(curve, X)
        un = [a * s for a in ps_sys]
        P("   >%3dd %-24s given a stoppage %s;  unconditional %s (%s-%s)" % (X, name, sig(s), sig(statistics.median(un)),
                                                                          sig(q(un, .025)), sig(q(un, .975))))
    s75, s115, s232 = S_at(curve, 75), S_at(curve, 115), S_at(curve, 232)
    P("   conditional chain: P(past 115 | past 75) = %s;  P(past 232 | past 115) = %s" % (sig(s115 / s75), sig(s232 / s115)))
    P("")
    P("D. WHERE THE TWO DISAGREE")
    P("   Given a stoppage, sports history says it reaches spring training %s of the time; BLS says %s."
      % (sig(s1[75][0]), sig(s75)))
    P("   Sports history says it cancels games %s; BLS says %s.  It passes 232 days: sports %s, BLS %s."
      % (sig(s1[115][0]), sig(s115), sig(s1[232][0]), sig(s232)))
    h0 = 1 - S_at(curve, 30); h115 = 1 - S_at(curve, 145) / S_at(curve, 115)
    P("   The ordinary American strike is short (BLS median %s days) because the cost lands on both sides"
      % sig_n(statistics.median([x["dur"] for x in args._bls if x["event"]])))
    P("   at once.  A sports lockout begun in December costs almost nothing until games are at stake: no")
    P("   salaries are paid in the offseason and little revenue is lost.  So the sports clock that matters")
    bmed = statistics.median([x["dur"] for x in args._bls if x["event"]])
    P("   is days to the first cancelled game, and the sports rows run long -- %d of %d sit above the BLS"
      % (sum(r["days"] > bmed for r in durrows), len(durrows)))
    P("   median.  BLS is the wrong base rate for the first ~100 days of an offseason lockout.  It is a fair")
    P("   warning for what follows: once a stoppage is long, it tends to stay long (BLS chance of ending")
    P("   within 30 days: %s for a new stoppage, %s for one already 115 days old)." % (sig(h0), sig(h115)))
    sysd = [r["days"] for r in durrows if r["dist_a"] == "system"]
    a75 = sum(d > 75 for d in sysd); a115 = sum(d > 115 for d in sysd); a232 = sum(d > 232 for d in sysd)
    P("   Sports chain (system-change stoppages): past 115 given past 75 = %d/%d; past 232 given past 115 = %d/%d."
      % (a115, a75, a232, a115))
    P("   BLS chain: %s and %s.  Both say the same thing: the spring-training deadline is the fork." %
      (sig(s115 / s75), sig(s232 / s115)))
    P("")
    P("E. ONE-LINE ANSWER (the editor's number)")
    P("   %-34s %-26s %s" % ("", "unconditional", "if the lockout happens"))
    P("   %-34s %-26s %s" % ("P(stoppage on/near Dec 1)", "~%s (%s-%s)" % (sig(p), sig(lo), sig(hi)), "--"))
    for X, name in ((75, "P(reaches spring training)"), (115, "P(cancels regular-season games)"), (232, "P(passes 232 days)")):
        un = (s1[X][3], s1[X][4], s1[X][5]); co = (s1[X][0], s1[X][1], s1[X][2])
        lo_ = min(s1[X][0], s2[X][0], s3[X][0]); hi_ = max(s1[X][0], s2[X][0], s3[X][0])
        P("   %-34s %-26s %s (%s-%s); other sports subsets %s-%s; BLS %s" % (
            name, "~%s (%s-%s)" % (sig(un[0]), sig(un[1]), sig(un[2])), sig(co[0]), sig(co[1]), sig(co[2]),
            sig(lo_), sig(hi_), sig(S_at(curve, X))))
    P("   Headline column: system-change stoppages (B1), the class this one belongs to.  n = %d; every" % len(sys_d))
    P("   interval spans roughly half the scale, so say 'about one in X', never a decimal.")
    return F

def stakes(args, L):
    P = L.append
    att, api, srcname = load_attendance()
    P("")
    P("6. WHAT IS AT STAKE (MLB)")
    rev = 12.1e9; players = 942; avg = 5335966; games = 2430; clubs = 30
    pay = players * avg
    P("   Revenue: $12.1B in 2024 (Forbes, reported by CBS Sports 2025-01-27; a record, up from $11.6B in 2023).")
    P("     SINGLE FETCHED SOURCE: S&P Global reports the same figure but blocked our request.  No 2025")
    P("     figure from a named source was found.")
    P("     per scheduled regular-season game: $%sM;  per calendar day: $%sM" % (sig_n(rev / games / 1e6), sig_n(rev / 365 / 1e6)))
    P("   Player salaries, 2026 opening day (AP payroll study, 2026-04-09): 942 players x $5,335,966 = $%sB"
      % sig_n(pay / 1e9))
    P("     (AP wire only -- one source.)  Per regular-season game lost: ~$%sM of player pay;" % sig_n(pay / games / 1e6))
    P("     per club-game: $%sM.  A lost 162-game season = ~$%sB of salaries and, on the revenue figure," % (
        sig_n(pay / clubs / 162 / 1e6), sig_n(pay / 1e9)))
    P("     most of $12B of revenue (postseason and national TV included).")
    P("   The cap itself (AP 2026-05-28): cap $245.3M, floor $171.2M from 2027; 8 clubs over the cap and 12")
    P("     under the floor on 2026 opening-day payrolls; MLB says revenue grew 247% since 2003, payroll 149%.")
    # attendance
    P("")
    P("7. ATTENDANCE AFTER A STOPPAGE (per home game, all clubs; Lahman Teams table: %s)" % srcname)
    P("   cross-check: MLB Stats API season totals (attendance endpoint), shown as the ratio Lahman/API.")
    years = sorted(att)
    with open(OUT / "attendance.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["season", "clubs", "games_played", "home_games", "attendance", "per_game", "statsapi_total", "statsapi_openings", "lahman_over_api"])
        for y in years:
            a = att[y]; t = api.get(y, (0, 0))
            w.writerow([y, a[3], a[2] // 2, a[1], a[0], round(a[0] / a[1]) if a[1] else "", t[0], t[1],
                        round(a[0] / t[0], 4) if t[0] else ""])
    pg = {y: att[y][0] / att[y][1] for y in years if att[y][1] and att[y][0]}
    def show(ys, note=""):
        for y in ys:
            if y in pg:
                t = api.get(y, (0, 0))
                P("     %d  %6s per game  (%d clubs, %d games)  Lahman/API %s %s" % (
                    y, "{:,}".format(round(pg[y])), att[y][3], att[y][2] // 2,
                    "%.3f" % (att[y][0] / t[0]) if t[0] else "n/a", note))
    P("   1981 strike:")
    show(range(1979, 1985))
    P("   1994-95 strike:")
    show(range(1992, 1999))
    ref93, ref94 = pg[1993], pg[1994]
    rec93 = next((y for y in years if y > 1995 and pg.get(y, 0) >= ref93), None)
    rec94 = next((y for y in years if y > 1995 and pg.get(y, 0) >= ref94), None)
    P("     drop 1994 -> 1995: %s%%;  first season back above 1993's level: %s (%s seasons after 1995);"
      % (sig_n(100 * (pg[1995] / ref94 - 1)), rec93, rec93 - 1995 if rec93 else "n/a"))
    P("     above 1994's pre-strike level: %s.  Confounds: 1993-94 were inflated by expansion clubs (Colorado drew" % rec94)
    P("     55,350 a game in 1993, Lahman) and new parks; 1995 itself was a 144-game season begun three weeks late.")
    rec81 = next((y for y in years if y > 1981 and pg.get(y, 0) >= pg[1980]), None)
    P("     1981: per-game attendance fell %s%% from 1980; back above 1980 in %s." % (sig_n(100 * (pg[1981] / pg[1980] - 1)), rec81))
    P("   2021-22 lockout (no games lost):")
    show(range(2018, 2026), "")
    P("     2020 had no fans and 2021 had capacity limits (COVID), so 2022 vs 2019 is the only clean")
    P("     comparison: %s%%.  No lockout effect can be separated from the pandemic." % sig_n(100 * (pg[2022] / pg[2019] - 1)))
    P("   NHL 2004-05: skipped -- no primary attendance source was found that we could fetch.")
    return pg

def main():
    global OFFLINE
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="read only the cache")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--draws", type=int, default=100000)
    args = ap.parse_args()
    OFFLINE = args.offline
    fetch_all()
    rows = build_rows()
    write_csv(rows)
    L, base, durrows, off = analyze(rows, args)
    bls, asof = load_bls()
    curve, b = bls_section(bls, asof, durrows, L)
    args._nbls = len(b); args._bls = b
    stakes(args, L)
    L += ["", "SOURCE CODES (negotiations.csv `sources` column)"] + ["   %s = %s" % kv for kv in SOURCE_KEY.items()]
    L += ["", "8. LIMITS",
          "   * n is small: %d base negotiations, %d stoppages with durations.  Every interval is wide." % (len(base), len(durrows)),
          "   * Distance (a) was coded by someone who knew the outcomes, from a written rule; the borderline",
          "     cases are flipped as a sensitivity above.  A blind second coder would be better.",
          "   * The leagues' early agreements are under-enumerated (section 1), biasing P(stoppage) upward.",
          "   * Rows are not independent: the same union and owners meet again, and the last fight shapes the",
          "     next.  Treating 1990-2026 MLB as separate coin flips understates uncertainty.",
          "   * Duration thresholds are measured from the stoppage's start; in-season strikes and December",
          "     lockouts start their clocks at very different points in the money calendar.",
          "   * BLS covers U.S. bargaining units of 1,000+ workers; no MLB/NBA/NHL unit is that large."]
    F = forecast(rows, base, durrows, off, curve, args, L)
    (OUT / "analysis.txt").write_text("\n".join(L) + "\n")
    (OUT / "forecast.txt").write_text("\n".join(F) + "\n")
    print("\n".join(L)); print(); print("\n".join(F))

if __name__ == "__main__":
    main()
