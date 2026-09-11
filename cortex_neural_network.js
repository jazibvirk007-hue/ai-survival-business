/* TJ Cortex Neural Network
 * Real-time visualization of the Cortex communication bus.
 * No synthetic business messages are generated here: packets are spawned only
 * from events returned by /api/communications.
 */
(() => {
  "use strict";

  const NODE_LAYOUT = {
    CEO: [0.50, 0.50],
    Intelligence: [0.50, 0.15],
    Product: [0.72, 0.24],
    "Agent Factory": [0.86, 0.50],
    Growth: [0.72, 0.76],
    Communications: [0.50, 0.85],
    Commerce: [0.28, 0.76],
    Finance: [0.14, 0.50],
    Guard: [0.28, 0.24],
    Memory: [0.50, 0.33]
  };

  const NODE_ALIASES = {
    ceo: "CEO",
    cortex: "CEO",
    "cortex ceo": "CEO",
    intelligence: "Intelligence",
    research: "Intelligence",
    "cortex intelligence": "Intelligence",
    product: "Product",
    "product agent": "Product",
    "agent factory": "Agent Factory",
    agents: "Agent Factory",
    growth: "Growth",
    prospecting: "Growth",
    "cortex growth": "Growth",
    communications: "Communications",
    communication: "Communications",
    commerce: "Commerce",
    orders: "Commerce",
    finance: "Finance",
    guard: "Guard",
    "cortex guard": "Guard",
    memory: "Memory",
    "cortex memory": "Memory"
  };

  const NODE_COLORS = {
    CEO: "#39e7ff",
    Intelligence: "#6ca8ff",
    Product: "#a56cff",
    "Agent Factory": "#ff6cd9",
    Growth: "#52f2a3",
    Communications: "#ffd166",
    Commerce: "#55d6be",
    Finance: "#7ce7ff",
    Guard: "#ff7f7f",
    Memory: "#c18cff"
  };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function normalizeAgent(value) {
    if (typeof value !== "string") return null;
    const key = value.trim().toLowerCase();
    return NODE_ALIASES[key] || (Object.prototype.hasOwnProperty.call(NODE_LAYOUT, value) ? value : null);
  }

  function safeText(value, fallback) {
    if (value === null || value === undefined || value === "") return fallback;
    return String(value).slice(0, 500);
  }

  class CortexNeuralNetwork {
    constructor(root) {
      this.root = root;
      this.canvas = root.querySelector("canvas");
      this.ctx = this.canvas.getContext("2d");
      this.inspector = root.querySelector("[data-neural-inspector]");
      this.eventCount = root.querySelector("[data-neural-count]");
      this.status = root.querySelector("[data-neural-status]");
      this.lastEvent = root.querySelector("[data-neural-last]");
      this.nodes = Object.keys(NODE_LAYOUT).map((name) => ({
        name,
        x: NODE_LAYOUT[name][0],
        y: NODE_LAYOUT[name][1],
        glow: 0,
        hover: false
      }));
      this.edges = [];
      this.packets = [];
      this.events = [];
      this.seen = new Set();
      this.particles = Array.from({ length: 36 }, (_, index) => ({
        x: (index * 0.137) % 1,
        y: (index * 0.271) % 1,
        speed: 0.00004 + (index % 7) * 0.000012,
        phase: index * 1.71
      }));
      this.running = true;
      this.reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(this.root);
      this.canvas.addEventListener("click", (event) => this.inspectAt(event));
      this.canvas.addEventListener("mousemove", (event) => this.hoverAt(event));
      this.resize();
      this.fetchLoop();
      requestAnimationFrame((time) => this.frame(time));
    }

    resize() {
      const rect = this.canvas.getBoundingClientRect();
      const ratio = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
      this.canvas.width = Math.max(1, Math.floor(rect.width * ratio));
      this.canvas.height = Math.max(1, Math.floor(rect.height * ratio));
      this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      this.width = rect.width;
      this.height = rect.height;
    }

    point(node) {
      return { x: node.x * this.width, y: node.y * this.height };
    }

    buildEdges() {
      const names = Object.keys(NODE_LAYOUT);
      const desired = new Set();
      for (const event of this.events) {
        const sender = normalizeAgent(event.sender);
        const recipient = normalizeAgent(event.recipient);
        if (!sender || !recipient || sender === recipient) continue;
        const key = [sender, recipient].sort().join("|");
        desired.add(key);
      }
      for (const left of names) {
        for (const right of names) {
          if (left >= right) continue;
          const key = [left, right].sort().join("|");
          if (desired.has(key)) continue;
        }
      }
      this.edges = Array.from(desired).map((key) => {
        const [a, b] = key.split("|");
        return { a, b, strength: 0.18, pulse: 0 };
      });
    }

    spawnPacket(event) {
      const sender = normalizeAgent(event.sender);
      const recipient = normalizeAgent(event.recipient);
      if (!sender || !recipient || sender === recipient) return;
      this.packets.push({
        sender,
        recipient,
        start: performance.now(),
        duration: this.reducedMotion ? 1 : 900 + Math.random() * 650,
        status: safeText(event.status, "sent")
      });
      const senderNode = this.nodes.find((node) => node.name === sender);
      const recipientNode = this.nodes.find((node) => node.name === recipient);
      if (senderNode) senderNode.glow = 1;
      if (recipientNode) recipientNode.glow = 1;
    }

    ingest(events, streamReady) {
      if (!Array.isArray(events)) return;
      const ordered = [...events].reverse();
      for (const event of ordered) {
        const id = safeText(event.event_id || event.id || event.correlation_id || `${event.timestamp}|${event.sender}|${event.recipient}|${event.summary}`, "event");
        if (this.seen.has(id)) continue;
        this.seen.add(id);
        this.events.push(event);
        if (this.events.length > 120) this.events.shift();
        this.spawnPacket(event);
      }
      this.buildEdges();
      this.eventCount.textContent = `${this.events.length} observed events`;
      this.status.textContent = streamReady ? "LIVE BUS" : "BUS IDLE";
      if (this.events.length) {
        const event = this.events[this.events.length - 1];
        this.lastEvent.textContent = `${safeText(event.sender, "?")} → ${safeText(event.recipient, "?")}`;
      }
    }

    async fetchLoop() {
      try {
        const response = await fetch("/api/communications?limit=50", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        this.ingest(payload.events, Boolean(payload.stream && payload.stream.live_stream_ready));
      } catch (error) {
        this.status.textContent = "BUS UNAVAILABLE";
      } finally {
        window.setTimeout(() => this.fetchLoop(), 1500);
      }
    }

    drawBackground(time) {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.width, this.height);
      const gradient = ctx.createRadialGradient(this.width * 0.5, this.height * 0.5, 10, this.width * 0.5, this.height * 0.5, Math.max(this.width, this.height) * 0.7);
      gradient.addColorStop(0, "rgba(22,38,74,0.42)");
      gradient.addColorStop(0.55, "rgba(7,13,29,0.62)");
      gradient.addColorStop(1, "rgba(3,6,15,0.96)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, this.width, this.height);
      for (const particle of this.particles) {
        if (!this.reducedMotion) particle.y = (particle.y + particle.speed) % 1;
        const x = particle.x * this.width;
        const y = particle.y * this.height;
        const alpha = 0.18 + 0.12 * Math.sin(time * 0.001 + particle.phase);
        ctx.fillStyle = `rgba(93,177,255,${clamp(alpha, 0.04, 0.35)})`;
        ctx.fillRect(x, y, 1.2, 1.2);
      }
    }

    drawEdges(time) {
      const ctx = this.ctx;
      for (const edge of this.edges) {
        const a = this.nodes.find((node) => node.name === edge.a);
        const b = this.nodes.find((node) => node.name === edge.b);
        if (!a || !b) continue;
        const p1 = this.point(a);
        const p2 = this.point(b);
        const pulse = edge.pulse;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = `rgba(72,141,210,${0.16 + pulse * 0.45})`;
        ctx.lineWidth = 1 + pulse * 1.4;
        ctx.stroke();
        if (!this.reducedMotion) {
          const t = (time * 0.00008) % 1;
          const x = p1.x + (p2.x - p1.x) * t;
          const y = p1.y + (p2.y - p1.y) * t;
          ctx.fillStyle = "rgba(57,231,255,0.32)";
          ctx.beginPath();
          ctx.arc(x, y, 1.4, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    drawPackets(time) {
      const ctx = this.ctx;
      const keep = [];
      for (const packet of this.packets) {
        const sender = this.nodes.find((node) => node.name === packet.sender);
        const recipient = this.nodes.find((node) => node.name === packet.recipient);
        if (!sender || !recipient) continue;
        const progress = clamp((time - packet.start) / packet.duration, 0, 1);
        const p1 = this.point(sender);
        const p2 = this.point(recipient);
        const eased = progress * progress * (3 - 2 * progress);
        const x = p1.x + (p2.x - p1.x) * eased;
        const y = p1.y + (p2.y - p1.y) * eased;
        const color = packet.status === "failed" || packet.status === "denied" ? "#ff7f7f" : "#39e7ff";
        ctx.shadowBlur = 18;
        ctx.shadowColor = color;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 4.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
        if (progress < 1) keep.push(packet);
      }
      this.packets = keep;
    }

    drawNodes() {
      const ctx = this.ctx;
      for (const node of this.nodes) {
        const point = this.point(node);
        const color = NODE_COLORS[node.name] || "#39e7ff";
        const radius = node.name === "CEO" ? 32 : 23;
        const glow = clamp(node.glow, 0, 1);
        node.glow *= 0.94;
        if (glow > 0.01 || node.hover) {
          ctx.shadowBlur = 28 + glow * 30;
          ctx.shadowColor = color;
        }
        ctx.fillStyle = "rgba(6,12,25,0.96)";
        ctx.strokeStyle = color;
        ctx.lineWidth = node.name === "CEO" ? 2.2 : 1.3;
        ctx.beginPath();
        ctx.arc(point.x, point.y, radius + glow * 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.fillStyle = color;
        ctx.font = node.name === "CEO" ? "700 12px system-ui" : "600 10px system-ui";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(node.name.toUpperCase(), point.x, point.y);
      }
    }

    hitTest(x, y) {
      for (const node of this.nodes) {
        const point = this.point(node);
        const radius = node.name === "CEO" ? 40 : 31;
        if (Math.hypot(x - point.x, y - point.y) <= radius) return node;
      }
      return null;
    }

    hoverAt(event) {
      const rect = this.canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      for (const node of this.nodes) node.hover = false;
      const node = this.hitTest(x, y);
      if (node) {
        node.hover = true;
        this.canvas.style.cursor = "pointer";
      } else {
        this.canvas.style.cursor = "default";
      }
    }

    inspectAt(event) {
      const rect = this.canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const node = this.hitTest(x, y);
      if (node) {
        const related = this.events.filter((item) => normalizeAgent(item.sender) === node.name || normalizeAgent(item.recipient) === node.name).slice(-5).reverse();
        this.inspector.innerHTML = `<strong>${node.name}</strong><div class="muted">${related.length} recent related events</div>${related.map((item) => `<div class="neural-detail"><span>${safeText(item.sender, "?")} → ${safeText(item.recipient, "?")}</span><small>${safeText(item.summary, "event")}</small></div>`).join("") || `<div class="muted">No communication event observed yet.</div>`;
        return;
      }
      this.inspector.innerHTML = `<span class="muted">Select an agent node to inspect its latest observed communications.</span>`;
    }

    frame(time) {
      if (!this.running) return;
      this.drawBackground(time);
      this.drawEdges(time);
      this.drawPackets(time);
      this.drawNodes();
      requestAnimationFrame((next) => this.frame(next));
    }
  }

  function init() {
    const root = document.querySelector("[data-neural-network]");
    if (!root || !window.ResizeObserver) return;
    window.cortexNeuralNetwork = new CortexNeuralNetwork(root);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
