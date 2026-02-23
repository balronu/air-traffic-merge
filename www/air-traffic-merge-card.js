// Air Traffic Merge Card (FR24 + ADS-B)
// Drop this into /config/www/air-traffic-merge-card.js and add as Lovelace resource.
// type: custom:air-traffic-merge-card
//
// Config:
// - entity (required): sensor.air_traffic_merged
// - status_entity (optional): sensor.air_traffic_status
// - title (optional)
// - highlight_callsign (optional, default "CHX16")
// - max_items (optional, default 30)
// - show_debug (optional, default false)
// - tracked_icons (optional): base map (backwards compatible)
// - tracked_icons_callsign (optional): map for callsign-tracking
// - tracked_icons_registration (optional): map for registration-tracking
// - prioritize_tracked (optional, default true)

const CARD_TAG = "air-traffic-merge-card";

const tpl = (strings, ...values) =>
  strings.reduce((acc, s, i) => acc + s + (values[i] ?? ""), "");

function fmtNum(v, digits = 0) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

function tsToLocal(ts) {
  const n = Number(ts);
  if (!Number.isFinite(n) || n <= 0) return "—";
  try {
    return new Date(n * 1000).toLocaleString();
  } catch (e) {
    return "—";
  }
}

function getState(hass, entityId) {
  return entityId ? hass.states[entityId] : undefined;
}

function getAttr(entity, attr, fallback) {
  if (!entity || !entity.attributes) return fallback;
  const v = entity.attributes[attr];
  return v === undefined || v === null ? fallback : v;
}

function ensureArray(v) {
  return Array.isArray(v) ? v : [];
}

function sourceBadge(source) {
  if (source === "BOTH") return "✅ FR24+ADS-B";
  if (source === "FR24") return "⚠️ nur FR24";
  if (source === "ADSB") return "⚠️ nur ADS-B";
  return source ?? "—";
}

function arrowFromDeg(deg) {
  const d = Number(deg);
  if (!Number.isFinite(d)) return "";
  // 8-way arrow
  const dirs = ["⬆️","↗️","➡️","↘️","⬇️","↙️","⬅️","↖️"];
  const idx = Math.round(((d % 360) / 45)) % 8;
  return dirs[idx];
}

const css = `
  :host { display:block; }
  ha-card { overflow:hidden; }
  .wrap { padding: 12px 16px 16px; }
  .header { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
  .title { font-weight: 600; font-size: 1.05rem; line-height: 1.2; }
  .sub { opacity: .8; font-size: .9rem; margin-top: 2px; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top: 10px; }
  .chip { padding: 4px 10px; border-radius: 999px; background: var(--secondary-background-color); font-size: .85rem; }
  .list { margin-top: 12px; display:flex; flex-direction:column; gap:10px; }
  .item { padding: 10px 12px; border-radius: 12px; border: 1px solid var(--divider-color); }
  .itemHead { display:flex; align-items:center; justify-content:space-between; gap:10px; }
  .itemTitle { font-weight: 700; }
  .muted { opacity:.75; }
  .meta { margin-top: 4px; font-size: .92rem; }
  .kv { display:flex; flex-wrap:wrap; gap:10px; margin-top: 6px; font-size: .92rem; }
  .kv span { white-space: nowrap; }
  .code { font-family: var(--code-font-family, monospace); opacity:.85; }
  details { margin-top: 10px; }
  summary { cursor:pointer; }
`;

class AirTrafficMergeCard extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("You need to define an entity (sensor.air_traffic_merged)");
    }
    this._config = {
      title: config.title ?? "Flugzeuge",
      entity: config.entity,
      status_entity: config.status_entity,
      highlight_callsign: config.highlight_callsign ?? "CHX16",
      max_items: config.max_items ?? 30,
      show_debug: config.show_debug ?? false,
      tracked_icons: config.tracked_icons ?? { CHX16: '🚑🚁' },
      tracked_icons_callsign: config.tracked_icons_callsign ?? null,
      tracked_icons_registration: config.tracked_icons_registration ?? null,
      prioritize_tracked: config.prioritize_tracked ?? true,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 6;
  }

  _render() {
    if (!this._hass || !this._config) return;

    const mergedEnt = getState(this._hass, this._config.entity);
    const statusEnt = getState(this._hass, this._config.status_entity);

    const flights = ensureArray(getAttr(mergedEnt, "flights", []));
    const lastUpdate = getAttr(statusEnt, "last_update", getAttr(mergedEnt, "last_update", 0));
    const fr24Count = getAttr(statusEnt, "fr24_count", "—");
    const adsbCount = getAttr(statusEnt, "adsb_count", "—");
    const mergedCount = getAttr(statusEnt, "merged_count", flights.length);
    const trackingEnabled = getAttr(statusEnt, "tracking_enabled", false);
    const trackedActiveCount = getAttr(statusEnt, "tracked_active_count", 0);
    const trackedActive = ensureArray(getAttr(statusEnt, "tracked_active", []));

    const status = statusEnt ? statusEnt.state : "";

    const statusText =
      status === "none" ? "⚠️ Keine Daten" :
      status === "adsb_only" ? "⚠️ Nur ADS-B" :
      status === "fr24_only" ? "⚠️ Nur FR24" :
      status === "both" ? "✅ Beide Quellen" : "";

    const maxItems = Number(this._config.max_items) || 30;
    let items = flights.slice(0, maxItems);
    if (this._config.prioritize_tracked) {
      items = items.sort((a,b) => (b.tracked === true) - (a.tracked === true));
    }

    const listHtml = items.length === 0
      ? `<div class="muted">Keine Flüge vorhanden.</div>`
      : items.map(f => {
          const reg = (f.registration || "").trim();
          const hx = (f.hex || "").trim();
          const callsign = (f.callsign || "").trim();
          const title = reg ? reg : (hx ? `HEX: ${hx}` : "—");

          const isHighlight = callsign === this._config.highlight_callsign;
          const isTracked = !!f.tracked;
          const trackedTarget = (f.tracked_target || '').trim().toUpperCase();
          const iconMapBase = this._config.tracked_icons || {};
          const iconMapCS = this._config.tracked_icons_callsign || iconMapBase;
          const iconMapREG = this._config.tracked_icons_registration || iconMapBase;
          const trackedBy = (f.tracked_by || '').toString().toLowerCase();
          const iconMap = trackedBy === 'registration' ? iconMapREG : iconMapCS;

          const icon = (isHighlight || isTracked)
            ? (iconMap[trackedTarget] || iconMap[callsign] || iconMap[this._config.highlight_callsign] || '🎯')
            : '✈️';

          const airline = (f.airline || "").trim();
          const model = (f.aircraft_model || "").trim();
          const modelLine = (airline || model) ? `<div class="muted">${airline} ${model}</div>` : "";

          const src = sourceBadge(f.source);
          const alt = f.alt_m !== null && f.alt_m !== undefined ? `${fmtNum(f.alt_m,0)} m` : "—";
          const spd = f.spd_kmh !== null && f.spd_kmh !== undefined ? `${fmtNum(f.spd_kmh,0)} km/h` : "—";
          const dist = f.dist_km !== null && f.dist_km !== undefined ? `${fmtNum(f.dist_km,1)} km` : "—";
          const dir = f.dir_deg !== null && f.dir_deg !== undefined ? `${fmtNum(f.dir_deg,0)}° ${arrowFromDeg(f.dir_deg)}` : "—";

          const csLine = callsign ? callsign : (reg ? reg : (hx ? `HEX ${hx}` : "—"));

          return `
            <div class="item">
              <div class="itemHead">
                <div>
                  <div class="itemTitle">${icon} ${isTracked ? '🎯 ' : ''}${isHighlight ? `<b>${this._config.highlight_callsign}</b> — ` : ""}${title}</div>
                  ${modelLine}
                </div>
                <div class="chip">${src}</div>
              </div>
              <div class="meta"><b>Kennung:</b> ${csLine}</div>
              <div class="kv">
                <span>🗼 ${alt}</span>
                <span>🚀 ${spd}</span>
                <span>📏 ${dist}</span>
                <span>🧭 ${dir}</span>
              </div>
              ${(model || hx) ? `<div class="meta code">${model ? `${model}` : ""}${model && hx ? " · " : ""}${hx ? hx : ""}</div>` : ""}
            </div>
          `;
        }).join("");

    const debugHtml = (this._config.show_debug)
      ? `
        <details>
          <summary><b>🛠️ Debug</b></summary>
          <div class="meta">
            <div><b>Merged entity:</b> <span class="code">${this._config.entity}</span></div>
            ${this._config.status_entity ? `<div><b>Status entity:</b> <span class="code">${this._config.status_entity}</span></div>` : ""}
            <div><b>Last update:</b> ${tsToLocal(lastUpdate)}</div>
            <div><b>Counts:</b> FR24 ${fr24Count} · ADS-B ${adsbCount} · Merged ${mergedCount}</div>
          </div>
        </details>
      `
      : "";

    const root = this;
    if (!root.shadowRoot) root.attachShadow({ mode: "open" });

    root.shadowRoot.innerHTML = `
      <style>${css}</style>
      <ha-card>
        <div class="wrap">
          <div class="header">
            <div>
              <div class="title">${this._config.title}</div>
              <div class="sub">📡 Letztes Update: <b>${tsToLocal(lastUpdate)}</b></div>
            </div>
          </div>
          <div class="chips">
            <div class="chip">FR24: <b>${fr24Count}</b></div>
            <div class="chip">ADS-B: <b>${adsbCount}</b></div>
            <div class="chip">Zusammengeführt: <b>${mergedCount}</b></div>
            ${statusText ? `<div class="chip">${statusText}</div>` : ""}
            ${(trackingEnabled || trackedActiveCount > 0) ? `<div class="chip">🎯 Tracked: <b>${trackedActiveCount}</b>${trackedActiveCount > 0 ? ` (${trackedActive.join(", ")})` : ""}</div>` : ""}
          </div>
          <div class="list">${listHtml}</div>
          ${debugHtml}
        </div>
      </ha-card>
    `;
  }
}

customElements.define(CARD_TAG, AirTrafficMergeCard);

// Lovelace card picker text
window.customCards = window.customCards || [];
window.customCards.push({
  type: CARD_TAG,
  name: "Air Traffic Merge Card",
  description: "Merged FR24 + ADS-B flight list (with CHX highlight)."
});
