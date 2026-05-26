const API = 'http://127.0.0.1:5000';
let lastEventId = null;
let simInterval = null;
let simRunning = false;
let congestions = {};
let statMaxes = { penalties: 1, duplicates: 1, queue: 1, logs: 1, wrongway: 1 };

// ============================
// CLOCK
// ============================
function updateClock() {
  const now = new Date();
  document.getElementById('headerTime').textContent = now.toLocaleTimeString('en-US', {
    hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
setInterval(updateClock, 1000);
updateClock();

// ============================
// STATS
// ============================
function updateStats(data) {
  const fields = {
    penalties: 'penalties',
    duplicates_blocked: 'duplicates',
    queue_size: 'queue',
    total_logs: 'logs',
    wrongway_alerts: 'wrongway'
  };
  const barIds = {
    penalties: 'penaltiesBar',
    duplicates_blocked: 'dupesBar',
    queue_size: 'queueBar',
    total_logs: 'logsBar',
    wrongway_alerts: 'wrongwayBar'
  };
  const maxKeys = {
    penalties: 'penalties',
    duplicates_blocked: 'duplicates',
    queue_size: 'queue',
    total_logs: 'logs',
    wrongway_alerts: 'wrongway'
  };
  for (const [key, elId] of Object.entries(fields)) {
    if (data[key] !== undefined) {
      const el = document.getElementById(elId);
      if (el) {
        const val = data[key];
        el.textContent = val;
        const mk = maxKeys[key];
        if (val > statMaxes[mk]) statMaxes[mk] = val;
        const bar = document.getElementById(barIds[key]);
        if (bar) bar.style.width = Math.min(100, (val / statMaxes[mk]) * 100) + '%';
      }
    }
  }
}

// ============================
// LOG
// ============================
function addLog(type, msg) {
  const logEl = document.getElementById('log');
  const waiting = logEl.querySelector('.log-waiting');
  if (waiting) waiting.remove();

  const now = new Date().toLocaleTimeString('en-US', {
    hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
  });

  const typeMap = {
    SpeedViolationEvent:  ['SpeedViolation',  'type-speed'],
    VehicleDetectedEvent: ['VehicleDetect',   'type-vehicle'],
    CongestionAlertEvent: ['Congestion',      'type-congestion'],
    WrongWayDriverEvent:  ['WrongWay',        'type-wrongway'],
    DUPLICATE:            ['DUPLICATE',       'type-duplicate'],
    SYSTEM:               ['System',          'type-system'],
    ERROR:                ['Error',           'type-wrongway'],
  };

  const [label, cls] = typeMap[type] || [type, 'type-system'];
  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `
    <span class="log-time">${now}</span>
    <span class="log-type ${cls}">${label.padEnd(14, '\u00A0')}</span>
    <span class="log-msg">${msg}</span>
  `;
  logEl.insertBefore(line, logEl.firstChild);

  const lines = logEl.querySelectorAll('.log-line');
  if (lines.length > 100) lines[lines.length - 1].remove();
}

function clearLog() {
  document.getElementById('log').innerHTML = '<div class="log-waiting">Log cleared.</div>';
}

// ============================
// CAMERA COLOURS  ← FIXED: uses .cam-item and .cam-dot
// ============================
function updateCameraStatus(cameraId, vehicleCount) {
  const items = document.querySelectorAll('.cam-item');
  items.forEach(item => {
    const idEl = item.querySelector('.cam-id');
    if (!idEl || idEl.textContent.trim() !== cameraId) return;

    const dot = item.querySelector('.cam-dot');
    const statusEl = item.querySelector('.cam-status');
    if (!dot || !statusEl) return;

    dot.classList.remove('active', 'high', 'alert', 'critical');

    if (vehicleCount >= 999) {
      dot.classList.add('alert');
      statusEl.textContent = 'Alert';
      statusEl.style.color = '#ff4d6d';
    } else if (vehicleCount >= 80) {
      dot.classList.add('critical');
      statusEl.textContent = 'Critical';
      statusEl.style.color = '#ff4d6d';
    } else if (vehicleCount >= 50) {
      dot.classList.add('high');
      statusEl.textContent = 'High load';
      statusEl.style.color = '#f7c948';
    } else {
      dot.classList.add('active');
      statusEl.textContent = 'Active';
      statusEl.style.color = '';
    }
  });
}

function flashCamera(cameraId) {
  const items = document.querySelectorAll('.cam-item');
  items.forEach(item => {
    const idEl = item.querySelector('.cam-id');
    if (!idEl || idEl.textContent.trim() !== cameraId) return;

    const dot = item.querySelector('.cam-dot');
    const statusEl = item.querySelector('.cam-status');
    if (!dot || !statusEl) return;

    const prevClass = dot.className;
    const prevText = statusEl.textContent;
    const prevColor = statusEl.style.color;

    dot.classList.remove('active', 'high', 'alert', 'critical');
    dot.classList.add('high');
    statusEl.textContent = 'Violation!';
    statusEl.style.color = '#f7c948';

    setTimeout(() => {
      dot.className = prevClass;
      statusEl.textContent = prevText;
      statusEl.style.color = prevColor;
    }, 1000);
  });
}

// ============================
// CONGESTION PANEL
// ============================
function updateCongestionPanel(location, count) {
  if (count > 0) congestions[location] = count;
  renderCongestions();
}

function renderCongestions() {
  const el = document.getElementById('congestionList');
  const countEl = document.getElementById('congestionCount');
  const entries = Object.entries(congestions);
  countEl.textContent = entries.length + ' active';

  if (entries.length === 0) {
    el.innerHTML = '<div class="empty-state">No active congestions</div>';
    return;
  }

  el.innerHTML = '';
  entries.forEach(([loc, cnt]) => {
    const badgeCls = cnt >= 100 ? 'badge-crit' : cnt >= 60 ? 'badge-warn' : 'badge-ok';
    const div = document.createElement('div');
    div.className = 'congestion-item';
    div.innerHTML = `
      <span class="congestion-location">${loc}</span>
      <span class="congestion-badge ${badgeCls}">${cnt} vehicles</span>
    `;
    el.appendChild(div);
  });
}

// ============================
// PUBLISH
// ============================
async function publishEvent(eventType, payload) {
  try {
    const res = await fetch(`${API}/api/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_id: payload.camera_id || 'CAM-01',
        event_type: eventType,
        payload: payload
      })
    });
    const data = await res.json();
    lastEventId = data.event_id;
    updateStats(data);

    let msg = '';
    if (eventType === 'SpeedViolationEvent') {
      msg = `${payload.vehicle_plate} | ${payload.speed} km/h | ${payload.camera_id} | Penalty issued`;
      flashCamera(payload.camera_id);
    } else if (eventType === 'VehicleDetectedEvent') {
      msg = `${payload.vehicle_plate} | ${payload.lane_number} | ${payload.camera_id}`;
    } else if (eventType === 'CongestionAlertEvent') {
      msg = `${payload.intersection} | ${payload.vehicle_count} vehicles detected`;
      updateCongestionPanel(payload.intersection, payload.vehicle_count);
      updateCameraStatus(payload.camera_id, payload.vehicle_count);
    } else if (eventType === 'WrongWayDriverEvent') {
      msg = `${payload.vehicle_plate} | ${payload.direction} | ${payload.camera_id}`;
      updateCameraStatus(payload.camera_id, 999);
    }

    addLog(eventType, msg);
    await getStatus();
  } catch (err) {
    addLog('ERROR', 'Could not reach server. Is Flask running?');
  }
}

async function publishSpeed() {
  await publishEvent('SpeedViolationEvent', {
    camera_id: 'CAM-07',
    vehicle_plate: 'ABC-' + Math.floor(Math.random() * 9000 + 1000),
    speed: Math.floor(Math.random() * 40 + 80),
    speed_limit: 60
  });
}

async function publishVehicle() {
  await publishEvent('VehicleDetectedEvent', {
    camera_id: 'CAM-03',
    vehicle_plate: 'XYZ-' + Math.floor(Math.random() * 9000 + 1000),
    lane_number: 'Lane ' + Math.floor(Math.random() * 3 + 1)
  });
}

async function publishCongestion() {
  const intersections = [
    'Main St & 5th Ave',
    'Stadium Rd & Park Blvd',
    'Ring Rd & Airport Link',
    'GT Road & Mall Junction'
  ];
  const cameras = ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-07', 'CAM-09', 'CAM-11'];
  const cam = cameras[Math.floor(Math.random() * cameras.length)];
  await publishEvent('CongestionAlertEvent', {
    camera_id: cam,
    vehicle_count: Math.floor(Math.random() * 80 + 40),
    intersection: intersections[Math.floor(Math.random() * intersections.length)]
  });
}

async function publishWrongWay() {
  const cameras = ['CAM-01', 'CAM-02', 'CAM-03', 'CAM-07', 'CAM-09', 'CAM-11'];
  const cam = cameras[Math.floor(Math.random() * cameras.length)];
  await publishEvent('WrongWayDriverEvent', {
    camera_id: cam,
    vehicle_plate: 'WRG-' + Math.floor(Math.random() * 9000 + 1000),
    direction: 'Northbound on Southbound lane'
  });
}

async function publishDuplicate() {
  if (!lastEventId) {
    addLog('SYSTEM', 'Publish an event first, then test duplicate!');
    return;
  }
  try {
    const res = await fetch(`${API}/api/publish_duplicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_id: lastEventId })
    });
    const data = await res.json();
    updateStats(data);
    addLog('DUPLICATE', `Blocked ID: ${lastEventId} | Total blocked: ${data.duplicates_blocked}`);
  } catch (err) {
    addLog('ERROR', 'Could not reach server.');
  }
}

// ============================
// STATUS
// ============================
async function getStatus() {
  try {
    const res = await fetch(`${API}/api/status`);
    const data = await res.json();
    updateStats(data);

    const pill = document.getElementById('systemStatus');
    if (pill) {
      pill.style.borderColor = 'rgba(0,229,160,0.3)';
      pill.style.color = '#00e5a0';
      const dot = pill.querySelector('.pulse-dot');
      const label = pill.querySelector('span:last-child');
      if (dot) dot.style.background = '#00e5a0';
      if (label) label.textContent = 'Online';
    }
  } catch (err) {
    const pill = document.getElementById('systemStatus');
    if (pill) {
      pill.style.borderColor = 'rgba(255,77,109,0.3)';
      pill.style.color = '#ff4d6d';
      const dot = pill.querySelector('.pulse-dot');
      const label = pill.querySelector('span:last-child');
      if (dot) dot.style.background = '#ff4d6d';
      if (label) label.textContent = 'Offline';
    }
  }
}

// ============================
// AUTO SIMULATION
// ============================
function randomEvent() {
  const roll = Math.random();
  if (roll < 0.35) publishSpeed();
  else if (roll < 0.60) publishVehicle();
  else if (roll < 0.80) publishCongestion();
  else publishWrongWay();
}

function toggleSim() {
  const btn = document.getElementById('simBtn');
  const icon = document.getElementById('simIcon');
  const label = document.getElementById('simLabel');

  if (simRunning) {
    clearInterval(simInterval);
    simRunning = false;
    btn.classList.remove('running');
    icon.innerHTML = '<polygon points="3,2 11,7 3,12" fill="currentColor"/>';
    label.textContent = 'Start Auto Simulation';
    addLog('SYSTEM', 'Auto simulation stopped.');
  } else {
    simRunning = true;
    btn.classList.add('running');
    icon.innerHTML = '<rect x="2" y="2" width="4" height="10" fill="currentColor"/><rect x="8" y="2" width="4" height="10" fill="currentColor"/>';
    label.textContent = 'Stop Auto Simulation';
    addLog('SYSTEM', 'Auto simulation started — cameras are live!');
    randomEvent();
    simInterval = setInterval(randomEvent, 2000);
  }
}

// ============================
// INIT
// ============================
getStatus();
setInterval(getStatus, 3000);