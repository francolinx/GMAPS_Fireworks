#!/usr/bin/env python3
"""Synthetic US tower/ground phraseology (FAA JO 7110.65 / AIM style) with gold spans by construction.

Why: ATCO2 is European + Australian. This adds US phraseology ("cleared for takeoff", "line up and wait",
"hold short", "climb and maintain", group-form flight numbers) so the model is not blind to it, and gives a
second held-out "stress" split whose labels are exact by construction (no human labelling, no teacher).

Every token carries a tag (callsign / command / value / none). ASR-style noise is applied to the token list,
then the text and the gold spans are rebuilt from the tags, so the gold always matches the text exactly.

  python scripts/02_synth_us_phraseology.py --train 3000 --stress 300 --out data/synthetic

Judges should be told this is synthetic. It is for training breadth and a secondary stress test only;
the headline benchmark stays the real ATCO2 gold test split.
"""
import argparse, hashlib, json, os, random

DIGITS = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "niner"}
GROUP = {"10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen", "14": "fourteen", "15": "fifteen", "16": "sixteen", "17": "seventeen", "18": "eighteen", "19": "nineteen",
         "20": "twenty", "30": "thirty", "40": "forty", "50": "fifty", "60": "sixty", "70": "seventy", "80": "eighty", "90": "ninety"}
NATO = {c: w for c, w in zip("abcdefghijklmnopqrstuvwxyz", "alpha bravo charlie delta echo foxtrot golf hotel india juliett kilo lima mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu".split())}
AIRLINES_A = ["united", "delta", "american", "southwest", "alaska", "jetblue", "skywest", "fedex", "spirit", "frontier", "envoy", "republic"]
AIRLINES_B = ["hawaiian", "sun country", "allegiant", "brickyard", "cactus", "speedbird", "lufthansa", "air canada", "ups", "atlas"]
TYPES = ["cessna", "skyhawk", "cherokee", "citation", "bonanza", "baron", "mooney", "cirrus", "gulfstream", "lear"]
AIRPORTS_A = [("KSFO", "sfo", ["28l", "28r", "10l", "10r", "1l", "1r", "19l", "19r"]), ("KATL", "atlanta", ["26r", "27l", "8r", "9l", "10", "28"]),
              ("KJFK", "kennedy", ["4l", "4r", "22l", "22r", "13l", "31r"]), ("KORD", "ohare", ["28c", "10c", "27l", "9r", "22l"]), ("KDEN", "denver", ["16r", "34l", "25", "17l", "8"])]
AIRPORTS_B = [("KLAX", "los angeles", ["24l", "24r", "25l", "25r", "6l", "7r"]), ("KBOS", "boston", ["4r", "22l", "27", "9", "33l"]),
              ("KSEA", "seattle", ["16c", "34c", "16l", "34r"]), ("KMIA", "miami", ["9", "27", "8r", "12", "30"]), ("KLGA", "laguardia", ["4", "22", "13", "31"])]
TAXIWAYS = list("abcdefghjklmnpqrstuvwz")


def say_digits(s):
    return " ".join(DIGITS[c] if c.isdigit() else NATO[c] for c in s)


def say_runway(r):
    n, side = "".join(c for c in r if c.isdigit()), "".join(c for c in r if c.isalpha())
    return "runway " + say_digits(n) + ({"l": " left", "r": " right", "c": " center"}.get(side, ""))


def say_flight(n, rng):
    s = str(n)
    if rng.random() < 0.5 or len(s) < 3:            # ICAO digit form
        return say_digits(s)
    head, tail = s[:-2], s[-2:]                       # FAA group form: "two forty five"
    if tail[0] == "0":
        return say_digits(s)
    if tail in GROUP:
        return say_digits(head) + " " + GROUP[tail]
    return say_digits(head) + " " + GROUP[tail[0] + "0"] + " " + DIGITS[tail[1]]


def callsign(rng, pool):
    k = rng.random()
    if k < 0.55:
        return f"{rng.choice(pool)} {say_flight(rng.randint(10, 2999), rng)}"
    if k < 0.85:
        tail = "".join(rng.choice("0123456789") for _ in range(rng.randint(2, 3))) + "".join(rng.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(rng.randint(1, 2)))
        return ("november " if rng.random() < 0.6 else f"{rng.choice(TYPES)} ") + say_digits(tail)
    return rng.choice(["rescue", "lifeguard", "medevac", "coast guard", "ops", "airport"]) + " " + say_digits(str(rng.randint(1, 99)))


def alt(rng):
    v = rng.choice([1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000])
    return (say_digits(str(v // 1000)) + " thousand" + (" five hundred" if v % 1000 else "")) if v < 10000 else "one zero thousand"


def freq(rng):
    return say_digits(str(rng.choice([118, 119, 120, 121, 124, 125, 126, 127, 128, 132, 133]))) + " point " + say_digits(rng.choice(["1", "3", "5", "65", "75", "85", "9", "95"]))


def wind(rng):
    return f"wind {say_digits(str(rng.choice([180, 210, 240, 270, 280, 290, 300, 330])))} at {say_digits(str(rng.randint(3, 22)))}"


def hdg(rng):
    return "heading " + say_digits(str(rng.choice([90, 120, 150, 180, 210, 240, 270, 280, 300, 330, 360])).zfill(3))


# token builders: each returns a list of (word, tag, span_id); adjacent same-tag spans stay separate
_SPAN = [0]


def T(text, tag):
    _SPAN[0] += 1
    return [(w, tag, _SPAN[0]) for w in text.split()]


def atco_templates(rng, cs, rw, rw2, tw, tw2, apt):
    V = "value"; C = "command"
    return [
        ("CLEARED_TO_LAND", T(cs, "callsign") + T(say_runway(rw), V) + T("cleared to land", C) + (T(wind(rng), V) if rng.random() < .6 else [])),
        ("CLEARED_TO_LAND", T(cs, "callsign") + T("cleared to land", C) + T(say_runway(rw), V)),
        ("CLEARED_FOR_TAKEOFF", T(cs, "callsign") + T(say_runway(rw), V) + T("cleared for takeoff", C) + (T("fly", "none") + T(say_runway(rw).replace("runway", "runway") + " heading", V) if rng.random() < .3 else [])),
        ("CLEARED_FOR_TAKEOFF", T(cs, "callsign") + T("turn left", C) + T(hdg(rng), V) + T(say_runway(rw), V) + T("cleared for takeoff", C)),
        ("LINE_UP_AND_WAIT", T(cs, "callsign") + T(say_runway(rw), V) + T("line up and wait", C) + (T("traffic on a", "none") + T(say_digits(str(rng.randint(2, 6))) + " mile final", V) if rng.random() < .5 else [])),
        ("HOLD_SHORT", T(cs, "callsign") + T("hold short", C) + T(say_runway(rw), V) + (T("at", "none") + T("taxiway " + NATO[tw], V) if rng.random() < .4 else [])),
        ("CROSS_RUNWAY", T(cs, "callsign") + T("cross", C) + T(say_runway(rw), V) + T("at", "none") + T(NATO[tw], V)),
        ("CROSS_RUNWAY", T(cs, "callsign") + T("cross", C) + T(say_runway(rw), V) + T("at", "none") + T(NATO[tw], V) + T("contact tower", C) + T(freq(rng), V)),
        ("TAXI", T(cs, "callsign") + T(f"{apt} ground", "none") + T("taxi to", C) + T(say_runway(rw), V) + T("via", "none") + T(f"{NATO[tw]} {NATO[tw2]}", V) + T("hold short", C) + T(say_runway(rw2), V)),
        ("TAXI", T(cs, "callsign") + T("taxi to", C) + T("the ramp", V) + T("via", "none") + T(NATO[tw], V)),
        ("CONTACT_FREQUENCY", T(cs, "callsign") + T("contact", C) + T(rng.choice(["tower", "ground", "departure", "norcal approach"]) + " " + freq(rng), V)),
        ("VACATE_RUNWAY", T(cs, "callsign") + T("exit", C) + T(NATO[tw], V) + T("contact ground", C) + T("point " + say_digits(rng.choice(["65", "8", "9", "75"])), V)),
        ("GO_AROUND", T(cs, "callsign") + T("go around", C) + (T("climb and maintain", C) + T(alt(rng), V) if rng.random() < .6 else [])),
        ("CLIMB", T(cs, "callsign") + T("climb and maintain", C) + T(alt(rng), V)),
        ("DESCEND", T(cs, "callsign") + T("descend and maintain", C) + T(alt(rng), V)),
        ("NAVIGATE", T(cs, "callsign") + T(rng.choice(["turn left", "turn right", "fly"]), C) + T(hdg(rng), V)),
        ("SPEED", T(cs, "callsign") + T("reduce speed to", C) + T(say_digits(str(rng.choice([170, 180, 190, 210, 250]))) + " knots", V)),
        ("HOLD_POSITION", T(cs, "callsign") + T("hold position", C) + (T("traffic crossing downfield", "none") if rng.random() < .5 else [])),
        ("REPORT", T(cs, "callsign") + T("report", C) + T(rng.choice(["a two mile final", "the runway in sight", "established on the localizer", "leaving " + alt(rng)]), V)),
        ("CLEARED_FOR_TAKEOFF", T(cs, "callsign") + T(wind(rng), V) + T(say_runway(rw), V) + T("cleared for takeoff", C)),
        ("ROUTE_CLEARANCE", T(cs, "callsign") + T("cleared to", C) + T(rng.choice(["oakland", "burbank", "reno", "san diego", "portland"]) + " airport", V) + T("via", "none") + T(rng.choice(["the sfo seven departure", "radar vectors", "direct"]), V) + T("squawk", C) + T(say_digits(str(rng.randint(1000, 7777))), V)),
    ]


def pilot_templates(rng, cs, rw, rw2, tw, apt):
    V = "value"; C = "command"
    short = " ".join(cs.split()[-2:]) if rng.random() < .35 else cs   # abbreviated readback
    return [
        ("CLEARED_TO_LAND", T(say_runway(rw), V) + T("cleared to land", C) + T(short, "callsign")),
        ("CLEARED_TO_LAND", T("cleared to land", C) + T(say_runway(rw), V) + T(short, "callsign")),
        ("CLEARED_FOR_TAKEOFF", T("cleared for takeoff", C) + T(say_runway(rw), V) + T(short, "callsign")),
        ("LINE_UP_AND_WAIT", T("line up and wait", C) + T(say_runway(rw), V) + T(short, "callsign")),
        ("HOLD_SHORT", T("holding short", C) + T(say_runway(rw), V) + T(short, "callsign")),
        ("HOLD_SHORT", T("hold short", C) + T(say_runway(rw), V) + T(short, "callsign")),
        ("CROSS_RUNWAY", T("crossing", C) + T(say_runway(rw), V) + T("at", "none") + T(NATO[tw], V) + T(short, "callsign")),
        ("TAXI", T("taxi to", C) + T(say_runway(rw), V) + T("via", "none") + T(NATO[tw], V) + T("hold short", C) + T(say_runway(rw2), V) + T(short, "callsign")),
        ("CONTACT_FREQUENCY", T(rng.choice(["tower", "ground", "departure"]), V) + T(freq(rng), V) + T(short, "callsign")),
        ("CONTACT_FREQUENCY", T("contact", C) + T(rng.choice(["tower", "ground"]) + " " + freq(rng), V) + T(short, "callsign")),
        ("REPORT", T(cs, "callsign") + T("ready for departure", C) + T(say_runway(rw), V)),
        ("POSITION_REPORT", T(f"{apt} tower", "none") + T(cs, "callsign") + T(rng.choice(["ten miles southeast", "five mile final", "over the bay at two thousand"]), V) + T("inbound", C) + T("with", "none") + T(rng.choice(["alpha", "bravo", "charlie", "delta", "kilo"]), V)),
        ("TAXI", T(f"{apt} ground", "none") + T(cs, "callsign") + T("request taxi", C) + (T("to", "none") + T(say_runway(rw), V) if rng.random() < .5 else [])),
        ("GO_AROUND", T("going around", C) + T(short, "callsign")),
        ("CLIMB", T("climb and maintain", C) + T(alt(rng), V) + T(short, "callsign")),
        ("ACK", T("wilco", C) + T(short, "callsign")),
        ("ACK", T("say again", C) + T("for", "none") + T(short, "callsign")),
        ("VACATE_RUNWAY", T("clear of", C) + T(say_runway(rw), V) + T(short, "callsign")),
        ("POSITION_REPORT", T(short, "callsign") + T("with you", "none") + T(rng.choice(["passing", "leaving"]), C) + T(alt(rng), V)),
    ]


def add_noise(tokens, rng, level):
    out = []
    for w, tag, sid in tokens:
        r = rng.random()
        if r < 0.03 * level and tag == "none":
            continue                                   # drop a filler word
        if r < 0.05 * level and tag == "none":
            out.append(("uh" if rng.random() < .7 else "ah", "none", 0))   # fillers only between spans
        if r < 0.07 * level and tag in ("none", "callsign"):
            out.append((w, tag, sid))                  # stutter ("united united two forty five")
        if w == "niner" and rng.random() < 0.4 * level:
            w = "nine"
        if w == "three" and rng.random() < 0.15 * level:
            w = "tree"
        if w == "runway" and rng.random() < 0.2 * level:
            continue                                   # pilots often drop "runway"
        out.append((w, tag, sid))
    return out


def realize(tokens):
    text = " ".join(w for w, _, _ in tokens)
    spans = {"callsign": [], "command": [], "value": []}
    cur, cur_key = [], None
    for w, tag, sid in tokens + [("", "none", -1)]:
        key = (tag, sid)
        if key != cur_key:
            if cur_key and cur_key[0] in spans and cur:
                spans[cur_key[0]].append(" ".join(cur))
            cur, cur_key = [], key
        cur.append(w)
    return text, spans


def gen(n, rng, airports, airline_pool, noise, src):
    rows = []
    for i in range(n):
        icao, apt, rws = rng.choice(airports)
        rw, rw2 = rng.sample(rws, 2)
        tw, tw2 = rng.sample(TAXIWAYS, 2)
        cs = callsign(rng, airline_pool)
        if rng.random() < 0.6:
            action, toks = rng.choice(atco_templates(rng, cs, rw, rw2, tw, tw2, apt)); role = "ATCO"
            fac = f"{apt.upper()} {'Ground' if action in ('TAXI', 'CROSS_RUNWAY', 'HOLD_SHORT') and rng.random() < .8 else 'Tower'}"
        else:
            action, toks = rng.choice(pilot_templates(rng, cs, rw, rw2, tw, apt)); role = "PILOT"
            fac = f"{apt.upper()} {rng.choice(['Tower', 'Ground'])}"
        toks = add_noise(toks, rng, noise)
        text, spans = realize(toks)
        rows.append({"id": f"{src}:{i:05d}", "airport": icao, "facility": fac, "speaker_label": "ATCO" if role == "ATCO" else cs,
                     "role": role, "text": text, "gold": spans, "source": src, "intended_action": action})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=int, default=3000)
    ap.add_argument("--stress", type=int, default=300)
    ap.add_argument("--noise", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=7110)
    ap.add_argument("--out", default="data/synthetic")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = random.Random(args.seed)
    train = gen(args.train, rng, AIRPORTS_A, AIRLINES_A, args.noise, "synth_us_train")
    stress = gen(args.stress, random.Random(args.seed + 1), AIRPORTS_B, AIRLINES_B, args.noise, "synth_us_stress")
    for name, rows in (("us_train.jsonl", train), ("us_stress.jsonl", stress)):
        p = os.path.join(args.out, name)
        with open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"wrote {len(rows)} → {p}")
    h = hashlib.sha256(open(os.path.join(args.out, "us_stress.jsonl"), "rb").read()).hexdigest()
    open(os.path.join(args.out, "us_stress.sha256"), "w").write(f"{h}  us_stress.jsonl\n")
    print("us_stress.jsonl sha256:", h)
    for r in train[:4]:
        print(" ", r["role"], "|", r["text"], "|", r["gold"])


if __name__ == "__main__":
    main()
