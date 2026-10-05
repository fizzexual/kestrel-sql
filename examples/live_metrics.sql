CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL);
INSERT INTO events VALUES (100, 12, 1), (101, 18, 2), (102, 25, 1);
SELECT COUNT(*) AS events, SUM(value) AS total, AVG(value) AS average FROM events WHERE ts >= 100 AND ts < 102;
BEGIN;
INSERT INTO events VALUES (103, 40, 2);
SELECT SUM(value) AS total FROM events;
ROLLBACK;
SELECT device, SUM(value) AS total FROM events GROUP BY device ORDER BY total DESC;
