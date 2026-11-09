CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE recursos(id integer PRIMARY KEY, nombre text NOT NULL);
CREATE TABLE reservas(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 recurso integer NOT NULL REFERENCES recursos(id),
 inicio timestamptz NOT NULL, fin timestamptz NOT NULL,
 CHECK(inicio < fin),
 EXCLUDE USING gist (recurso WITH =, tstzrange(inicio,fin,'[)') WITH &&)
);
INSERT INTO recursos SELECT i,'Sala '||i FROM generate_series(1,80) AS i;
INSERT INTO reservas(recurso,inicio,fin)
SELECT 1 + i%80, t, t + interval '30 minutes'
FROM generate_series(0,79999) AS i
CROSS JOIN LATERAL (SELECT timestamptz '2026-01-01 00:00+00' + (i/80)*interval '1 hour' AS t) AS slot;
ANALYZE reservas;
