#!/usr/bin/env python3
"""Download and parse the ATCO2-test-set-1h gold NER annotations, then split by airport.

Source: https://www.atco2.org/data  (atco2_1h_xml.tar.gz, "available for research purposes").
The data itself is NOT committed to this repo. Run this script to reproduce the splits.

Output (under --out, default ./data):
  atco2_1h_gold.jsonl      all 877 segments, plain text + gold entities
  splits/train.jsonl       training airports minus dev
  splits/dev.jsonl         every Nth row of the training airports
  splits/test.jsonl        held-out airports (never used for training or tuning)
  splits/test.sha256       hash of test.jsonl — commit this BEFORE the build period
"""
import argparse, collections, glob, hashlib, io, json, os, re, sys, tarfile, urllib.request
import xml.etree.ElementTree as ET

URL = "https://www.atco2.org/data/atco2_1h_xml-tar.gz"
TAG_RE = re.compile(r"\[#(callsign|command|value)\](.*?)\[/#\1\]", re.S)
UNNAMED_RE = re.compile(r"\[/?#unnamed\]")
# Default held-out airports: three countries the model never sees in training.
#   YSSY Sydney (AU), LKPR Prague (CZ), LZIB Bratislava (SK)
DEFAULT_TEST_AIRPORTS = ["YSSY", "LKPR", "LZIB"]


def speaker_role(label: str) -> str:
    label = (label or "").strip()
    if not label or label.upper().startswith("UNK"):
        return "UNKNOWN"
    if label.upper().startswith("ATCO"):
        return "ATCO"
    return "PILOT"  # pilot segments are labelled with the aircraft's ICAO callsign


def parse_xml_dir(xml_dir: str):
    rows = []
    for f in sorted(glob.glob(os.path.join(xml_dir, "*.xml"))):
        name = os.path.basename(f)[:-4]
        parts = name.split("_")
        airport = parts[0]
        facility = " ".join(p for p in parts[1:4] if not re.match(r"^\d", p))
        tree = ET.parse(f)
        for i, seg in enumerate(tree.getroot().findall("segment")):
            tagged = (seg.findtext("text") or "").strip()
            ents = collections.defaultdict(list)
            for kind, span in TAG_RE.findall(tagged):
                ents[kind].append(" ".join(span.split()))
            plain = TAG_RE.sub(lambda m: m.group(2), tagged)
            plain = " ".join(UNNAMED_RE.sub("", plain).split())
            label = (seg.findtext("speaker_label") or "").strip()
            rows.append({
                "id": f"{name}#{i}",
                "airport": airport,
                "facility": facility,
                "speaker_label": label,
                "role": speaker_role(label),
                "start": seg.findtext("start"),
                "end": seg.findtext("end"),
                "text": plain,
                "gold": {
                    "callsign": ents["callsign"],
                    "command": ents["command"],
                    "value": ents["value"],
                },
                "tagged_text": tagged,
            })
    return rows


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--tarball", help="use a local atco2_1h_xml.tar.gz instead of downloading")
    ap.add_argument("--test-airports", nargs="+", default=DEFAULT_TEST_AIRPORTS)
    ap.add_argument("--dev-every", type=int, default=7, help="every Nth training row goes to dev")
    args = ap.parse_args()

    xml_dir = os.path.join(args.out, "raw_xml")
    os.makedirs(xml_dir, exist_ok=True)
    if args.tarball:
        blob = open(args.tarball, "rb").read()
    else:
        print(f"downloading {URL} ...")
        blob = urllib.request.urlopen(URL, timeout=120).read()
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.endswith(".xml"):
                m.name = os.path.basename(m.name)  # flatten, no path traversal
                tf.extract(m, xml_dir)

    rows = parse_xml_dir(xml_dir)
    write_jsonl(os.path.join(args.out, "atco2_1h_gold.jsonl"), rows)

    test = [r for r in rows if r["airport"] in args.test_airports]
    rest = [r for r in rows if r["airport"] not in args.test_airports]
    dev = [r for i, r in enumerate(rest) if i % args.dev_every == 0]
    train = [r for i, r in enumerate(rest) if i % args.dev_every != 0]

    sp = os.path.join(args.out, "splits")
    write_jsonl(os.path.join(sp, "train.jsonl"), train)
    write_jsonl(os.path.join(sp, "dev.jsonl"), dev)
    write_jsonl(os.path.join(sp, "test.jsonl"), test)
    digest = sha256_file(os.path.join(sp, "test.jsonl"))
    with open(os.path.join(sp, "test.sha256"), "w") as fh:
        fh.write(f"{digest}  test.jsonl\n")

    by_ap = collections.Counter(r["airport"] for r in rows)
    print(f"segments: {len(rows)}  by airport: {dict(by_ap)}")
    print(f"train {len(train)} / dev {len(dev)} / test {len(test)}  (test airports: {args.test_airports})")
    print(f"test.jsonl sha256: {digest}")


if __name__ == "__main__":
    main()
