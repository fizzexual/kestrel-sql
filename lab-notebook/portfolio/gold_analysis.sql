-- Run with DuckDB against the pipeline database created by nyc_pipeline.py.
-- These joins and window functions are part of the data pipeline; Archive
-- deliberately implements only the aggregate SQL documented in ARCHIVE.md.
WITH borough_daily AS (
    SELECT
        CAST(to_timestamp(s.ts) AT TIME ZONE 'America/New_York' AS DATE) AS service_day,
        z.Borough AS borough,
        COUNT(*) AS trips,
        SUM(s.value) AS total_charged_cents
    FROM silver AS s
    JOIN zones AS z ON s.device = z.LocationID
    GROUP BY 1, 2
), calendar AS (
    SELECT CAST(d AS DATE) AS service_day
    FROM generate_series(DATE '2025-01-01', DATE '2025-01-31', INTERVAL '1 day') AS t(d)
), boroughs AS (
    SELECT DISTINCT Borough AS borough FROM zones
), daily_spine AS (
    SELECT c.service_day, b.borough,
        COALESCE(a.trips, 0) AS trips,
        COALESCE(a.total_charged_cents, 0) AS total_charged_cents
    FROM calendar AS c
    CROSS JOIN boroughs AS b
    LEFT JOIN borough_daily AS a
        ON c.service_day = a.service_day AND b.borough IS NOT DISTINCT FROM a.borough
), changes AS (
    SELECT *,
        LAG(trips) OVER (PARTITION BY borough ORDER BY service_day) AS previous_day_trips,
        DENSE_RANK() OVER (
            PARTITION BY service_day ORDER BY total_charged_cents DESC
        ) AS daily_charge_rank
    FROM daily_spine
)
SELECT *,
    trips - previous_day_trips AS trip_change,
    ROUND(100.0 * (trips - previous_day_trips) / NULLIF(previous_day_trips, 0), 2)
        AS trip_change_percent
FROM changes
ORDER BY service_day, daily_charge_rank, borough;
