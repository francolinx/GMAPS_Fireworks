#!/usr/bin/env python3
"""Map free-text ATC command spans to a small canonical action vocabulary.

The ATCO2 gold tags mark *spans* ("cleared to land", "clear to land", "landing on discretion"),
not categories. Both the gold spans and the model's predicted spans are passed through
normalize_command() so the action-level metrics compare like with like.

Rules are ORDERED: the first matching rule wins. Keep runway-occupancy actions (the ones
GMAPS cares about) at the top. Anything unmatched becomes OTHER; run
`python bench/normalize.py data/atco2_1h_gold.jsonl` to see coverage and the OTHER tail.
"""
import json, re, sys, collections

RUNWAY_CRITICAL = {
    "CLEARED_TO_LAND", "CLEARED_FOR_TAKEOFF", "LINE_UP_AND_WAIT", "HOLD_SHORT",
    "HOLD_POSITION", "CROSS_RUNWAY", "BACKTRACK", "TOUCH_AND_GO", "VACATE_RUNWAY", "GO_AROUND",
}

ACTIONS = [
    "CLEARED_TO_LAND", "CLEARED_FOR_TAKEOFF", "LINE_UP_AND_WAIT", "HOLD_SHORT", "HOLD_POSITION",
    "CROSS_RUNWAY", "BACKTRACK", "TOUCH_AND_GO", "VACATE_RUNWAY", "GO_AROUND",
    "TAXI", "STARTUP_PUSHBACK", "CONTACT_FREQUENCY", "REPORT", "CLIMB", "DESCEND",
    "NAVIGATE", "SPEED", "MAINTAIN", "APPROACH_CLEARANCE", "ROUTE_CLEARANCE",
    "POSITION_REPORT", "ACK", "OTHER",
]

# (action, regex) — evaluated in order on the lower-cased, whitespace-collapsed span.
RULES = [
    # --- runway occupancy / clearance state (GMAPS-critical) -----------------------------
    ("GO_AROUND",           r"\bgo(ing)?[- ]?around\b|\bbreaking off\b"),
    ("TOUCH_AND_GO",        r"\btouch and go\b|\bstop and go\b|\bin and go\b"),
    ("LINE_UP_AND_WAIT",    r"\blin(e|ing) up\b"),
    ("HOLD_SHORT",          r"\bhold(ing)? short\b"),
    ("BACKTRACK",           r"\bbacktrack\b"),
    ("VACATE_RUNWAY",       r"\bvacat|\bvacacated\b|\brunway vacated\b|^exit$|\bclear of\b"),
    # "ready for departure" / "report ready" are readiness reports, not a takeoff clearance
    ("REPORT",              r"\bready for departure\b|\breport ready\b|^ready for$|^ready to$"),
    ("CLEARED_FOR_TAKEOFF", r"\btake ?off\b|\bdepartur|\bdepart(ing)?\b|\bdepart from\b"),
    ("CLEARED_TO_LAND",     r"\bland(ing)?\b|\bfull stop\b|\btouchdown\b"),
    ("GO_AROUND",           r"\bgo around\b"),
    # climbing/descending reports that happen to contain "crossing" (altitude) go to CLIMB/DESCEND
    ("CLIMB",               r"\bclimb"),
    ("DESCEND",             r"\bdescen|\bin descent\b"),
    ("CROSS_RUNWAY",        r"\bcross"),
    ("HOLD_POSITION",       r"\bhold(ing)? position\b|\bhold on\b|^hold(ing)?$|\bholding point\b|"
                            r"\bstand ?by\b|\bwait(ing)?\b|^stop$|\bcall you( back)?$|\bi call you back\b|"
                            r"\bcall you (passing|when ready)\b"),
    # --- ground movement -------------------------------------------------------------------
    ("STARTUP_PUSHBACK",    r"\bstart ?up\b|\bpush ?back\b|\bpush and start\b|\bengine start\b|"
                            r"\bstart (and push|approved)\b|^starting$|\brun up\b|\bready for ifr\b|\bifr clearance\b"),
    ("TAXI",                r"\btaxi|\bpark(ing)?\b|\benter via\b|\bnext left via\b|\bturn left via\b|"
                            r"\bfollow( behind)?$|\bproceed normally\b|\bto the left$"),
    # --- comms -----------------------------------------------------------------------------
    ("CONTACT_FREQUENCY",   r"\bcontact\b|\bcontract\b|\bfrequency\b|\bleave the command\b|\bcall me on\b|"
                            r"\bconnect\b|^call$|\byou may leave\b|\bmay leave\b|\bchange frequency\b|\bleave out on\b"),
    ("REPORT",              r"\breport|\bnext final\b|^final$|\bfinal runway\b"),
    # --- vertical / lateral / speed -----------------------------------------------------------
    ("MAINTAIN",            r"\bmaintain\b"),
    ("SPEED",               r"\bspeed\b|^maximum$|\bspeed restrictions\b"),
    ("NAVIGATE",            r"\bheading?|\bturn|^fly$|\bfly heading\b|\btourning\b|\bproceed|\bdirect\b|\bstraight ahead\b|"
                            r"\borbit\b|\bvector|\bcircl|\bjoin|\bupwind\b|\boutbound\b|\binbound to\b|"
                            r"\benter control zone\b|\bcircuit|\bshortcut\b|\bleft turn\b|\bright turn\b|^next$"),
    ("APPROACH_CLEARANCE",  r"\bapproach\b|\bils\b|\bestablish|\betablished\b|\bstraight in\b|\bdme\b|"
                            r"\bexpect to land\b|\bexpect landing\b|\bcontinue( to| on| for| toward)?$|\brnp\b|\barp\b|\bvisual\b"),
    ("ROUTE_CLEARANCE",     r"\brecleared\b|\bcleared to\b|\bcleared( for)?$|\bclearance\b|\bcleared to destination\b|"
                            r"\brequested change\b|\bexpect clearance\b"),
    # --- position / status reports --------------------------------------------------------
    ("POSITION_REPORT",     r"\bpassing\b|\bapproaching\b|\bleaving\b|\bentering\b|\bidentified\b|\bis passing\b|"
                            r"\bwhen passing\b|^pass$|\binbound\b|\bwe just upon\b|\bstop established\b|\bin sight\b"),
    # --- acknowledgements / requests / misc -------------------------------------------------
    ("ACK",                 r"\bconfirm|\bsay again\b|^say$|^again$|\bcopy|\bcopied\b|\baffirm|\bapproved?\b|"
                            r"\bgo ahead\b|\bpass your message\b|\bnegative\b|\becho\b|\bbreak break\b|\bsorry\b|"
                            r"\banswer with\b|\broger\b|\bwilco\b|\bready\b|\brequest|\bnot ready\b|\bwant to\b|"
                            r"\bintend\b|\bexpect\b|\bavailable\b|\bnow active\b|\blooking\b|\bseaching\b|"
                            r"\bremain\b|\bstay clear\b|\bbelow\b|\bindicating\b|\bis calling\b|\bto compose\b|"
                            r"\bkeep the\b|\bout of\b|\bredue\b|^make$|\bmake your\b|\bwill\b|\bable to\b"),
]
_COMPILED = [(a, re.compile(p)) for a, p in RULES]


def normalize_command(span: str) -> str:
    s = " ".join((span or "").lower().replace("(-ding)", "").split())
    s = re.sub(r"\[hes\]", "", s).strip()
    for action, rx in _COMPILED:
        if rx.search(s):
            return action
    return "OTHER"


def actions_for(spans) -> set:
    return {normalize_command(s) for s in spans or []}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/atco2_1h_gold.jsonl"
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    by_action = collections.Counter()
    other = collections.Counter()
    mapping = collections.defaultdict(collections.Counter)
    n = 0
    for r in rows:
        for c in r["gold"]["command"]:
            n += 1
            a = normalize_command(c)
            by_action[a] += 1
            mapping[a][c.lower()] += 1
            if a == "OTHER":
                other[c.lower()] += 1
    print(f"{n} gold command spans → {len(by_action)} actions")
    for a, k in by_action.most_common():
        print(f"  {a:20s} {k:4d}   e.g. " + "; ".join(x for x, _ in mapping[a].most_common(4)))
    print(f"\nOTHER tail ({sum(other.values())} spans, {len(other)} distinct):")
    for x, k in other.most_common():
        print(f"  {k} {x}")
    crit = sum(k for a, k in by_action.items() if a in RUNWAY_CRITICAL)
    print(f"\nrunway-critical spans: {crit} ({crit / n:.1%})")
