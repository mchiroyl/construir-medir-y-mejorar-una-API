import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';

const mode = __ENV.MODO || 'humo';
const definitions = {humo:[['humo',1,20]], carga:[['carga',5,60]],
  estres:[['base',2,20],['normal',5,20],['media',10,20],['pico',15,20],['recuperacion',2,20]]};
const scenarios = {};
let start = 0;
for (const [name,rate,seconds] of definitions[mode]) {
  scenarios[name]={executor:'constant-arrival-rate', rate, timeUnit:'1s', duration:seconds+'s',
    startTime:start+'s', preAllocatedVUs:mode==='estres'?2:4, maxVUs:mode==='estres'?4:16, gracefulStop:'2s'};
  start+=seconds;
}
const thresholds={checks:['rate>=0.99'],http_req_failed:['rate<0.01',{threshold:'rate<0.05',abortOnFail:true,delayAbortEval:'10s'}],
  dropped_iterations:['count==0']};
for (const op of ['disponibilidad','listado','crear'])
  thresholds['http_req_duration{op:'+op+'}']=['p(95)<'+(op==='crear'?500:300)];
if(mode==='estres') thresholds['http_req_duration{scenario:recuperacion}']=['p(95)<300'];
export const options={scenarios,thresholds,systemTags:['scenario','method','status','name','expected_response'],summaryTrendStats:['avg','med','p(95)','p(99)','max']};
const base='http://127.0.0.1:8765';
export default function(){
  const i=exec.scenario.iterationInTest, pos=i%20;
  const op=pos<12?'disponibilidad':pos<17?'listado':'crear';
  const params={timeout:'2s',tags:{op,name:op},headers:{'Content-Type':'application/json'}};
  let ok=false;
  if(op==='disponibilidad'){
    const day=i%2?'2028-01-01':'2026-01-01';
    const r=http.get(base+'/disponibilidad?recurso=1&inicio='+day+'T00:00:00Z&fin='+day+'T00:10:00Z',params);
    ok=r.status===200 && r.json('disponible')===(i%2===1);
  } else if(op==='listado'){
    const page=1+i%2, r=http.get(base+'/reservas?pagina='+page+'&limite=10',params);
    if(r.status===200){
      const rows=r.json('reservas');
      ok=r.json('pagina')===page && rows.length===10 && rows.every((x,j)=>!j || rows[j-1].inicio>x.inicio || (rows[j-1].inicio===x.inicio && rows[j-1].id>x.id));
    }
  } else {
    const index=Object.keys(scenarios).indexOf(exec.scenario.name)*10000+i;
    const t=Date.UTC(2030,0,1)+index*60000;
    const r=http.post(base+'/reservas',JSON.stringify({recurso:1,inicio:new Date(t).toISOString(),fin:new Date(t+60000).toISOString()}),params);
    ok=r.status===201 && r.json('id')>80000 && r.json('recurso')===1 && Date.parse(r.json('inicio'))===t;
  }
  check(ok,{[op+' cumple el contrato']:v=>v});
}
