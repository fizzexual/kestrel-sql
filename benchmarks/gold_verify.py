"""Check the analytical SQL against the pipeline's silver source and daily gold."""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, help="Defaults to pipeline.duckdb in the directory recorded by nyc_pipeline.py")
    parser.add_argument("--output", type=Path, default=ROOT / "portfolio" / "gold-verification.json")
    args = parser.parse_args()
    if args.database is None:
        pipeline = json.loads((ROOT / "benchmarks" / "nyc-results.json").read_text(encoding="utf-8"))
        args.database = Path(pipeline["pipeline_directory"]) / "pipeline.duckdb"
    import duckdb
    db = duckdb.connect(str(args.database.resolve()), read_only=True)
    db.execute("SET threads=1")
    assert db.execute("SELECT COUNT(*)=COUNT(DISTINCT LocationID) AND COUNT(*)=COUNT(LocationID) FROM zones").fetchone()[0]
    result = db.execute((ROOT / "portfolio" / "gold_analysis.sql").read_text()).fetchall()
    columns = [c[0] for c in db.description]
    expected = db.execute("SELECT COUNT(*), SUM(value) FROM silver").fetchone()
    assert sum(r[2] for r in result) == expected[0]
    assert sum(r[3] for r in result) == expected[1]
    by_borough = {}
    for row in result:
        by_borough.setdefault(row[1], []).append(row)
    for rows in by_borough.values():
        assert len(rows) == 31
        assert rows[0][0] == date(2025, 1, 1) and rows[0][4] is None
        for previous, current in zip(rows, rows[1:]):
            assert current[0] == previous[0] + timedelta(days=1)
            assert current[4] == previous[2]
            assert current[6] == current[2] - previous[2]
    # Independent daily aggregation catches lost or duplicated dimension joins.
    daily = db.execute("""SELECT CAST(to_timestamp(ts) AT TIME ZONE 'America/New_York' AS DATE),
        COUNT(*), SUM(value) FROM silver GROUP BY 1""").fetchall()
    for day, trips, total in daily:
        selected = [row for row in result if row[0] == day]
        assert sum(row[2] for row in selected) == trips
        assert sum(row[3] for row in selected) == total
        charges = sorted({row[3] for row in selected}, reverse=True)
        assert all(row[5] == charges.index(row[3])+1 for row in selected)
    report = {"duckdb_version": duckdb.__version__, "query": "portfolio/gold_analysis.sql",
        "rows": len(result), "boroughs": len(by_borough), "calendar_days_per_borough": 31,
        "silver_trip_count": expected[0], "silver_total_charged_cents": expected[1],
        "checks": {"zone_key_unique_nonnull": True, "counts_and_sums_reconcile": True,
            "daily_join_reconciliation": True, "lag_uses_complete_calendar": True,
            "dense_rank_matches_independent_order": True}, "columns": columns,
        "first_day": [[str(r[0]), *r[1:]] for r in result if r[0] == date(2025,1,1)]}
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="first_day"}, indent=2))
    db.close()


if __name__ == "__main__":
    main()
