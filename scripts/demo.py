"""Capturar un cliente de demostración que envía solicitudes reales a la API local."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

def capture():
    markup="""<meta charset='utf-8'><style>
    *{box-sizing:border-box} body{margin:28px 40px;color:#19373c;font:22px 'Segoe UI',sans-serif}h1{font-size:38px;margin:0 0 8px}p{margin:8px 0;color:#46616a}button{background:#165d62;color:white;border:0;border-radius:5px;padding:10px 22px;font-size:20px;margin:12px 6px 12px 0}pre{background:#f1f6f5;padding:12px 18px;font:19px/1.3 Consolas,monospace;margin:6px 0;white-space:pre-wrap;overflow-wrap:anywhere}
    </style><h1>Reservas de salas</h1><p>Cliente de demostración · API local en 127.0.0.1:8765</p>
    <p>Sala 80 · 1 de mayo de 2045 · 14:00 a 15:00 UTC</p><button onclick="send('GET')">Consultar disponibilidad</button><button onclick="send('POST')">Reservar</button><main></main>
    <script>window.trace=[];const data={recurso:80,inicio:'2045-05-01T14:00:00Z',fin:'2045-05-01T15:00:00Z'};
    async function send(method){const path=method==='GET'?'/disponibilidad':'/reservas';
    const url=method==='GET'?path+'?'+new URLSearchParams(data):path;
    const r=await fetch(url,method==='GET'?{}:{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const b=await r.json();const entry=document.createElement('pre');
    entry.textContent=method+' '+path+'   →   HTTP '+r.status+'\\n'+JSON.stringify(b);
    document.querySelector('main').appendChild(entry);trace.push({metodo:method,url:r.url,estado:r.status,cuerpo:b});}</script>"""
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel="msedge",headless=True)
        page=browser.new_page(viewport={"width":1280,"height":630},device_scale_factor=1)
        page.route("http://127.0.0.1:8765/cliente-demo",lambda route: route.fulfill(content_type="text/html; charset=utf-8",body=markup))
        page.goto("http://127.0.0.1:8765/cliente-demo")
        for i,label in enumerate(["Consultar disponibilidad","Reservar","Consultar disponibilidad","Reservar"]):
            page.get_by_role("button",name=label,exact=True).click()
            page.wait_for_function("n=>trace.length===n",arg=i+1)
            if i in (0,1,3):
                page.locator("body").screenshot(path=str(Path("evidencias")/("01-api.png" if i==3 else f"demo-paso-{i+1}.png")))
        traces=page.evaluate("trace"); browser.close()
    assert [x["estado"] for x in traces]==[200,201,200,409]
    assert traces[0]["cuerpo"]["disponible"] and not traces[2]["cuerpo"]["disponible"]
    Path("evidencias/demo-api.json").write_text(json.dumps(traces,indent=2,ensure_ascii=False),encoding="utf8")
if __name__=="__main__": capture()
