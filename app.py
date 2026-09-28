from flask import Flask, jsonify, request
from threading import Lock
app=Flask(__name__); lock=Lock()
state={"participant_count":0,"participants":[],"current":-1,"finished":False,"version":0}
def bump(): state["version"]+=1

CSS='''*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:radial-gradient(circle at 12% 8%,#0b2a16 0,transparent 28%),#030604;color:#f6fff8;font-family:Arial,sans-serif}body:before{content:"";position:fixed;inset:0;pointer-events:none;box-shadow:inset 0 0 130px rgba(37,240,111,.08)}button,input{font:inherit}.brand{font-weight:900;letter-spacing:.06em}.m{border:2px solid #25f06f;padding:.2em .45em;box-shadow:0 0 22px rgba(37,240,111,.25)}.slash{color:#25f06f;padding:0 .3em}.w{color:#777}'''

CONTROL='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Шарики — управление</title><style>'''+CSS+'''
.wrap{max-width:1050px;margin:auto;padding:28px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}.brand{font-size:22px}.tag{color:#25f06f;font-weight:900}.card{background:#09110c;border:1px solid #173523;border-radius:24px;padding:26px}.setup{display:flex;gap:14px;align-items:end;flex-wrap:wrap}label{display:block;color:#829287;font-size:13px;margin-bottom:8px}input{width:180px;background:#020503;color:#fff;border:1px solid #275237;border-radius:14px;padding:15px;font-size:22px}button{border:0;border-radius:15px;padding:15px 20px;font-weight:900;cursor:pointer}.primary,.plus{background:#25f06f;color:#021006}.danger{background:#291014;color:#ff9aa4}.game{display:none;margin-top:22px}.now{display:grid;grid-template-columns:1fr auto;align-items:center;padding:26px;border:1px solid #245536;border-radius:22px}.name{font-size:clamp(34px,6vw,68px);font-weight:900}.score{font-size:clamp(70px,12vw,130px);font-weight:900;color:#25f06f}.actions{display:grid;grid-template-columns:1fr 150px;gap:14px;margin-top:16px}.plus{min-height:115px;font-size:38px}.minus{font-size:26px;background:#18241c;color:#fff}.next{width:100%;margin-top:14px;background:#fff;color:#061009;font-size:20px}.row{display:flex;justify-content:space-between;padding:12px 4px;border-bottom:1px solid #14251a}.row b{color:#25f06f}.done h3{color:#829287;font-size:14px}.links{margin-top:18px;color:#829287;font-size:13px}.links a{color:#25f06f}</style></head><body><div class="wrap"><div class="top"><div class="brand"><span class="m">МУЖСКОЕ</span><span class="slash">/</span><span class="w">ЖЕНСКОЕ</span></div><div class="tag">ШАРИКИ · УПРАВЛЕНИЕ</div></div><div class="card"><div class="setup"><div><label>Количество участников</label><input id="count" type="number" min="1" max="50" value="4"></div><button class="primary" onclick="startGame()">НАЧАТЬ КОНКУРС</button><button class="danger" onclick="resetGame()">СБРОСИТЬ</button></div><div class="game" id="game"><div class="now"><div><div style="color:#829287;font-weight:800">СЕЙЧАС ИГРАЕТ</div><div class="name" id="name"></div></div><div class="score" id="score"></div></div><div class="actions"><button class="plus" onclick="change(1)">+1 ШАРИК</button><button class="minus" onclick="change(-1)">−1</button></div><button class="next" onclick="nextP()">СЛЕДУЮЩИЙ УЧАСТНИК →</button><div class="done"><h3>УЖЕ СЫГРАЛИ</h3><div id="done"></div></div></div><div class="links">Зрительский экран: <a href="/screen" target="_blank">открыть /screen</a></div></div></div><script>
async function post(p,b={}){await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});refresh()}
function startGame(){let n=parseInt(count.value);if(n>0)post('/api/start',{count:n})}function resetGame(){if(confirm('Сбросить весь конкурс?'))post('/api/reset')}function change(delta){post('/api/score',{delta})}function nextP(){post('/api/next')}
async function refresh(){let s=await(await fetch('/api/state')).json();game.style.display=s.participant_count?'block':'none';if(s.participant_count){if(!s.finished){let p=s.participants[s.current];name.textContent=p.name;score.textContent=p.score}else{name.textContent='КОНКУРС ЗАВЕРШЁН';score.textContent='✓'}done.innerHTML=s.participants.slice(0,s.finished?s.participants.length:s.current).map(p=>`<div class="row"><span>${p.name}</span><b>${p.score}</b></div>`).join('')}}refresh();setInterval(refresh,1000)</script></body></html>'''

SCREEN='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Шарики — экран</title><style>'''+CSS+'''
html,body{height:100%;overflow:hidden}.screen{height:100vh;padding:4vh 5vw;display:flex;flex-direction:column}.header{display:flex;justify-content:space-between;align-items:center}.brand{font-size:clamp(16px,2vw,30px)}.contest{font-size:clamp(18px,2vw,32px);font-weight:900;color:#25f06f;letter-spacing:.16em}.main{flex:1;display:grid;grid-template-columns:1fr .65fr;align-items:center;gap:5vw;border-bottom:1px solid #173523}.who small{display:block;color:#7e9184;font-size:clamp(15px,1.4vw,24px);font-weight:800;letter-spacing:.14em;margin-bottom:2vh}.name{font-size:clamp(50px,7.5vw,145px);font-weight:900;line-height:.9}.score{font-size:clamp(130px,22vw,390px);font-weight:900;color:#25f06f;text-align:right;line-height:.75;text-shadow:0 0 55px rgba(37,240,111,.3);transition:.12s}.score.pop{transform:scale(1.08)}.history{min-height:17vh;padding-top:2vh}.history-title{color:#65756a;font-size:clamp(12px,1.1vw,18px);font-weight:800;letter-spacing:.15em;margin-bottom:1.3vh}.history-list{display:flex;gap:1.2vw;flex-wrap:wrap}.pill{background:#09130d;border:1px solid #173523;border-radius:14px;padding:.8vh 1vw;color:#aebbb2;font-size:clamp(14px,1.3vw,22px)}.pill b{color:#fff;margin-left:.7vw}.empty{color:#415046}</style></head><body><div class="screen"><div class="header"><div class="brand"><span class="m">МУЖСКОЕ</span><span class="slash">/</span><span class="w">ЖЕНСКОЕ</span></div><div class="contest">ШАРИКИ</div></div><div class="main"><div class="who"><small id="caption">СЕЙЧАС ИГРАЕТ</small><div class="name" id="name">ОЖИДАНИЕ</div></div><div class="score" id="score">0</div></div><div class="history"><div class="history-title">РЕЗУЛЬТАТЫ</div><div class="history-list" id="history"><span class="empty">Участники ещё не играли</span></div></div></div><script>
let old=null;async function refresh(){try{let s=await(await fetch('/api/state',{cache:'no-store'})).json();if(!s.participant_count){caption.textContent='ГОТОВИМСЯ К КОНКУРСУ';name.textContent='ОЖИДАНИЕ';score.textContent='0'}else if(!s.finished){let p=s.participants[s.current];caption.textContent='СЕЙЧАС ИГРАЕТ';name.textContent=p.name;if(old!==null&&old!==p.score){score.classList.add('pop');setTimeout(()=>score.classList.remove('pop'),140)}score.textContent=p.score;old=p.score}else{caption.textContent='';name.textContent='КОНКУРС ЗАВЕРШЁН';score.textContent='✓'}let a=s.finished?s.participants:s.participants.slice(0,Math.max(0,s.current));history.innerHTML=a.length?a.map(p=>`<span class="pill">${p.name}<b>${p.score}</b></span>`).join(''):'<span class="empty">Участники ещё не играли</span>'}catch(e){}}refresh();setInterval(refresh,350)</script></body></html>'''

@app.get("/")
def control(): return CONTROL
@app.get("/screen")
def screen(): return SCREEN
@app.get("/api/state")
def get_state():
    with lock: return jsonify(state)
@app.post("/api/start")
def start():
    d=request.get_json(silent=True) or {}; n=max(1,min(50,int(d.get("count",1))))
    with lock:
        state.update(participant_count=n,participants=[{"name":f"УЧАСТНИК {i+1}","score":0} for i in range(n)],current=0,finished=False); bump(); return jsonify(state)
@app.post("/api/score")
def score_api():
    d=request.get_json(silent=True) or {}; delta=1 if int(d.get("delta",1))>0 else -1
    with lock:
        i=state["current"]
        if 0<=i<len(state["participants"]) and not state["finished"]: state["participants"][i]["score"]=max(0,state["participants"][i]["score"]+delta); bump()
        return jsonify(state)
@app.post("/api/next")
def next_api():
    with lock:
        if state["participant_count"] and not state["finished"]:
            if state["current"]+1<state["participant_count"]: state["current"]+=1
            else: state["finished"]=True
            bump()
        return jsonify(state)
@app.post("/api/reset")
def reset():
    with lock: state.update(participant_count=0,participants=[],current=-1,finished=False); bump(); return jsonify(state)
if __name__=="__main__":
    import os; app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
