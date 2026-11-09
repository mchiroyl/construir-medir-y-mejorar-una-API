import argparse, csv, gzip, json, os, shutil, subprocess, time
from datetime import datetime,timezone
from pathlib import Path
import psutil, psycopg, requests

parser=argparse.ArgumentParser()
parser.add_argument("version",choices=["antes","despues"])
parser.add_argument("modo",choices=["humo","carga","estres"])
parser.add_argument("numero",type=int)
args=parser.parse_args()
dest=Path("resultados")/args.version/f"{args.modo}-{args.numero}"
dest.mkdir(parents=True,exist_ok=False)
dsn=os.environ.get("DATABASE_URL") or Path(".dsn").read_text().strip()
with psycopg.connect(dsn,autocommit=True) as c:
    assert c.execute("select current_database()").fetchone()[0]=="s15_reservas"
    c.execute("DELETE FROM reservas WHERE id>80000")
    c.execute("ALTER TABLE reservas ALTER COLUMN id RESTART WITH 80001")
    c.execute("VACUUM ANALYZE reservas")
    assert c.execute("SELECT count(*) FROM reservas").fetchone()[0]==80000
for _ in range(5):
    requests.get("http://127.0.0.1:8765/reservas",timeout=4).raise_for_status()
exe=os.environ.get("K6_BIN") or shutil.which("k6")
raw=dest/"serie.json.gz"
command=[exe,"run","--quiet","--address","127.0.0.1:0","-e","MODO="+args.modo,"--out","json="+str(raw),"k6/reservas.js"]
api_pid=next(x.pid for x in psutil.net_connections(kind="tcp") if x.laddr.port==8765 and not x.raddr)
api=psutil.Process(api_pid)
api.cpu_percent();psutil.cpu_percent()
meta=dict(commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),comando=command,inicio=datetime.now(timezone.utc).isoformat(),semilla=80000)
with (dest/"k6.txt").open("w",encoding="utf-8") as log,(dest/"recursos.csv").open("w",newline="") as samples:
    p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    k6=psutil.Process(p.pid)
    k6.cpu_percent()
    writer=csv.writer(samples)
    writer.writerow(["utc","cpu_host_pct","ram_disponible_gib","cpu_api_pct_un_nucleo","rss_api_mib","cpu_k6_pct_un_nucleo","rss_k6_mib","pg_ticks","pg_rss_suma_kib"])
    unsafe=0
    while p.poll() is None:
        time.sleep(2)
        if p.poll() is not None:
            break
        # Linux clock ticks and per-process RSS; shared pages can be counted repeatedly.
        probe="awk '$2==\"(postgres)\" {t+=$14+$15;r+=$24} END {print t+0, r*4}' /proc/[0-9]*/stat 2>/dev/null"
        pg=subprocess.run(["wsl","-d","Ubuntu","--","bash","-s"],input=probe+chr(10),capture_output=True,text=True,encoding="utf-8",errors="replace").stdout.strip().split()
        cpu=psutil.cpu_percent()
        free=psutil.virtual_memory().available/2**30
        try:
            writer.writerow([datetime.now(timezone.utc).isoformat(),cpu,free,api.cpu_percent(),api.memory_info().rss/2**20,k6.cpu_percent(),k6.memory_info().rss/2**20,*pg])
        except psutil.NoSuchProcess:
            break
        samples.flush()
        now=time.monotonic()
        if free<2 or cpu>90:
            unsafe=unsafe or now
            if now-unsafe>=10:
                meta["aborto"]="Límite de recursos del host";p.terminate();break
        else:
            unsafe=0
    meta["salida"]=p.wait()
meta["fin"]=datetime.now(timezone.utc).isoformat()
(dest/"ejecucion.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
print(dest, meta["salida"],flush=True)
raise SystemExit(0 if meta["salida"]==0 else 1)


