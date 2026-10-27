# Who’s watching? How Australians record their wildlife

**Live page:** https://kevin-zaw.github.io/35644087-wildlife-dv2/

FIT3179 Data Visualisation 2, Monash University. Kevin Kaung Myat Zaw (35644087), October 2026.

A scrolling data story about 154 million records of Australian animals, plants and fungi: what gets recorded, who records it, how volunteers record (a FrogID spotlight), where and when people look, and why every record counts. It has 18 charts built with Vega-Lite 5 and one Vega treemap, designed for a 1280 × 800 browser window.

## Contents

- `index.html`, `css/`, `js/main.js`: the page; `main.js` embeds each spec into its `div` (`#c01`–`#c17`).
- `specs/`: one JSON specification per chart.
- `data/`: chart data (about 1 MB). `data/ala/raw_download/` holds the Atlas of Living Australia download and its query log (`manifest.json`).
- `scripts/`: `download_wildlife_data.py` (ALA download), `prepare_ala_data.py` (ALA chart files), `process.py` (FrogID chart files).
- `sketch/sketch.pdf`: the hand-drawn sketch.

## Data sources

1. Atlas of Living Australia record counts, downloaded 27 October 2026.
2. GBIF analytics for Australia (October 2026) and the GBIF activity report for Australia (January 2026).
3. Chapman (2009), *Numbers of Living Species in Australia and the World*, ABRS.
4. FrogID dataset 6.0 (2023 records, via TidyTuesday 2025-09-02), Australian Museum. Dataset 7.0 (September 2026) figures are quoted in the text.
5. Australian Bureau of Statistics, state population at 30 June 2023.
6. Natural Earth 1:50m boundaries.

Full citations and links are in the page footer.

## Use of generative AI

Anthropic’s Claude helped write the scripts, chart specifications, page code and draft text. The author checked every number against the sources.

## Licence

Text and charts © 2026 Kevin Kaung Myat Zaw, CC BY 4.0. Data remain under their original licences.
