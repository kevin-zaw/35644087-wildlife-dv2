# Who’s watching? How Australians record their wildlife

FIT3179 Data Visualisation 2, Monash University. Author: Kevin Kaung Myat Zaw, October 2026.

A single scrolling web page about wildlife observations in Australia. It covers:

- **What gets recorded:** 154 million records of animals, plants and fungi; six in ten are birds.
- **How the record has grown:** from 2.6 million records in 2007 to 259.5 million in 2026.
- **Who supplies the records:** nearly half come from volunteer birdwatchers.
- **A citizen-science case study:** one open project, the Australian Museum’s FrogID, followed record by record to show where, when and how volunteers record wildlife.

Designed for a 1280 × 800 browser window.

## Charts (16 charts; 12 advanced idioms; 5 maps of 4 map types)

| # | Spec | Idiom | Data |
|---|---|---|---|
| 1 | 01_treemap_national_records | Treemap (Vega) | GBIF report 2026 |
| 2 | 02_line_records_over_time | Step line chart (basic) | GBIF analytics 2026 |
| 3 | 03_butterfly_species_vs_records | Butterfly chart + lollipop (linked) | GBIF + Chapman |
| 4 | 04_waffle_record_sources | Waffle chart | GBIF report 2026 |
| 5 | 05_waffle_frogid_contributors | Paired waffles (linked) | FrogID |
| 6 | 06_calendar_frogid_daily | Calendar heatmap | FrogID |
| 7 | 07_radial_clock_frogid_hours | Radial bar chart, small multiples | FrogID |
| 8 | 08_bin_map_frogid_records | Bin map | FrogID |
| 9–10 | 09_choropleth_frogid_per_capita | Choropleth + connected dot plot (linked) | FrogID + ABS |
| 11 | 10_symbol_map_frog_richness | Proportional symbol map | FrogID |
| 12 | 11_heatmap_latitude_month | Heatmap + bar | FrogID |
| 13 | 12_ridgeline_frog_seasons | Ridgeline (click drives chart 14) | FrogID |
| 14 | 13_dot_map_frog_species_month | Dot map, focus + context, Play animation | FrogID |
| 15 | 14_dotplot_frog_rarity | Dot plot (basic) | FrogID |
| 16 | 15_dot_map_cane_toad | Dot map | FrogID |

## Data sources

1. GBIF analytics for Australia, occ.csv (generated 8 October 2026): https://analytics-files.gbif.org/country/AU/about/csv/
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
