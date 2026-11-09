"""Reconstruir la comparación a partir de los puntos originales de k6."""
import csv, gzip, json, math
from collections import defaultdict
from pathlib import Path

def percentile(values,q):
    values=sorted(values)
    x=(len(values)-1)*q
    i=math.floor(x)
    return values[i]+(values[math.ceil(x)]-values[i])*(x-i)

rows=[]
for folder in sorted(Path("resultados").glob("*/*")):
    meta=folder/"ejecucion.json"
    if not meta.exists():
        continue
    dur=defaultdict(list)
    counts=defaultdict(lambda:defaultdict(float))
    for line in gzip.open(folder/"serie.json.gz","rt",encoding="utf8"):
        item=json.loads(line)
        if item["type"]!="Point":continue
        point=item["data"]; tags=point.get("tags",{})
        phase=tags.get("scenario",""); op=tags.get("op","")
        if item["metric"]=="http_req_duration":
            for key in [(phase,op),(phase,"todas")]:
                dur[key].append(point["value"])
        if item["metric"] in ("http_req_failed","dropped_iterations","iterations","checks"):
            counts[phase][item["metric"]]+=point["value"]
    for (phase,op),values in dur.items():
        secs=60 if phase=="carga" else 20
        c=counts[phase]
        rows.append(dict(version=folder.parent.name,corrida=folder.name,fase=phase,op=op,n=len(values),
                         p50=round(percentile(values,.5),3),p95=round(percentile(values,.95),3),
                         p99=round(percentile(values,.99),3),req_por_s=round(len(values)/secs,3),
                         iteraciones=c["iterations"] if op=="todas" else "",errores=c["http_req_failed"] if op=="todas" else "",
                         descartadas=c["dropped_iterations"] if op=="todas" else "",checks_ok=c["checks"] if op=="todas" else ""))
with Path("resultados/comparacion.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
