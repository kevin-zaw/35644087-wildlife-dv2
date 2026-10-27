# DV2 interview preparation (3%)

Answer in your own words. Open the live page and point at the chart while you speak.

## About the whole page

**What is your visualisation about, in one sentence?**
Who records Australia's wildlife and what the records leave out. Sightings (human observations) grew 24-fold, but the records favour birds, cities, spring and count weeks. A FrogID spotlight shows how individual volunteers record.

**Who is it for?**
The average Australian adult with no statistics background. That is why every chart has a "How to read" note and the text uses plain words.

**What are your sources?**
- Atlas of Living Australia record counts, which I downloaded on 27 October 2026 with my own Python script (133 queries, all logged in manifest.json).
- GBIF report and analytics (2026).
- Chapman (2009).
- FrogID 2023.
- ABS population, June 2023.

**How many idioms?**
18 charts and 10 distinct advanced idioms, plus 3 basic ones (line, stacked area, dot plot). The 5 maps use 4 map idioms. Repeated idioms are counted once.


## Code walkthrough (the tutor says she will ask "which part of the code makes this work?")

Open the repository in VS Code and point at these exact places.

| Question | Where to point |
|---|---|
| How are the charts embedded in the page? | `index.html` has one empty `<div id="c01">` … `<div id="c17">` per chart, the ID selectors. The Vega, Vega-Lite and Vega-Embed libraries load in the `<head>` (`<script src=".../vega@5.30.0">` etc.). `js/main.js` has the `charts` list, which pairs each ID with its spec file in `specs/`, and calls `vegaEmbed(el, spec, opts)` for each one. |
| How does the dropdown work? | `specs/10_bin_map_wildlife_density.json` → `"params": [{"name": "grp", "bind": {"input": "select", "options": [...]}}]`. The transform `datum.properties[grp]` then picks the chosen group's density. |
| How does the month slider work? | `specs/15_bin_map_wildlife_seasons.json` → param `mon` with `"bind": {"input": "range", "min": 1, "max": 12}`. The map builds a key `cell + '|' + mon` and looks up that month's value. |
| How does the Play button animate it? | `index.html` → `<button id="playBtn">`. `js/main.js` → `linkViews()` uses `setInterval` to call `map.signal("mon", m).runAsync()` every 1.1 s. |
| How does clicking the heatmap change the map? | `specs/14_heatmap_wildlife_latitude_month.json` → param `monthPick`, a point selection on field `m` triggered `on: click`. `js/main.js` → `heat.addDataListener("monthPick_store", …)` sets the map's `mon` signal. |
| Linked hover highlighting? | The choropleth layer in `specs/11_…json` has param `st`; the lollipop uses it in an `opacity` condition. The butterfly (`specs/04_…json`) has one hover param per panel, combined in a `test` expression. |
| Legend filtering? | `specs/03_area_public_sightings.json` → param `layerPick` with `"bind": "legend"`. |
| Tooltips? | `"tooltip": [ {...}, {...} ]` inside each chart's `encoding`. |
| Annotations? | Text-mark layers with their own `"data": {"values": [...]}`. City names use a white-stroke copy underneath for legibility (a halo). The bin map and seasonal map use dynamic titles (`"title": {"text": {"expr": ...}}`). |
| Why is there no "…" button on the charts? | `js/main.js` → embed option `actions: false`. |
| Facet, repeat or concat? | The ridgeline (`specs/13_…json`) uses `facet` (`row`), with its built-in row labels switched off (`"header": {"labels": false}`) and group names drawn as a text layer. Side-by-side views (butterfly, waffles, heatmap + bar, choropleth + lollipop) use `hconcat`. I don't use `repeat`. |
| How was the treemap made? | It's Vega, not Vega-Lite (`specs/01_…json`): a `nest` transform builds the kingdom → group hierarchy, then the `treemap` transform lays it out. |
| Where does the data come from? | `scripts/download_wildlife_data.py` (my ALA download, with every query logged in `data/ala/raw_download/manifest.json`); `scripts/prepare_ala_data.py` turns it into the chart files. |

## Typography (if asked)

- **Display headings:** Young Serif.
- **Body text:** Literata, at 20 px. Lines are capped at about 10 words; I measured this in the browser, and no line on the page exceeds 10 words.
- **Charts, labels and notes:** Source Sans 3 (sans-serif), at least 12 px.
- **Hierarchy:** the main title is largest, then part headings, chart headlines, body text, notes and captions.

## Likely "why" questions

**Why a treemap?**
Groups nest inside kingdoms, a true hierarchy, and area shows part-to-whole.

**Why a heatmap for the time of day, not clocks?**
Aligned rows let you compare seasons hour by hour. Polar small multiples make cross-season comparison hard.

**Why records per 100,000 residents in the choropleth?**
A choropleth of raw totals mostly shows population. Normalising lets states be compared fairly.

**Why a stacked area rather than a stream graph?**
A zero baseline with a labelled y-axis lets readers read totals. Stream graphs often hide the y-axis, which the tutor warned about.

**Why one diverging scale in the seasonal map?**
The data genuinely diverge around 1 (busier or quieter than usual). It uses brown–teal, never red–green.

**Why records per 1,000 km² in the bin map?**
1° squares shrink about 26% from the tropics to Tasmania, so raw counts would favour the north. Density is fair.

**Why do the dot maps use same-size dots?**
A dot map shows where. Sizing the dots would double-encode and turn it into a symbol map. Totals are shown in the proportional symbol map instead.

**Why this projection?**
- Albers equal-area conic, with standard parallels 18°S and 36°S and central meridian 132°E.
- Conic projections suit mid-latitude areas that are wider than tall, so distortion stays low across the continent.
- Equal area is needed because the maps compare quantities across areas.

**Why these colours?**
- Each colour has one meaning across the page: teal = records, purple = species, orange = people, grey = government, charcoal = cane toad.
- The family palette is colour-blind safe, with no red–green pair.
- Every quantitative scale is sequential (one hue, light to dark).

**Why the dashed line in the ridgeline?**
It shows all frogs combined, a proxy for listening effort. Without it, the November FrogID Week surge would look like frogs calling more.

**Why a log scale in the butterfly and dot plot?**
Values range from 1 to 112,472. A linear scale would squash every group except birds. Each log gridline is ×10, and the page says so.

## Interaction (Shneiderman's mantra)

- **Overview first:** the national treemap and the line chart.
- **Zoom and filter:** species list, month slider, Play button, legend click, and linked hover between views.
- **Details on demand:** a tooltip on every chart.

## Limitations to admit (markers reward honesty)

- The year 2025 is excluded from the trend because its records are still arriving.
- FrogID records are filed under a different record type, so they are missing from the sightings source table.

- Chapman's species counts date from 2009, the latest national compilation.
- Records measure observer effort as well as where wildlife actually lives.
- The FrogID data end on 10 November 2023, partway through FrogID Week.

## If asked what you'd improve

Add more years to show trends, add a bioregion map, and use the full ALA download to compare every group by state per person.
