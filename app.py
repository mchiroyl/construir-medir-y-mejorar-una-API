import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify, abort
from psycopg.errors import ExclusionViolation, ForeignKeyViolation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from waitress import serve

def connection_string():
    return os.environ.get("DATABASE_URL") or Path(".dsn").read_text().strip()

app = Flask(__name__)
pool = ConnectionPool(connection_string(), min_size=2, max_size=8, kwargs={"row_factory":dict_row})
LIST_SQL = "SELECT id,recurso,inicio,fin FROM reservas ORDER BY inicio DESC,id DESC LIMIT %s OFFSET %s"
def interval(data):
    try:
        resource = int(str(data["recurso"]))
        start, end = (datetime.fromisoformat(str(data[key])) for key in ("inicio","fin"))
        if resource < 1 or start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError()
        return resource, start, end
    except (KeyError, ValueError, TypeError):
        abort(400)

def output(row):
    return {key: (value.astimezone(timezone.utc).isoformat() if isinstance(value,datetime) else value)
            for key,value in row.items()}

@app.get("/salud")
def health():
    with pool.connection() as c:
        c.execute("SELECT 1")
    return {"estado":"ok"}

@app.get("/disponibilidad")
def availability():
    resource, start, end = interval(request.args)
    with pool.connection() as c:
        if not c.execute("SELECT id FROM recursos WHERE id=%s",(resource,)).fetchone():
            abort(404)
        row=c.execute("SELECT NOT EXISTS(SELECT 1 FROM reservas WHERE recurso=%s AND tstzrange(inicio,fin,'[)') && tstzrange(%s,%s,'[)')) AS disponible",(resource,start,end)).fetchone()
    return row

@app.post("/reservas")
def create():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)
    values = interval(data)
    try:
        with pool.connection() as c:
            row=c.execute("INSERT INTO reservas(recurso,inicio,fin) VALUES (%s,%s,%s) RETURNING id,recurso,inicio,fin",values).fetchone()
    except ExclusionViolation:
        return {"error":"Horario ocupado"},409
    except ForeignKeyViolation:
        abort(404)
    return jsonify(output(row)),201

@app.get("/reservas")
def listing():
    try:
        page=int(request.args.get("pagina",1))
        size=int(request.args.get("limite",10))
        if not 1 <= page <= 1000000 or not 1 <= size <= 100:
            raise ValueError()
    except ValueError:
        abort(400)
    with pool.connection() as c:
        rows=c.execute(LIST_SQL,(size,(page-1)*size)).fetchall()
    return {"pagina":page,"reservas":[output(row) for row in rows]}

if __name__ == "__main__":
    serve(app,host="127.0.0.1",port=8765,threads=8)
