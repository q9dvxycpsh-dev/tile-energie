/* Calculateur de dimensionnement solaire — TILE ÉNERGIE */
(function () {
  'use strict';
  const $ = (s) => document.querySelector(s);

  const PRESETS = [
    { name: 'Ampoule LED', w: 10, h: 5 },
    { name: 'Ventilateur', w: 60, h: 8 },
    { name: 'Téléviseur', w: 90, h: 5 },
    { name: 'Réfrigérateur', w: 150, h: 10 },
    { name: 'Congélateur', w: 200, h: 10 },
    { name: 'Box internet', w: 15, h: 24 },
    { name: 'Ordinateur', w: 120, h: 6 },
    { name: 'Pompe à eau', w: 750, h: 2 },
    { name: 'Climatiseur', w: 1200, h: 6 },
    { name: 'Machine à laver', w: 500, h: 1 },
    { name: 'Chargeur téléphone', w: 10, h: 3 },
  ];

  // Configuration initiale réaliste pour un foyer
  let rows = [
    { name: 'Ampoule LED', w: 10, qty: 6, h: 5 },
    { name: 'Ventilateur', w: 60, qty: 2, h: 8 },
    { name: 'Téléviseur', w: 90, qty: 1, h: 5 },
    { name: 'Réfrigérateur', w: 150, qty: 1, h: 10 },
    { name: 'Box internet', w: 15, qty: 1, h: 24 },
  ];

  const presetSel = $('#preset');
  const body = $('#appliance-body');
  const LOSS = 1.3, PF = 0.8;
  const fmt = (n) => Math.round(n).toLocaleString('fr-FR');

  function fillPresets() {
    PRESETS.forEach((p, i) => {
      const o = document.createElement('option');
      o.value = i; o.textContent = p.name + ' (' + p.w + ' W)';
      presetSel.appendChild(o);
    });
  }

  function render() {
    body.innerHTML = '';
    rows.forEach((r, i) => {
      const wh = r.w * r.qty * r.h;
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td class="ref" style="color:var(--ink);font-family:var(--font-body);font-weight:600">' + r.name + '</td>' +
        '<td><input type="number" min="1" value="' + r.w + '" data-k="w" data-i="' + i + '" style="padding:7px 9px"></td>' +
        '<td><input type="number" min="0" value="' + r.qty + '" data-k="qty" data-i="' + i + '" style="padding:7px 9px"></td>' +
        '<td><input type="number" min="0" max="24" step="0.5" value="' + r.h + '" data-k="h" data-i="' + i + '" style="padding:7px 9px"></td>' +
        '<td><strong>' + fmt(wh) + '</strong></td>' +
        '<td><button class="icon-badge icon-badge--sm" type="button" data-del="' + i + '" aria-label="Supprimer" style="background:var(--danger-bg);color:var(--danger);width:36px;height:36px;border-radius:9px"><svg class="icon" aria-hidden="true"><use href="#i-x"></use></svg></button></td>';
      body.appendChild(tr);
    });
    compute();
  }

  function compute() {
    const dailyWh = rows.reduce((s, r) => s + r.w * r.qty * r.h, 0);
    const peakLoad = rows.reduce((s, r) => s + r.w * r.qty, 0);
    const psh = parseFloat($('#psh').value);
    const voltage = parseFloat($('#voltage').value);
    const dod = parseFloat($('#battype').value);
    const autonomy = parseFloat($('#autonomy').value);
    const panelWp = Math.max(50, parseFloat($('#panelwp').value) || 450);

    const requiredWp = dailyWh * LOSS / psh;
    const panels = Math.max(0, Math.ceil(requiredWp / panelWp));
    const actualWp = panels * panelWp;

    const batteryWh = dailyWh * autonomy / dod;
    const batteryAh = batteryWh / voltage;

    const inverterW = peakLoad * 1.25;
    const inverterKVA = inverterW / PF / 1000;

    // Budget indicatif (FCFA)
    const pvCost = actualWp * 650;
    const battCost = batteryWh * 230;
    const invCost = inverterW * 120;
    const total = (pvCost + battCost + invCost) * 1.2;
    const low = total * 0.9, high = total * 1.15;

    $('#r-daily').textContent = (dailyWh / 1000).toFixed(1).replace('.', ',') + ' kWh';
    $('#r-pv').textContent = (actualWp / 1000).toFixed(2).replace('.', ',') + ' kWc';
    $('#r-panels').textContent = panels + ' panneau' + (panels > 1 ? 'x' : '') + ' de ' + panelWp + ' Wc';
    $('#r-batt').textContent = fmt(batteryAh) + ' Ah';
    $('#r-batt-sub').textContent = (batteryWh / 1000).toFixed(1).replace('.', ',') + ' kWh sous ' + voltage + ' V';
    $('#r-inv').textContent = inverterKVA.toFixed(1).replace('.', ',') + ' kVA';
    $('#r-inv-sub').textContent = 'Pointe estimée ' + fmt(peakLoad) + ' W';
    $('#r-budget').textContent = fmt(low) + ' à ' + fmt(high) + ' FCFA';
  }

  // Events
  document.addEventListener('input', (e) => {
    const i = e.target.dataset.i, k = e.target.dataset.k;
    if (i !== undefined && k) {
      rows[i][k] = parseFloat(e.target.value) || 0;
      const wh = rows[i].w * rows[i].qty * rows[i].h;
      const cell = e.target.closest('tr').children[4];
      if (cell) cell.innerHTML = '<strong>' + fmt(wh) + '</strong>';
      compute();
    }
    if (['psh', 'voltage', 'battype', 'autonomy', 'panelwp'].includes(e.target.id)) compute();
  });
  document.addEventListener('change', (e) => {
    if (['psh', 'voltage', 'battype', 'autonomy'].includes(e.target.id)) compute();
  });
  document.addEventListener('click', (e) => {
    const del = e.target.closest('[data-del]');
    if (del) { rows.splice(parseInt(del.dataset.del, 10), 1); render(); }
  });

  document.addEventListener('DOMContentLoaded', () => {
    if (!presetSel || !body) return;
    fillPresets();
    $('#add-appliance').addEventListener('click', () => {
      const p = PRESETS[parseInt(presetSel.value || 0, 10)];
      rows.push({ name: p.name, w: p.w, qty: 1, h: p.h });
      render();
    });
    render();
  });
})();
