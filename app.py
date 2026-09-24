import json, os, random, sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('SMART_TOILET_DB',ROOT/'smart_toilet.db'))
def connection():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS readings (id INTEGER PRIMARY KEY, time TEXT, facility TEXT, occupancy INTEGER, air_quality INTEGER, water_level INTEGER, water_liters REAL, hours_since_clean REAL, risk INTEGER, anomaly INTEGER, alert TEXT)'); c.commit(); return c
def add(d):
 for key in ('occupancy','air_quality','water_level'):
  if type(d.get(key)) is not int or not 0<=d[key]<=100: raise ValueError(key+' must be an integer from 0 to 100')
 for key in ('water_liters','hours_since_clean'):
  if type(d.get(key)) not in (int,float) or not 0<=d[key]<=720: raise ValueError(key+' must be a number from 0 to 720')
 if not isinstance(d.get('facility'),str) or not 1<=len(d['facility'].strip())<=60: raise ValueError('facility must be 1-60 characters')
 with connection() as c:
  previous=[r[0] for r in c.execute('SELECT water_liters FROM readings WHERE facility=? ORDER BY id DESC LIMIT 20',(d['facility'],))]
  unusual=len(previous)>=5 and d['water_liters']>max(15,2.5*sum(previous)/len(previous))
  risk=min(100,min(35,int(2*d['hours_since_clean']))+min(25,int(.25*d['occupancy']))+(25 if d['air_quality']>=70 else 0)+(15 if d['water_level']<=20 else 0))
  anomaly=int(d['air_quality']>=80 or d['water_level']<=10 or unusual)
  alerts=[]
  if d['air_quality']>=80: alerts.append('Poor air quality')
  if d['water_level']<=10: alerts.append('Low water level')
  if unusual: alerts.append('Unusual water usage')
  if risk>=65: alerts.append('Cleaning or maintenance recommended')
  cur=c.execute('INSERT INTO readings (time,facility,occupancy,air_quality,water_level,water_liters,hours_since_clean,risk,anomaly,alert) VALUES (?,?,?,?,?,?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(timespec='seconds'),d['facility'].strip(),d['occupancy'],d['air_quality'],d['water_level'],d['water_liters'],d['hours_since_clean'],risk,anomaly,'; '.join(alerts) or 'Normal'))
  return dict(c.execute('SELECT * FROM readings WHERE id=?',(cur.lastrowid,)).fetchone())
def rows():
 with connection() as c: return [dict(r) for r in c.execute('SELECT * FROM readings ORDER BY id DESC LIMIT 100')]
class Handler(BaseHTTPRequestHandler):
 def reply(self,code,obj):
  body=json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
 def do_GET(self):
  if self.path=='/api/readings': return self.reply(200,rows())
  if self.path=='/api/summary':
   data=rows(); return self.reply(200,{'readings':len(data),'anomalies':sum(x['anomaly'] for x in data),'alerts':sum(x['alert']!='Normal' for x in data),'average_risk':round(sum(x['risk'] for x in data)/len(data),1) if data else 0,'water_liters':round(sum(x['water_liters'] for x in data),1)})
  if self.path=='/':
   body=(ROOT/'dashboard.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); return self.wfile.write(body)
  self.reply(404,{'error':'Not found'})
 def do_POST(self):
  if self.path!='/api/readings': return self.reply(404,{'error':'Not found'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=8192: raise ValueError('Body size invalid')
   data=json.loads(self.rfile.read(size))
   if not isinstance(data,dict): raise ValueError('Expected object')
   self.reply(201,add(data))
  except (ValueError,TypeError) as error: self.reply(400,{'error':str(error)})
if __name__=='__main__':
 connection().close()
 if not rows():
  random.seed(283)
  for i in range(40): add({'facility':['Block A','Block B'][i%2],'occupancy':random.randrange(0,101),'air_quality':random.randrange(20,90),'water_level':random.randrange(5,101),'water_liters':round(random.uniform(2,14),1),'hours_since_clean':round(random.uniform(0,28),1)})
 port=int(os.environ.get('PORT','8000')); print(f'Open http://localhost:{port}',flush=True); ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
