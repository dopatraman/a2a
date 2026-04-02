// A2A Hub Dashboard

const state = {
  agents: {},       // id -> {agent_id, name, status, connected_at}
  watches: [],      // [{watcher_id, watcher_name, target_id, target_name}]
  events: [],       // envelope objects
  ws: null,
};

const MAX_EVENTS = 200;

// --- WebSocket ---

function connectWS() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${location.host}/ws/dashboard`);

  ws.onopen = () => {
    state.ws = ws;
    setStatus('connected');
    // Send a keepalive ping every 30s so the connection stays open
    ws._pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 30000);
  };

  ws.onmessage = (e) => {
    const envelope = JSON.parse(e.data);
    handleEvent(envelope);
  };

  ws.onclose = () => {
    state.ws = null;
    setStatus('disconnected');
    clearInterval(ws._pingInterval);
    // Reconnect after 2s
    setTimeout(connectWS, 2000);
  };

  ws.onerror = () => ws.close();
}

function setStatus(status) {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  const footer = document.getElementById('ws-status');

  if (status === 'connected') {
    dot.className = 'connected';
    text.textContent = 'live';
    footer.textContent = 'ws: connected';
  } else {
    dot.className = '';
    text.textContent = 'reconnecting...';
    footer.textContent = 'ws: disconnected — reconnecting';
  }
}

// --- Event Handling ---

function handleEvent(envelope) {
  // Add to event stream
  state.events.unshift(envelope);
  if (state.events.length > MAX_EVENTS) state.events.pop();
  renderNewEvent(envelope);

  // Handle status events
  if (envelope.type === 'status') {
    const payload = envelope.payload || {};
    const event = payload.event;

    if (event === 'connected') {
      state.agents[envelope.from_agent] = {
        agent_id: envelope.from_agent,
        name: payload.name || 'unnamed',
        status: 'connected',
      };
      renderAgents();
      renderTopology();
    } else if (event === 'disconnected') {
      delete state.agents[envelope.from_agent];
      state.watches = state.watches.filter(
        w => w.watcher_id !== envelope.from_agent && w.target_id !== envelope.from_agent
      );
      renderAgents();
      renderTopology();
    } else if (event === 'watch') {
      const watcher = state.agents[envelope.from_agent];
      const target = state.agents[payload.target_id];
      state.watches.push({
        watcher_id: envelope.from_agent,
        watcher_name: watcher ? watcher.name : envelope.from_agent,
        target_id: payload.target_id,
        target_name: target ? target.name : payload.target_id,
      });
      renderAgents();
      renderTopology();
    } else if (event === 'unwatch') {
      state.watches = state.watches.filter(
        w => !(w.watcher_id === envelope.from_agent && w.target_id === payload.target_id)
      );
      renderAgents();
      renderTopology();
    }
  }

  // Animate topology edge on emit/stderr
  if (envelope.type === 'emit' || envelope.type === 'stderr') {
    animateEventFlow(envelope.from_agent);
  }

  updateAgentCount();
}

// --- Initial State ---

async function loadInitialState() {
  try {
    const [agentsRes, watchesRes] = await Promise.all([
      fetch('/api/agents'),
      fetch('/api/watches'),
    ]);
    const agents = await agentsRes.json();
    const watches = await watchesRes.json();

    agents.forEach(a => { state.agents[a.agent_id] = a; });
    state.watches = watches;

    renderAgents();
    renderTopology();
    updateAgentCount();
  } catch (e) {
    console.error('Failed to load initial state:', e);
  }
}

// --- Render: Agents ---

function renderAgents() {
  const container = document.getElementById('agents-list');
  const agentList = Object.values(state.agents);

  if (agentList.length === 0) {
    container.innerHTML = '<div class="empty-state">No agents connected</div>';
    return;
  }

  // Track existing cards for animation
  const existingIds = new Set([...container.querySelectorAll('.agent-card')].map(el => el.dataset.id));
  const newIds = new Set(agentList.map(a => a.agent_id));

  // Remove disconnected agents with animation
  container.querySelectorAll('.agent-card').forEach(el => {
    if (!newIds.has(el.dataset.id)) {
      el.classList.add('removing');
      setTimeout(() => el.remove(), 300);
    }
  });

  agentList.forEach(agent => {
    let card = container.querySelector(`[data-id="${agent.agent_id}"]`);
    const watching = state.watches
      .filter(w => w.watcher_id === agent.agent_id)
      .map(w => w.target_name);

    if (card) {
      // Update existing card
      card.querySelector('.agent-watching').textContent =
        watching.length ? `watching: ${watching.join(', ')}` : '';
    } else {
      // Create new card
      card = document.createElement('div');
      card.className = 'agent-card';
      card.dataset.id = agent.agent_id;
      card.innerHTML = `
        <div class="agent-name">
          <span class="agent-dot"></span>
          ${escapeHtml(agent.name)}
        </div>
        <div class="agent-id">${agent.agent_id}</div>
        <div class="agent-watching">${watching.length ? `watching: ${watching.join(', ')}` : ''}</div>
      `;
      container.appendChild(card);
    }
  });
}

// --- Render: Events ---

function renderNewEvent(envelope) {
  const container = document.getElementById('events-list');

  // Remove empty state
  const empty = container.querySelector('.empty-state');
  if (empty) empty.remove();

  const card = document.createElement('div');
  card.className = `event-card type-${envelope.type} flash`;

  const time = new Date(envelope.timestamp).toLocaleTimeString();
  const agentName = state.agents[envelope.from_agent]?.name || envelope.from_agent;
  const payload = formatPayload(envelope);

  card.innerHTML = `
    <div class="event-header">
      <span class="event-from">
        ${escapeHtml(agentName)}
        <span class="event-type ${envelope.type}">${envelope.type}</span>
      </span>
      <span class="event-time">${time}</span>
    </div>
    <div class="event-payload">${escapeHtml(payload)}</div>
  `;

  container.prepend(card);

  // Remove flash class after animation
  setTimeout(() => card.classList.remove('flash'), 800);

  // Limit displayed events
  while (container.children.length > MAX_EVENTS) {
    container.lastChild.remove();
  }
}

function formatPayload(envelope) {
  const p = envelope.payload || {};
  if (envelope.type === 'status') {
    if (p.event === 'connected') return `${p.name} connected`;
    if (p.event === 'disconnected') return 'disconnected';
    if (p.event === 'watch') return `now watching ${p.target_id}`;
    if (p.event === 'unwatch') return `stopped watching ${p.target_id}`;
    return JSON.stringify(p);
  }
  if (p.content) return p.content;
  if (p.stderr) return p.stderr;
  return JSON.stringify(p);
}

// --- Render: Topology ---

function renderTopology() {
  const svg = document.getElementById('topology-svg');
  const rect = svg.getBoundingClientRect();
  const width = rect.width || 280;
  const height = rect.height || 400;

  const agents = Object.values(state.agents);
  if (agents.length === 0) {
    svg.innerHTML = `<text x="${width/2}" y="${height/2}" text-anchor="middle" fill="#8888a0" font-family="Inter" font-size="13">No agents</text>`;
    return;
  }

  // Layout: arrange nodes in a circle
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.32;
  const positions = {};

  const colors = ['#448aff', '#b388ff', '#00e676', '#ffab40', '#ff80ab', '#ff5252'];

  agents.forEach((agent, i) => {
    const angle = (2 * Math.PI * i / agents.length) - Math.PI / 2;
    positions[agent.agent_id] = {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
      color: colors[i % colors.length],
    };
  });

  let svgContent = `<defs>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" class="topo-arrow"/>
    </marker>
  </defs>`;

  // Draw edges
  state.watches.forEach(watch => {
    const from = positions[watch.watcher_id];
    const to = positions[watch.target_id];
    if (!from || !to) return;

    // Shorten line to not overlap with circles
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist === 0) return;
    const nx = dx / dist;
    const ny = dy / dist;
    const startX = from.x + nx * 26;
    const startY = from.y + ny * 26;
    const endX = to.x - nx * 30;
    const endY = to.y - ny * 30;

    const edgeId = `edge-${watch.watcher_id}-${watch.target_id}`;
    svgContent += `<line id="${edgeId}" class="topo-edge drawing"
      x1="${startX}" y1="${startY}" x2="${endX}" y2="${endY}"
      marker-end="url(#arrowhead)"/>`;

    // "watches" label at midpoint
    const mx = (startX + endX) / 2;
    const my = (startY + endY) / 2 - 8;
    svgContent += `<text class="topo-label" x="${mx}" y="${my}">watches</text>`;
  });

  // Draw nodes
  agents.forEach((agent) => {
    const pos = positions[agent.agent_id];
    svgContent += `<g class="topo-node" data-id="${agent.agent_id}">
      <circle cx="${pos.x}" cy="${pos.y}" r="24"
        fill="${pos.color}22" stroke="${pos.color}" stroke-width="2"/>
      <text x="${pos.x}" y="${pos.y + 4}">${escapeHtml(agent.name)}</text>
    </g>`;
  });

  svg.innerHTML = svgContent;
}

function animateEventFlow(fromAgentId) {
  // Find all edges FROM watchers of this agent (events flow from watched → watcher)
  state.watches.forEach(watch => {
    if (watch.target_id === fromAgentId) {
      const edgeId = `edge-${watch.watcher_id}-${watch.target_id}`;
      const edge = document.getElementById(edgeId);
      if (!edge) return;

      // Brief glow on the edge
      edge.style.opacity = '1';
      edge.style.strokeWidth = '3';
      edge.style.filter = 'drop-shadow(0 0 6px var(--accent-purple))';
      setTimeout(() => {
        edge.style.opacity = '';
        edge.style.strokeWidth = '';
        edge.style.filter = '';
      }, 600);
    }
  });
}

// --- Helpers ---

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function updateAgentCount() {
  const count = Object.keys(state.agents).length;
  document.getElementById('agent-count').textContent =
    `${count} agent${count !== 1 ? 's' : ''}`;
}

// --- Init ---

loadInitialState();
connectWS();

// Re-render topology on resize
window.addEventListener('resize', () => renderTopology());

// Initial empty states
document.getElementById('events-list').innerHTML = '<div class="empty-state">Waiting for events...</div>';
