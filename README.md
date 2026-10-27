# Who’s watching? How Australians record their wildlife

FIT3179 Data Visualisation 2, Monash University. Author: Kevin Kaung Myat Zaw, October 2026.

A single scrolling web page about wildlife observations in Australia. It covers:

- **What gets recorded:** 154 million records of animals, plants and fungi; six in ten are birds.
- **How the record has grown:** from 2.6 million records in 2007 to 259.5 million in 2026.
- **Who supplies the records:** nearly half come from volunteer birdwatchers.
- **A citizen-science case study:** one open project, the Australian Museum’s FrogID, followed record by record to show where, when and how volunteers record wildlife.

Designed for a 1280 × 800 browser window.

## Charts (18 charts; 10 advanced idioms; 5 maps of 4 map types)

| # | Spec | Idiom | Data |
|---|---|---|---|
| 1 | 01_treemap_national_records | Treemap (Vega) | GBIF 2026 |
| 2 | 02_line_records_over_time | Step line chart (basic) | GBIF analytics |
| 3 | 03_area_public_sightings | Stacked area chart (basic) | ALA download |
| 4 | 04_butterfly_species_vs_records | Butterfly chart + lollipop | GBIF + Chapman |
| 5 | 05_waffle_record_sources | Waffle chart | GBIF 2026 |
| 6 | 06_heatmap_sources_by_group | Heatmap + type strip | ALA download |
| 7 | 07_waffle_frogid_contributors | Paired waffles | FrogID |
| 8 | 08_calendar_frogid_daily | Calendar heatmap | FrogID |
| 9 | 09_heatmap_frogid_season_hour | Heatmap | FrogID |
| 10 | 10_bin_map_wildlife_density | Bin map, group selector | ALA download |
| 11–12 | 11_choropleth_wildlife_per_capita | Choropleth + lollipop (linked) | ALA + ABS |
| 13 | 12_symbol_map_frog_richness | Proportional symbol map | FrogID |
| 14 | 13_ridgeline_wildlife_months | Ridgeline | ALA download |
| 15 | 14_heatmap_wildlife_latitude_month | Heatmap + bar (click drives 16) | ALA download |
| 16 | 15_bin_map_wildlife_seasons | Bin map, month slider + Play | ALA download |
| 17 | 16_dotplot_frog_rarity | Dot plot (basic) | FrogID |
| 18 | 17_dot_map_cane_toad | Dot map | FrogID |

## Reproducing the data

1. `python scripts/download_wildlife_data.py`: downloads ALA counts into `data/ala/` (the files used are kept in `data/ala/raw_download/`).
2. `python scripts/prepare_ala_data.py`: turns them into the chart files in `data/ala/`.
3. `scripts/process.py` prepares the FrogID files.

## Data sources

1. Atlas of Living Australia biocache record counts, downloaded 27 October 2026 (see data/ala/raw_download/manifest.json)
2. GBIF analytics for Australia, occ.csv (generated 8 October 2026): https://analytics-files.gbif.org/country/AU/about/csv/
2. GBIF activity report: Australia (January 2026): https://analytics-files.gbif.org/country/AU/GBIF_CountryReport_AU.pdf
3. Chapman, A.D. (2009). *Numbers of Living Species in Australia and the World*, 2nd edition. Australian Biological Resources Study.
4. FrogID dataset 6.0, Australian Museum, 2023 records (via TidyTuesday, 2 September 2025). Rowley & Callaghan (2020), *ZooKeys* 912: 139–151.
5. Australian Bureau of Statistics, *National, state and territory population*, June 2023.
6. Australian Society of Herpetologists species list; Natural Earth 1:50m boundaries.

Adapted examples: Vega-Lite example gallery (ridgeline, radial, waffle, annotations, choropleth lookup) and the Vega treemap example.

## Step still to do: download the all-wildlife data

Run `scripts/download_wildlife_data.py` in VS Code (see `HOW_TO_DOWNLOAD_DATA.md`). It downloads counts of all Australian wildlife records from the Atlas of Living Australia, by group, year, month, state, 1° square and data source, with a GBIF fallback. It writes the tables to `data/ala/` and bundles them as `results_for_claude.zip`.

## Run locally

Run `python -m http.server 8000` in this folder, then open http://localhost:8000.

## Use of generative AI

Anthropic’s Claude helped write the data script, chart specifications, page code and draft text. The author checked every number against the sources.

## Licence

Text and charts © 2026 Kevin Kaung Myat Zaw, CC BY 4.0. Data remain under their original licences.
