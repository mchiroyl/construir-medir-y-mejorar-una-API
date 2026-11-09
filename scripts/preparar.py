"""Instalar la semilla una sola vez o restaurar las filas de prueba."""
import argparse, os
from pathlib import Path
import psycopg

parser=argparse.ArgumentParser()
parser.add_argument("accion",choices=["instalar","restablecer","diagnosticar","corregir"])
args=parser.parse_args()
with psycopg.connect(os.environ.get("DATABASE_URL") or Path(".dsn").read_text().strip(),autocommit=True) as c:
    if c.execute("SELECT current_database()").fetchone()[0]!="s15_reservas":
        raise SystemExit("Use exclusivamente la base de práctica s15_reservas")
    if args.accion=="instalar":
        c.execute(Path("db/schema.sql").read_text(encoding="utf-8"))
    elif args.accion=="restablecer":
        c.execute("DELETE FROM reservas WHERE id>80000")
        c.execute("ALTER TABLE reservas ALTER COLUMN id RESTART WITH 80001")
        c.execute("VACUUM ANALYZE reservas")
    elif args.accion=="corregir":
        c.execute(Path("db/mejora.sql").read_text(encoding="utf-8"))
        c.execute("ANALYZE reservas")
    else:
        for row in c.execute("EXPLAIN (ANALYZE,BUFFERS) SELECT id,recurso,inicio,fin FROM reservas ORDER BY inicio DESC,id DESC LIMIT 10 OFFSET 10"):
            print(row[0])
    print("Recursos y reservas:",c.execute("SELECT (SELECT count(*) FROM recursos),count(*) FROM reservas").fetchone())
