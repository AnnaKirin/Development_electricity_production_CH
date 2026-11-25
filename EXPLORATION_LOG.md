# Exploration log (B.1)

## 2026-11-23 - exploration.py created

**What was done**
- Created `exploration.py`. It reads `cleaned_data/Plants_cleaned.csv`, `cleaned_data/Electricity_statistics.csv` and `cleaned_data/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson`.
- Output goes to `figures/` as HTML. PNG was not saved: package `vl-convert-python` is not installed.
- Run: `.venv/bin/python exploration.py`
- No existing file was changed. The original CSV files stay as they were.

**Figures**
| Figure | Content | Dimensions |
|---|---|---|
| A | Capacity added per year, by technology (from 1900) | time, capacity, technology |
| B | Same per decade (bars) + running total (line). Second level of detail | time, capacity, technology |
| C | Map of capacity per canton + bars per canton and technology | space, capacity, technology |
| D | Share of installed capacity vs share of production, 1960-2025, per technology | time, capacity, production, technology |

**Decisions**
1. Plants and statistics files are not joined by year. Plant year = commissioning year. Statistics year = calendar year of production. Instead: running total of capacity per year, compared with production of the same year, as shares.
2. kW is converted to MW. kW and GWh are never compared directly, only shares.
3. Technology mapping:
   - Hydro run-of-river = all hydro except storage and pumped storage -> `Production_run_of_river_GWh`
   - Hydro storage = Storage + Pumped storage power plant -> `Production_storage_GWh`
   - Nuclear -> `Production_nuclear_GWh`
   - Photovoltaic -> `Production_photovoltaics_GWh`
   - Wind -> `Production_wind_GWh`
   - Biomass = SubCategory Biomass -> `Production_wood_GWh` + `Production_biogas_GWh` (cannot be split in the register)
4. Left out: fossil fuel and waste incineration (217 plants without a match; waste has no clean production column).
5. Years before 1900 are left out of figure A and B bars. Their capacity is still counted in totals and running totals.
6. Figure C: the map is a choropleth of total capacity per canton. Canton number -> abbreviation uses the official BFS numbering (1 = ZH ... 26 = JU). The geojson has 51 shapes (lake parts); all of a canton share one colour.
7. One colour per technology in all figures.
8. Production `NA` is treated as 0 in the shares. In early years no mapped production exists, so the production share is empty there.

**Checks (all passed)**
1. Total MW by year equals total MW by canton.
2. Running total never decreases.
3. Shares sum to 100% in every year (capacity and production; years without mapped production skipped).
4. Every canton in the data has a map shape.
5. 7365 plants have year 2026. They are in figures A and B, not in D (statistics end in 2025).

**Result for 2025 (share of capacity / share of production)**
- Photovoltaic: 34.6% / 12.2%
- Nuclear: 12.1% / 28.3%
- Hydro run-of-river: 15.0% / 25.1%
- Hydro storage: 36.8% / 32.5%
- Wind: 0.4% / 0.2%
- Biomass: 1.0% / 1.7%

**Known limits (for the text of B.1)**
- The register holds only plants that exist today. Closed plants are missing, so capacity in earlier years is too low.

**Open**
- PNG export: install `vl-convert-python`.

## 2026-11-25 - Data description (cleaned_data)

**1. `Plants_cleaned.csv`**: one row per plant, 339,499 rows, 11 columns.

| Column | Type | Empty | Values | Dimension |
|---|---|---|---|---|
| xtf_id | number (id) | 0 | unique per plant | key |
| PostCode | number (id) | 0 | 3,161 codes | space |
| Municipality | text | 0 | 3,903 names | space |
| Canton | text | 0 | 26 cantons | space |
| BeginningOfOperation | year | 0 | 1863 .. 2026 | time |
| TotalPower | kW | 0 | 0.2 .. 1,526,000 | capacity |
| MainCategory | text | 0 | 4 types | technology |
| SubCategory | text | 0 | 8 types | technology |
| PlantCategory | text | 10,529 | 13 types (hydro kinds) | technology |
| _x, _y | coordinates (LV95) | 2,514 | Swiss grid | space |

Plants per SubCategory:

| SubCategory | Plants |
|---|---|
| Photovoltaic | 337,455 |
| Hydroelectric power | 1,325 |
| Biomass | 434 |
| Natural gas | 188 |
| Wind energy | 64 |
| Waste | 28 |
| Nuclear energy | 4 |
| Crude oil | 1 |

**2. `Electricity_statistics.csv`**: one row per year, 66 rows (1960-2025), 18 columns, all in GWh.

| Columns | Empty years | Data from |
|---|---|---|
| Production_run_of_river, _storage | 10 | 1970 |
| Production_nuclear | 9 | 1969 |
| Production_other_total | 0 | 1960 |
| Production_other_fossil, _renewables_waste, _wood, _biogas, _photovoltaics, _wind | 30 | 1990 |
| Consumption_storage_pumps, Production_net, Imports, Exports, Domestic_consumption, End_consumption | 0 | 1960 |
| Losses | 0 | 1960 |

Solar has only 30 years of production data, from 1990.

**3. `swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson`**: canton shapes.

| Item | Value |
|---|---|
| Shapes | 51 (26 cantons plus lake parts) |
| Key used | KANTONSNUM (1 = ZH ... 26 = JU) |
| Other fields | NAME, KANTONSFLA (area), EINWOHNERZ (people) |

## 2026-11-25 - infographic4.py: shares as the common unit

**Decision**
- Chart 01 (map) is in MW and chart 02 (production mix) is in TWh. These units cannot be converted into each other: MW is capacity (how much can be produced at once), TWh is energy (how much was produced in a year).
- Both charts therefore use shares (%) as the common unit:
  - 01: share of the canton's installed MW held by its dominant technology (plants commissioned up to 2025).
  - 02: share of each year's national TWh per technology (100% stacked area, 1970-2025).
- Both charts end in 2025, the last year of the statistics file.
- Alternatives rejected: both in MW (loses the production story), both in TWh (canton TWh would be an estimate from national full-load hours), keeping both units (reader must notice the unit change).
- Cost: chart 02 no longer shows that total production grew; it shows only the mix.
