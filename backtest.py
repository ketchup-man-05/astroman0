"""
backtest.py - replay documented KP horary cases through the engine and score the verdicts.

    python backtest.py cases.json                      # both chart-time modes
    python backtest.py cases.json --modes query        # one mode only

Each case needs the moment the question was asked (UTC), the place, the KP number and the
KNOWN outcome. Cases with "enabled": false are skipped. NEVER invent cases - use published ones.
"""
import argparse, csv, json, math, sys
from datetime import datetime, timezone
import chart_caster

# Same topic table as ai_narrator.py (copied so this script doesn't need Streamlit).
# name: (positive houses, negative houses, key house)
TOPICS = {
    "career":   ([2, 6, 10, 11], [1, 5, 9, 12], 10),
    "marriage": ([2, 7, 11],     [1, 6, 10],    7),
    "travel":   ([3, 9, 12],     [2, 4, 11],    12),
    "health":   ([1, 5, 11],     [6, 8, 12],    6),
    "property": ([4, 11, 12],    [3, 10],       4),
    "exam":     ([4, 9, 11],     [3, 8],        4),
    "children": ([2, 5, 11],     [1, 4, 10],    5),
    "court":    ([6, 11],        [12],          6),
    "general":  ([2, 11],        [8, 12],       11),
}

def verdict_class(verdict):
    v = verdict.upper()
    if v.startswith("DELAYED"):
        return "DELAYED"
    if v.startswith("MIXED"):
        return "MIXED"
    if v.startswith("UNFAVORABLE") or v.startswith("DEFINITIVE NO") or v.startswith("NO"):
        return "NO"
    return "YES"

def wilson(k, n, z=1.96):
    """95% confidence interval for k successes out of n."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)

def run_case(case, mode):
    if case.get("topic"):
        pos, neg, key = TOPICS[case["topic"]]
    else:
        pos, neg, key = case["positive"], case["negative"], case["key_house"]
    as_of = datetime.fromisoformat(case["query_utc"].replace("Z", "+00:00"))
    coords = (case["lat"], case["lon"])
    r = chart_caster.execute_kp_reading(case.get("city", "n/a"), int(case["number"]), pos, neg, key,
                                        as_of=as_of, coords=coords, chart_time_mode=mode, log=False,
                                        include_timing=False)
    if "error" in r:
        return {"error": r["error"]}
    return {"verdict": r["verdict"], "cls": verdict_class(r["verdict"]), "score": r["kp_score"],
            "deciding": r["deciding_planet"], "retro": r["is_retrograde"]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("--modes", nargs="+", default=["query", "horary"], choices=["query", "horary"])
    ap.add_argument("--out", default="backtest_results.csv")
    args = ap.parse_args()

    cases = [c for c in json.load(open(args.cases, encoding="utf-8")) if c.get("enabled", True)]
    cases = [c for c in cases if c.get("expected") in ("YES", "NO")]
    if not cases:
        print("No usable cases (need enabled cases with expected = YES or NO). See cases.json.")
        sys.exit(1)

    rows = []
    print(f"\n{len(cases)} cases\n")
    for mode in args.modes:
        hit = wrong = mixed = delayed = err = 0
        print(f"=== mode: {mode} ===")
        for c in cases:
            try:
                res = run_case(c, mode)
            except Exception as e:
                res = {"error": f"{type(e).__name__}: {e}"}
            if "error" in res:
                err += 1
                print(f"  {c['id']:<14} ERROR {res['error']}")
                rows.append([mode, c["id"], c["expected"], "ERROR", "", "", res["error"]])
                continue
            if res["cls"] == "MIXED":
                mixed += 1; tag = "mixed"
            elif res["cls"] == "DELAYED":
                # DELAYED means the chart leans negative but the deciding planet/star is retrograde;
                # this project reads that as "not yet", not a clean NO, so it is left undecided here
                # rather than scored as a miss against an "expected NO" case.
                delayed += 1; tag = "delayed"
            elif res["cls"] == c["expected"]:
                hit += 1; tag = "HIT"
            else:
                wrong += 1; tag = "MISS"
            print(f"  {c['id']:<14} expected {c['expected']:<3} got {res['cls']:<8} score {res['score']:+d}  [{tag}]")
            rows.append([mode, c["id"], c["expected"], res["cls"], res["score"], res["deciding"], res["verdict"]])

        decided = hit + wrong
        lo, hi = wilson(hit, decided)
        yes_rate = sum(1 for c in cases if c["expected"] == "YES") / len(cases)
        print(f"  -> decided {decided}/{len(cases)} (mixed {mixed}, delayed {delayed}, errors {err})")
        if decided:
            print(f"  -> accuracy on decided cases: {hit}/{decided} = {hit/decided:.0%}  (95% CI {lo:.0%}-{hi:.0%})")
        print(f"  -> baseline: always answering the majority outcome scores {max(yes_rate, 1-yes_rate):.0%}\n")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mode", "case", "expected", "got", "score", "deciding_planet", "verdict"])
        w.writerows(rows)
    print(f"Saved {args.out}")

if __name__ == "__main__":
    main()