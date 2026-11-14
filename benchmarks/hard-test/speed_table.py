"""Print the speed result as Markdown tables: python speed_table.py [result-speed.json]"""
import json
import os
import sys

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "result-speed.json")
report = json.load(open(path, encoding="utf-8"))
engines = [name for name, entry in report["engines"].items() if "error" not in entry]
failed = {name: entry["error"] for name, entry in report["engines"].items() if "error" in entry}


def fmt(ms):
    if ms is None:
        return "-"
    if ms < 1:
        return "%.3f" % ms
    if ms < 100:
        return "%.1f" % ms
    return "%.0f" % ms


print("base rows %d, late rows %d" % (report["base_rows"], report["late_rows"]))
print("setup seconds: " + ", ".join("%s %s" % (n, report["engines"][n].get("setup_s")) for n in engines))
print("late insert seconds: " + ", ".join("%s %s" % (n, report["engines"][n].get("late_insert_s")) for n in engines))
if failed:
    print("FAILED engines: " + json.dumps(failed))
native = report.get("kestrel_database_in_process_us")
if native:
    print("kestrel Database in-process (own timer, microseconds): " +
          ", ".join("%s %.1f" % (k, v["median_us"]) for k, v in native.items()))

for phase, title in (("ordered", "Phase A: time in order"), ("late", "Phase B: after the late rows")):
    print("\n### %s  (median milliseconds, client-observed)\n" % title)
    print("| query | " + " | ".join(engines) + " |")
    print("| --- |" + " ---: |" * len(engines))
    first = report["engines"][engines[0]]
    for shape in first[phase + "_fixed"]:
        cells = [fmt(report["engines"][n][phase + "_fixed"][shape]["median_ms"]) for n in engines]
        print("| fixed: %s | %s |" % (shape, " | ".join(cells)))
    for group in first[phase + "_sets"]:
        cells = [fmt(report["engines"][n][phase + "_sets"][group]["median_ms"]) for n in engines]
        count = first[phase + "_sets"][group]["queries"]
        print("| %d random: %s | %s |" % (count, group, " | ".join(cells)))
    for group in first[phase + "_sets"]:
        cells = [fmt(report["engines"][n][phase + "_sets"][group]["p95_ms"]) for n in engines]
        print("| p95: %s | %s |" % (group, " | ".join(cells)))
    disagree = {}
    for n in engines:
        entry = report["engines"][n]
        bad = sum(v["queries"] - v["agree"] for v in entry[phase + "_sets"].values())
        bad += sum(not v["agree"] for v in entry[phase + "_fixed"].values())
        disagree[n] = bad
    print("\nanswers differing from DuckDB: " + ", ".join("%s %d" % item for item in disagree.items()))
