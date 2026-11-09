from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import requests
from pathlib import Path
import os, psycopg
base="http://127.0.0.1:8765"
data={"recurso":78,"inicio":"2040-01-01T12:00:00Z","fin":"2040-01-01T13:00:00Z"}
def verify(label, observed, expected):
    print(f"{label}: {observed}; esperado {expected}",flush=True)
    assert observed == expected
def run():
    with psycopg.connect(os.environ.get('DATABASE_URL') or Path('.dsn').read_text(),autocommit=True) as db:
        db.execute("DELETE FROM reservas WHERE recurso=78 AND inicio >= '2040-01-01' AND inicio < '2040-01-02'")
        def get(path,params=None):
            return requests.get(base+path,params=params,timeout=5)
        def post(body):
            return requests.post(base+"/reservas",json=body,timeout=5)
        verify("Libre al inicio",get("/disponibilidad",data).json()["disponible"],True)
        barrier=Barrier(2)
        def race(_):
            barrier.wait()
            return post(data).status_code
        with ThreadPoolExecutor(2) as pool:
            verify("Dos altas concurrentes",sorted(pool.map(race, range(2))),[201,409])
        verify("Reservas persistidas",db.execute("SELECT count(*) FROM reservas WHERE recurso=78 AND inicio=%s",(data['inicio'],)).fetchone()[0],1)
        verify("Disponibilidad posterior",get("/disponibilidad",data).json()["disponible"],False)
        verify("Intervalo contiguo",post(dict(data,inicio=data["fin"],fin="2040-01-01T14:00:00Z")).status_code,201)
        verify("Intervalo invertido",post(dict(data,fin=data["inicio"])).status_code,400)
        verify("Recurso inexistente",post(dict(data,recurso=999)).status_code,404)
        verify("Paginación inválida",get("/reservas",{"pagina":0}).status_code,400)
        a,b=(get("/reservas",{"pagina":i,"limite":5}).json()["reservas"] for i in (1,2))
        both=a+b
        verify("Páginas completas y sin duplicados",len(set(x["id"] for x in both)),10)
        verify("Orden estable entre páginas",both,sorted(both,key=lambda x:(x["inicio"],x["id"]),reverse=True)) if both!=sorted(both,key=lambda x:(x["inicio"],x["id"]),reverse=True) else print("Orden estable entre páginas: OK")
if __name__=="__main__":
    run()
