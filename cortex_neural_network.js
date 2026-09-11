/* TJ Cortex Neural Network — real communication events only. */
(() => {
  "use strict";

  const LAYOUT = {
    CEO:[.50,.50], Intelligence:[.50,.14], Product:[.72,.24], "Agent Factory":[.86,.50],
    Growth:[.72,.76], Communications:[.50,.86], Commerce:[.28,.76], Finance:[.14,.50],
    Guard:[.28,.24], Memory:[.50,.33]
  };
  const ALIASES = {
    ceo:"CEO", cortex:"CEO", "cortex ceo":"CEO", research:"Intelligence", intelligence:"Intelligence",
    "cortex intelligence":"Intelligence", product:"Product", "product agent":"Product",
    agents:"Agent Factory", "agent factory":"Agent Factory", growth:"Growth", prospecting:"Growth",
    "cortex growth":"Growth", communications:"Communications", communication:"Communications",
    commerce:"Commerce", orders:"Commerce", finance:"Finance", guard:"Guard", "cortex guard":"Guard",
    memory:"Memory", "cortex memory":"Memory"
  };
  const COLORS = {
    CEO:"#39e7ff", Intelligence:"#6ca8ff", Product:"#a56cff", "Agent Factory":"#ff6cd9",
    Growth:"#52f2a3", Communications:"#ffd166", Commerce:"#55d6be", Finance:"#7ce7ff",
    Guard:"#ff7f7f", Memory:"#c18cff"
  };
  const MAX_EVENTS = 120;
  const text = (v, fallback="?") => (v === null || v === undefined || v === "" ? fallback : String(v).slice(0,500));
  const agent = v => {
    if (typeof v !== "string") return null;
    const k = v.trim().toLowerCase();
    return ALIASES[k] || (Object.prototype.hasOwnProperty.call(LAYOUT,v) ? v : null);
  };
  const clamp = (v,a,b) => Math.max(a,Math.min(b,v));

  class NeuralNetwork {
    constructor(root) {
      this.root=root;
      this.canvas=root.querySelector("canvas");
      this.ctx=this.canvas.getContext("2d");
      this.status=root.querySelector("[data-neural-status]");
      this.count=root.querySelector("[data-neural-count]");
      this.inspector=root.querySelector("[data-neural-inspector]");
      this.nodes=Object.keys(LAYOUT).map(name=>({name,x:LAYOUT[name][0],y:LAYOUT[name][1],glow:0,hover:false}));
      this.events=[]; this.seen=new Set(); this.packets=[]; this.edges=[];
      this.reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches || false;
      this.resizeObserver=new ResizeObserver(()=>this.resize());
      this.resizeObserver.observe(root);
      this.canvas.addEventListener("mousemove",e=>this.hover(e));
      this.canvas.addEventListener("click",e=>this.inspect(e));
      this.resize(); this.poll(); requestAnimationFrame(t=>this.frame(t));
    }
    resize(){
      const r=this.canvas.getBoundingClientRect(), d=Math.max(1,Math.min(2,devicePixelRatio||1));
      this.canvas.width=Math.max(1,Math.floor(r.width*d)); this.canvas.height=Math.max(1,Math.floor(r.height*d));
      this.ctx.setTransform(d,0,0,d,0,0); this.width=r.width; this.height=r.height;
    }
    point(n){return{x:n.x*this.width,y:n.y*this.height};}
    rebuildEdges(){
      const pairs=new Set();
      for(const e of this.events){const a=agent(e.sender),b=agent(e.recipient);if(a&&b&&a!==b)pairs.add([a,b].sort().join("|"));}
      this.edges=[...pairs].map(k=>{const [a,b]=k.split("|");return{a,b,pulse:0};});
    }
    ingest(list,live){
      if(!Array.isArray(list)) return;
      for(const e of [...list].reverse()){
        const id=text(e.id||e.event_id||`${e.timestamp}|${e.sender}|${e.recipient}|${e.summary}`,"event");
        if(this.seen.has(id)) continue;
        this.seen.add(id); this.events.push(e); if(this.events.length>MAX_EVENTS)this.events.shift();
        const a=agent(e.sender),b=agent(e.recipient);
        if(a&&b&&a!==b){this.packets.push({a,b,start:performance.now(),duration:this.reduced?1:950+Math.random()*500,status:text(e.status,"sent")});}
      }
      this.rebuildEdges();
      if(this.count)this.count.textContent=`${this.events.length} observed events`;
      if(this.status)this.status.textContent=live?"LIVE BUS":"BUS IDLE";
    }
    async poll(){
      try{const r=await fetch("/api/communications?limit=50",{cache:"no-store"});if(!r.ok)throw new Error();const p=await r.json();this.ingest(p.events,Boolean(p.stream?.live_stream_ready));}
      catch(_){if(this.status)this.status.textContent="BUS UNAVAILABLE";}
      finally{setTimeout(()=>this.poll(),1500);}
    }
    background(t){
      const c=this.ctx;c.clearRect(0,0,this.width,this.height);
      const g=c.createRadialGradient(this.width*.5,this.height*.5,10,this.width*.5,this.height*.5,Math.max(this.width,this.height)*.7);
      g.addColorStop(0,"rgba(22,38,74,.42)");g.addColorStop(.55,"rgba(7,13,29,.62)");g.addColorStop(1,"rgba(3,6,15,.96)");c.fillStyle=g;c.fillRect(0,0,this.width,this.height);
      if(!this.reduced){for(let i=0;i<28;i++){const x=((i*97)%1000)/1000*this.width,y=((i*173+t*.01)%1000)/1000*this.height;c.fillStyle="rgba(93,177,255,.16)";c.fillRect(x,y,1.2,1.2);}}
    }
    edgesDraw(){
      const c=this.ctx;
      for(const e of this.edges){const a=this.nodes.find(n=>n.name===e.a),b=this.nodes.find(n=>n.name===e.b);if(!a||!b)continue;const p=this.point(a),q=this.point(b);
        c.beginPath();c.moveTo(p.x,p.y);c.lineTo(q.x,q.y);c.strokeStyle=`rgba(72,141,210,${.18+e.pulse*.4})`;c.lineWidth=1+e.pulse;c.stroke();
      }
    }
    packetsDraw(now){
      const c=this.ctx,keep=[];
      for(const p of this.packets){const a=this.nodes.find(n=>n.name===p.a),b=this.nodes.find(n=>n.name===p.b);if(!a||!b)continue;const u=clamp((now-p.start)/p.duration,0,1),e=u*u*(3-2*u),x=this.point(a),y=this.point(b),px=x.x+(y.x-x.x)*e,py=x.y+(y.y-x.y)*e;
        const bad=p.status==="failed"||p.status==="denied";c.shadowBlur=18;c.shadowColor=bad?COLORS.Guard:COLORS.CEO;c.fillStyle=bad?COLORS.Guard:COLORS.CEO;c.beginPath();c.arc(px,py,4,0,Math.PI*2);c.fill();c.shadowBlur=0;if(u<1)keep.push(p);
      }this.packets=keep;
    }
    nodesDraw(){
      const c=this.ctx;
      for(const n of this.nodes){const p=this.point(n),color=COLORS[n.name],r=n.name==="CEO"?32:23,g=clamp(n.glow,0,1);n.glow*=.94;
        if(g>.01||n.hover){c.shadowBlur=28+g*28;c.shadowColor=color;}c.fillStyle="rgba(6,12,25,.96)";c.strokeStyle=color;c.lineWidth=n.name==="CEO"?2.2:1.3;c.beginPath();c.arc(p.x,p.y,r+g*5,0,Math.PI*2);c.fill();c.stroke();c.shadowBlur=0;c.fillStyle=color;c.font=n.name==="CEO"?"700 12px system-ui":"600 10px system-ui";c.textAlign="center";c.textBaseline="middle";c.fillText(n.name.toUpperCase(),p.x,p.y);
      }
    }
    hit(e){const r=this.canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;return this.nodes.find(n=>{const p=this.point(n);return Math.hypot(x-p.x,y-p.y)<(n.name==="CEO"?40:31);})||null;}
    hover(e){const n=this.hit(e);for(const x of this.nodes)x.hover=x===n;this.canvas.style.cursor=n?"pointer":"default";}
    inspect(e){const n=this.hit(e);if(!n){this.inspector.innerHTML='<span class="muted">Select an agent node to inspect its latest observed communications.</span>';return;}
      const rows=this.events.filter(x=>agent(x.sender)===n.name||agent(x.recipient)===n.name).slice(-5).reverse();
      const html=rows.map(x=>`<div class="neural-detail"><span>${text(x.sender)} → ${text(x.recipient)}</span><small>${text(x.summary,"event")}</small></div>`).join("");
      this.inspector.innerHTML=`<strong>${text(n.name)}</strong><div class="muted">${rows.length} recent related events</div>${html||'<div class="muted">No communication event observed yet.</div>'}`;
    }
    frame(t){this.background(t);this.edgesDraw();this.packetsDraw(t);this.nodesDraw();requestAnimationFrame(x=>this.frame(x));}
  }

  const api = async (url, options={}) => {
    const r=await fetch(url,{cache:"no-store",...options});
    let body={}; try{body=await r.json();}catch(_){ }
    if(!r.ok) throw new Error(body.error||"request_failed");
    return body;
  };
  const post = (url,payload={}) => api(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});

  function mountControls(){
    const surface=[...document.querySelectorAll(".card")].find(el=>el.querySelector(".label")?.textContent?.trim()==="Command Surface");
    if(!surface||surface.dataset.cortexControls==="1")return;
    const controls=surface.querySelector(".controls"); if(!controls)return;
    surface.dataset.cortexControls="1";
    controls.innerHTML='<button class="btn" data-cortex="observe">OBSERVE</button><button class="btn" data-cortex="tick">RUN ONE CYCLE</button><button class="btn" data-cortex="pause">PAUSE</button><button class="btn" data-cortex="resume">RESUME</button>';
    const output=document.createElement("div");output.className="muted";output.dataset.cortexControlOutput="1";output.textContent="Live controls ready — external actions remain Guard-gated.";surface.appendChild(output);
    const setBusy=b=>controls.querySelectorAll("button").forEach(x=>x.disabled=b);
    controls.addEventListener("click",async e=>{
      const b=e.target.closest("button[data-cortex]");if(!b)return;const action=b.dataset.cortex;setBusy(true);
      try{
        if(action==="observe"){const r=await api("/api/command-center/live");const s=r.command_center?.scheduler||{};output.textContent=`CORTEX: scheduler ${s.paused?"PAUSED":"READY"}; cycles ${s.cycles_completed??0}`;}
        else if(action==="pause"){await post("/api/scheduler/pause");output.textContent="CORTEX: scheduler paused — autonomous ticks blocked";}
        else if(action==="resume"){await post("/api/scheduler/resume");output.textContent="CORTEX: scheduler resumed — bounded cycles available";}
        else if(action==="tick"){const r=await post("/api/scheduler/tick",{execute:false});output.textContent=r.ok?"CORTEX: governed observation cycle completed":`CORTEX: ${r.error||"cycle blocked"}`;}
        window.dispatchEvent(new CustomEvent("cortex:control-updated"));
      }catch(err){output.textContent=`CORTEX: ${err.message||"control request failed"}`;}
      finally{setBusy(false);}
    });
  }

  function init(){const root=document.querySelector("[data-neural-network]");if(root&&window.ResizeObserver)new NeuralNetwork(root);mountControls();}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
