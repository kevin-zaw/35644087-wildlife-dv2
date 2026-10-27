// Who's calling? FIT3179 DV2 — embeds the Vega-Lite / Vega specifications in /specs.

const SANS = '"Source Sans 3", "Segoe UI", Arial, sans-serif';
const theme = {
  font: SANS,
  background: null,
  view: {stroke: null},
  padding: 4,
  axis: {
    labelFont: SANS, titleFont: SANS,
    labelFontSize: 12, titleFontSize: 12.5, titleFontWeight: 600,
    labelColor: "#4a5a54", titleColor: "#33443e",
    domainColor: "#b8c2bd", tickColor: "#b8c2bd", gridColor: "#e3e8e4"
  },
  legend: {
    labelFont: SANS, titleFont: SANS,
    labelFontSize: 12, titleFontSize: 12.5, titleFontWeight: 600,
    labelColor: "#33443e", titleColor: "#1b2b26"
  },
  header: {labelFont: SANS, titleFont: SANS},
  title: {font: SANS, fontSize: 15, fontWeight: 700, anchor: "start", color: "#1b2b26",
          subtitleFont: SANS, subtitleFontSize: 12.5, subtitleColor: "#5b6b65", offset: 10},
  text: {font: SANS}
};

const charts = [
  ["#c01", "specs/01_treemap_national_records.json"],
  ["#c02", "specs/02_line_records_over_time.json"],
  ["#c03", "specs/03_area_public_sightings.json"],
  ["#c04", "specs/04_butterfly_species_vs_records.json"],
  ["#c05", "specs/05_waffle_record_sources.json"],
  ["#c06", "specs/06_heatmap_sources_by_group.json"],
  ["#c07", "specs/07_waffle_frogid_contributors.json"],
  ["#c08", "specs/08_calendar_frogid_daily.json"],
  ["#c09", "specs/09_heatmap_frogid_season_hour.json"],
  ["#c10", "specs/10_bin_map_wildlife_density.json"],
  ["#c11", "specs/11_choropleth_wildlife_per_capita.json"],
  ["#c12", "specs/12_symbol_map_frog_richness.json"],
  ["#c13", "specs/13_ridgeline_wildlife_months.json"],
  ["#c14", "specs/14_heatmap_wildlife_latitude_month.json"],
  ["#c15", "specs/15_bin_map_wildlife_seasons.json"],
  ["#c16", "specs/16_dotplot_frog_rarity.json"],
  ["#c17", "specs/17_dot_map_cane_toad.json"]
];

const views = {};
const opts = {
  renderer: "svg",
  actions: false,   // hides the "..." menu so charts align cleanly
  tooltip: {theme: "light"}
};

// Merge the shared theme into each spec's own config (the spec's settings win).
function merge(base, over) {
  const out = Array.isArray(base) ? base.slice() : {...base};
  for (const k in over) {
    out[k] = over[k] && typeof over[k] === "object" && !Array.isArray(over[k]) && base[k] && typeof base[k] === "object"
      ? merge(base[k], over[k]) : over[k];
  }
  return out;
}

Promise.all(charts.map(([el, url]) =>
  fetch(url).then(r => r.json())
    .then(spec => { spec.config = merge(theme, spec.config || {}); return vegaEmbed(el, spec, opts); })
    .then(result => { views[el] = result.view; })
    .catch(err => {
      document.querySelector(el).textContent = "This chart could not load: " + err.message;
      console.error(url, err);
    })
)).then(linkViews);

function linkViews() {
  const heat = views["#c14"];
  const map = views["#c15"];
  if (!heat || !map) return;

  // Clicking a month in the latitude heatmap shows that month on the seasonal map (linked views).
  heat.addDataListener("monthPick_store", (name, store) => {
    if (store && store.length) map.signal("mon", store[0].values[0]).runAsync();
  });

  // "Play the year": steps the month slider from January to December.
  const btn = document.getElementById("playBtn");
  let timer = null;
  const stop = () => {
    clearInterval(timer); timer = null;
    btn.textContent = "Play the year"; btn.setAttribute("aria-pressed", "false");
  };
  btn.addEventListener("click", () => {
    if (timer) { stop(); return; }
    let m = map.signal("mon");
    if (m >= 12) m = 0;
    btn.textContent = "Pause"; btn.setAttribute("aria-pressed", "true");
    timer = setInterval(() => {
      m += 1;
      map.signal("mon", m).runAsync();
      if (m >= 12) stop();
    }, 1100);
  });
}
