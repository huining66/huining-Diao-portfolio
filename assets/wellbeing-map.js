(async () => {
  const byId = id => document.getElementById(id);
  const map = byId('world-map');
  const country = byId('map-country');
  const metric = byId('map-metric');
  const zoomIn = byId('map-in');
  const zoomOut = byId('map-out');
  const reset = byId('map-reset');
  const detail = byId('map-detail');
  const prompt = detail.textContent;
  const countries = new Map();
  let selected;
  let zoom = 1;
  let cx = 360;
  let cy = 180;
  let drag;
  let suppressClick = false;

  function updateView() {
    const width = 720 / zoom;
    const height = 360 / zoom;
    cx = Math.max(width / 2, Math.min(720 - width / 2, cx));
    cy = Math.max(height / 2, Math.min(360 - height / 2, cy));
    map.setAttribute('viewBox', [cx - width / 2, cy - height / 2, width, height].join(' '));
    map.classList.toggle('can-pan', zoom > 1);
    zoomIn.disabled = zoom === 4;
    zoomOut.disabled = reset.disabled = zoom === 1;
  }

  function select(entry, center = false) {
    selected?.path.removeAttribute('data-selected');
    selected = entry;
    country.value = entry?.data.code ?? '';
    if (!entry) {
      detail.textContent = prompt;
      return;
    }
    entry.path.setAttribute('data-selected', '');
    const { name, hours, score } = entry.data;
    detail.textContent = `${name} · ${hours.toFixed(0)} hours · ${score.toFixed(3)} / 10`;
    if (center && zoom > 1) {
      const { x, y, width, height } = entry.path.getBBox();
      cx = x + width / 2;
      cy = y + height / 2;
      updateView();
    }
  }

  function draw() {
    const hours = metric.value === 'hours';
    byId('map-low').textContent = hours ? '1,200 h' : '0';
    byId('map-high').textContent = hours ? '2,700 h' : '10';
    for (const { path, data } of countries.values()) {
      const fraction = hours ? (data.hours - 1200) / 1500 : data.score / 10;
      const value = Math.max(0, Math.min(1, fraction));
      path.setAttribute('fill', `hsl(210 55% ${85 - value * 55}%)`);
    }
  }

  try {
    const [geo, csv] = await Promise.all(
      ['data/wellbeing/countries.geojson', 'matched-data.csv'].map(async url => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Could not load ${url}`);
        return response;
      })
    );
    const rows = new Map((await csv.text()).trim().split(/\r?\n/).slice(1).map(line => {
      const [name, code, , hours, score] = line.split(',');
      return [code, { name, code, hours: Number(hours), score: Number(score) }];
    }));
    for (const feature of (await geo.json()).features) {
      if (!feature.geometry) continue;
      const { type, coordinates } = feature.geometry;
      const polygons = type === 'Polygon' ? [coordinates] : coordinates;
      const path = document.createElementNS(map.namespaceURI, 'path');
      path.setAttribute('d', polygons.flatMap(polygon => polygon.map(ring =>
        ring.map(([x, y], index) =>
          `${index ? 'L' : 'M'}${(360 + x * 2).toFixed(1)},${(180 - y * 2).toFixed(1)}`
        ).join(' ') + 'Z'
      )).join(' '));
      path.setAttribute('fill-rule', 'evenodd');
      path.setAttribute('fill', '#d1d5db');
      const data = rows.get(feature.properties.code);
      if (data) {
        const entry = { data, path };
        countries.set(data.code, entry);
        path.dataset.country = data.code;
        const title = document.createElementNS(map.namespaceURI, 'title');
        title.textContent = data.name;
        path.append(title);
        path.addEventListener('click', () => {
          if (!suppressClick) select(entry);
        });
      }
      path.setAttribute('aria-hidden', 'true');
      map.append(path);
    }
    for (const { data } of [...countries.values()].sort((a, b) => a.data.name.localeCompare(b.data.name))) {
      country.add(new Option(data.name, data.code));
    }
    country.disabled = false;
    country.addEventListener('change', () => select(countries.get(country.value), true));
    metric.addEventListener('change', draw);
    zoomIn.addEventListener('click', () => {
      zoom = Math.min(4, zoom * 1.5);
      updateView();
    });
    zoomOut.addEventListener('click', () => {
      zoom = Math.max(1, zoom / 1.5);
      updateView();
    });
    reset.addEventListener('click', () => {
      zoom = 1;
      updateView();
    });
    map.addEventListener('keydown', event => {
      const steps = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
      const step = steps[event.key];
      if (zoom === 1 || !step) return;
      event.preventDefault();
      cx += step[0] * 60 / zoom;
      cy += step[1] * 60 / zoom;
      updateView();
    });
    map.addEventListener('pointerdown', event => {
      suppressClick = false;
      if (zoom === 1 || event.button !== 0 || !event.isPrimary) return;
      drag = { id: event.pointerId, x: event.clientX, y: event.clientY, cx, cy };
    });
    map.addEventListener('pointermove', event => {
      if (drag?.id !== event.pointerId) return;
      const dx = event.clientX - drag.x;
      const dy = event.clientY - drag.y;
      if (!suppressClick && Math.hypot(dx, dy) < 5) return;
      if (!suppressClick) map.setPointerCapture(event.pointerId);
      suppressClick = true;
      const scale = 720 / (zoom * map.getBoundingClientRect().width);
      cx = drag.cx - dx * scale;
      cy = drag.cy - dy * scale;
      updateView();
    });
    for (const event of ['pointerup', 'pointercancel', 'pointerleave']) {
      map.addEventListener(event, () => { drag = undefined; });
    }
    draw();
    updateView();
  } catch {
    detail.textContent = 'Map data unavailable. Use the country comparison above.';
  }
})();
