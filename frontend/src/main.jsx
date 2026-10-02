import React, {useEffect, useMemo, useState} from "react";
import {createRoot} from "react-dom/client";
import {Server, Plus, Activity, Send, Download, Copy, Shield, Database, RefreshCw, Trash2, KeyRound, X} from "lucide-react";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/v1";
const ADMIN_KEY = import.meta.env.VITE_ADMIN_API_KEY || "dev-admin-key";

async function req(path, options={}) {
  const headers = {"Content-Type":"application/json", ...(options.headers||{})};
  const r = await fetch(API + path, {...options, headers});
  const data = await r.json().catch(()=>({}));
  if(!r.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map(x => `${x.loc?.join(".") || "field"}: ${x.msg}`).join("; ")
      : (data.detail || data.message || `HTTP ${r.status}`);
    throw new Error(detail);
  }
  return data;
}

function App(){
  const [clients,setClients]=useState([]);
  const [selected,setSelected]=useState(null);
  const [secret,setSecret]=useState("");
  const [queues,setQueues]=useState([]);
  const [clientName,setClientName]=useState("");
  const [queueName,setQueueName]=useState("");
  const [message,setMessage]=useState("");
  const [received,setReceived]=useState([]);
  const [status,setStatus]=useState("Ready");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [showSecret,setShowSecret]=useState(false);

  const adminHeaders = {"X-Admin-Key":ADMIN_KEY};
  const clientHeaders = selected && secret ? {"X-Client-Id":selected.client_id,"X-Client-Secret":secret} : {};

  async function run(fn, success){
    setBusy(true); setError("");
    try { await fn(); if(success) setStatus(success); }
    catch(e){ setError(e.message); setStatus("Request failed"); }
    finally { setBusy(false); }
  }

  async function loadClients(){
    await run(async()=>setClients(await req("/admin/clients",{headers:adminHeaders})),"Clients loaded");
  }

  async function createClient(){
    const name=clientName.trim();
    if(!name){ setError("Client name is required"); return; }
    await run(async()=>{
      const c=await req("/admin/clients",{method:"POST",headers:adminHeaders,body:JSON.stringify({name})});
      setSelected(c); setSecret(c.client_secret); setClientName(""); setShowSecret(true);
      setQueues(await req("/queues",{headers:{"X-Client-Id":c.client_id,"X-Client-Secret":c.client_secret}}));
      setClients(await req("/admin/clients",{headers:adminHeaders}));
    },"Client created");
  }

  async function selectClient(c){
    setSelected(c); setQueues([]); setReceived([]); setError("");
    const s=window.prompt(`Enter the client secret for ${c.name}`);
    if(!s){ setStatus("Secret required to connect"); return; }
    await run(async()=>{ setSecret(s); setQueues(await req("/queues",{headers:{"X-Client-Id":c.client_id,"X-Client-Secret":s}})); },`Connected as ${c.client_id}`);
  }

  async function createQueue(){
    const name=queueName.trim();
    if(!selected || !secret){ setError("Select a client and authenticate first"); return; }
    if(!name){ setError("Queue name is required"); return; }
    await run(async()=>{
      const q=await req("/queues",{method:"POST",headers:clientHeaders,body:JSON.stringify({name,can_produce:true,can_consume:true,durable:true})});
      setQueues([...queues,q]); setQueueName("");
    },"Queue created");
  }

  async function send(q){
    if(!message.trim()){ setError("Enter a message first"); return; }
    await run(async()=>{ await req(`/messages/${encodeURIComponent(q.name)}/send`,{method:"POST",headers:clientHeaders,body:JSON.stringify({body:message})}); setMessage(""); },"Message sent");
  }

  async function receive(q){
    await run(async()=>{ const r=await req(`/messages/${encodeURIComponent(q.name)}/receive`,{headers:clientHeaders}); setReceived(r.messages||[]); },"Messages received");
  }

  async function deleteQueue(q){
    if(!window.confirm(`Delete ${q.name}?`)) return;
    await run(async()=>{ await req(`/queues/${encodeURIComponent(q.name)}`,{method:"DELETE",headers:clientHeaders}); setQueues(queues.filter(x=>x.name!==q.name)); },"Queue deleted");
  }

  useEffect(()=>{ loadClients(); },[]);

  const connectionText=useMemo(()=>selected && secret ? `STOMP · ${selected.client_id}` : "Not authenticated",[selected,secret]);

  return <div className="app">
    <aside>
      <div className="brand"><div className="logo"><Server size={19}/></div><div><b>OpenMQ</b><span>Control Plane</span></div></div>
      <button className="side active"><Activity size={17}/> Dashboard</button>
      <button className="side"><Shield size={17}/> Clients & ACL</button>
      <button className="side"><Database size={17}/> Brokers</button>
      <div className="side-bottom"><span className="dot"/> Control plane online</div>
    </aside>
    <main>
      <header><div><div className="eyebrow">OPEN-SOURCE MESSAGING PLATFORM</div><h1>Broker Control Center</h1><p>Provision tenant-scoped queues, client credentials and direct Artemis connections.</p></div><div className="status"><span className="dot"/> {status}</div></header>
      {error && <div className="alert">{error}<button onClick={()=>setError("")}><X size={15}/></button></div>}
      <section className="cards">
        <div className="card"><span>Broker nodes</span><strong>1</strong><small>Local MVP · sharding later</small></div>
        <div className="card"><span>Clients</span><strong>{clients.length}</strong><small>Provisioned identities</small></div>
        <div className="card"><span>Queues</span><strong>{queues.length}</strong><small>{selected ? selected.client_id : "Select a client"}</small></div>
        <div className="card"><span>Architecture</span><strong>Pool</strong><small>HA replication later</small></div>
      </section>
      <section className="grid">
        <div className="panel">
          <div className="panel-title"><div><h2>Clients</h2><span>Client identity is independent from broker placement.</span></div><button className="primary" disabled={busy||!clientName.trim()} onClick={createClient}><Plus size={16}/> Create</button></div>
          <div className="inline-form"><input placeholder="client name" value={clientName} onChange={e=>setClientName(e.target.value)} onKeyDown={e=>e.key==='Enter'&&createClient()}/><button disabled={busy||!clientName.trim()} onClick={createClient}>Create client</button><button className="ghost" disabled={busy} onClick={loadClients}><RefreshCw size={15}/> Refresh</button></div>
          <div className="list">{clients.map(c=><div className={`row ${selected?.client_id===c.client_id?'selected':''}`} key={c.client_id} onClick={()=>selectClient(c)}><div><b>{c.name}</b><span>{c.client_id}</span></div><span className="badge">ACTIVE</span></div>)}</div>
          {selected && <div className="secret"><div><b>{selected.name}</b><span>Client ID: {selected.client_id}</span></div>{secret ? <><code>{secret}</code><button className="ghost small" onClick={()=>setShowSecret(!showSecret)}><KeyRound size={14}/> {showSecret?'Hide':'Show'}</button></> : <small>Secret is only available at creation. Select the client again to authenticate.</small>}</div>}
        </div>
        <div className="panel">
          <div className="panel-title"><div><h2>Queues</h2><span>{selected ? `Resources owned by ${selected.client_id}` : "Select a client first"}</span></div></div>
          <div className="inline-form"><input placeholder="queue name, e.g. orders" disabled={!secret||busy} value={queueName} onChange={e=>setQueueName(e.target.value)} onKeyDown={e=>e.key==='Enter'&&createQueue()}/><button disabled={!secret||busy||!queueName.trim()} onClick={createQueue}>Create queue</button></div>
          <div className="list">{queues.map(q=><div className="queue" key={q.name}><div><b>{q.name}</b><span>{q.broker} · {q.broker_host}:{q.stomp_port}</span></div><div className="actions"><button title="Copy connection" onClick={()=>navigator.clipboard?.writeText(`stomp://${q.broker_host}:${q.stomp_port} queue=${q.name} user=${q.username}`)}><Copy size={15}/></button><button title="Send message" onClick={()=>send(q)}><Send size={15}/></button><button title="Receive" onClick={()=>receive(q)}><Download size={15}/></button><button title="Delete" onClick={()=>deleteQueue(q)}><Trash2 size={15}/></button></div></div>)}</div>
          {secret && <div className="connection"><span>{connectionText}</span><small>Public endpoint: localhost:{queues[0]?.stomp_port || 61613}</small></div>}
        </div>
      </section>
      <section className="panel message-panel">
        <div className="panel-title"><div><h2>Message console</h2><span>Use a selected queue's Send/Receive buttons, or type here before pressing Send.</span></div></div>
        <div className="message-compose"><textarea value={message} onChange={e=>setMessage(e.target.value)} placeholder="Test message..."/><div className="message-buttons">{queues.map(q=><button key={q.name} disabled={!secret||busy} onClick={()=>send(q)}><Send size={14}/> Send to {q.name}</button>)}</div></div>
        <div className="received"><div className="received-title">Received messages</div>{received.length===0?<span className="muted">No messages received yet.</span>:received.map((m,i)=><div className="received-row" key={i}><code>{m.message_id||i}</code><span>{m.body}</span></div>)}</div>
      </section>
      <footer>OpenMQ · FastAPI + React + Apache Artemis · tenant-scoped queue MVP · HA/cluster layer planned</footer>
    </main>
  </div>
}
createRoot(document.getElementById("root")).render(<App/>);
