# Information Visualisation — Module Task

**Topic:** Development of electricity production in Switzerland — how the fleet of
power plants was built up across the country and across technologies, and how this
relates to the electricity actually produced over time.

## Datasets

**[1] Register of electricity production plants in Switzerland** — one record per plant:
location/canton, year of commissioning, installed capacity (kW), and energy/technology
type. 1863 - 2025.

**[2] Swiss national electricity balance, annual values (from 1960)** — electricity
produced per technology (GWh/year), plus imports, exports, consumption and losses.

## Data Sources

**[1]** *Elektrizitätsproduktionsanlagen / Electricity production plants*, Swiss Federal
Office of Energy (BFE), operated via Pronovo AG, published as Open Government Data:
- opendata.swiss: https://opendata.swiss/en/dataset/elektrizitatsproduktionsanlagen
- Files used: `ElectricityProductionPlant.csv` + lookup catalogues
  `MainCategoryCatalogue.csv` and `SubCategoryCatalogue.csv`.

**[2]** *Elektrizitätsbilanz der Schweiz – Jahreswerte / Swiss electricity balance –
annual values*, Swiss Federal Office of Energy (BFE), Electricity Statistics, published
as Open Government Data:
- Electricity statistics overview: https://www.bfe.admin.ch/en/electricity-statistics
- opendata.swiss portal (BFE electricity statistics, dataset OGD32): https://opendata.swiss
- File used: `ogd32_elektrizitaetbilanz_jahreswerte.csv`.

Both datasets are public BFE Open Government Data (free use with source attribution).

## Four Substantial Data Dimensions

- **Space** — canton / location of each power plant across Switzerland (dataset [1]).
- **Time** — year of commissioning per plant (dataset [1]) and year of production,
  annual series from 1960 onwards (dataset [2]).
- **Attribute** — installed capacity per plant (kW, dataset [1]) and electricity actually
  produced (GWh/year, dataset [2]).
- **Attribute** — energy / technology type: photovoltaic, hydropower, wind, nuclear, etc.
  — the shared link between [1] and [2].

## Research Questions

1. How is electricity production capacity distributed geographically across Switzerland,
   and which cantons/regions concentrate the most installed capacity (and in which
   technologies)?
2. How has the mix of production technologies developed over time, and does the strong
   growth in installed photovoltaic capacity translate into a comparable share of the
   electricity actually produced?

## Task 
1. Part B.1 - Visual Data Exploration
1-2 A4 pages of 2 or 3 exploration graphics (static visualizations in the pdf document, 
screen-shot and working URL for dynamic visualizations [note: dynamic visualizations are 
NOT a requirement]), show at least two different levels of aggregation of one of the data 
dimensions (e.g., daily data in one graphic and aggregated weekly data in another graphic) 
and use at least three of your four substantial data dimensions 1 A4 page of structured 
description (maximum 500 words, word count does not include detailed references to sources 
of the used raw data and any other information used for the task) how your visual exploration 
of which data lead to the insight(s) communicated in B.2, how you verified your insights, 
and how you ensure that B.2 clearly communicates the insight(s) (design aspects).

2. Part B.2 - Visual Insight(s) Communication
Single communication visualization / Information Graphic (maximum 1 A4 page, static) 
that communicates and explains the insight(s)

