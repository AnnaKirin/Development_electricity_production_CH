    """B.1 Visual data exploration: electricity production in Switzerland.

Run:  .venv/bin/python exploration.py
Output: figures/*.html (and *.png if the package vl-convert-python is installed)
"""
import json
from pathlib import Path

import altair as alt
import pandas as pd

BASE = Path(__file__).parent
DATA = BASE / "cleaned_data"
OUT = BASE / "figures"
OUT.mkdir(exist_ok=True)

alt.data_transformers.disable_max_rows()


def save(chart, name):
    chart.save(OUT / f"{name}.html")
    try:
        chart.save(OUT / f"{name}.png", scale_factor=2)
    except Exception as e:  # vl-convert-python missing
        print(f"  (no PNG for {name}: {type(e).__name__})")
    print("saved", name)


# ---------------------------------------------------------------- 0. LOAD
plants = pd.read_csv(DATA / "Plants_cleaned.csv")
stats = pd.read_csv(DATA / "Electricity_statistics.csv")  # "NA" -> NaN
cantons = json.load(open(DATA / "swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson"))

print("Plants:", len(plants), "| years", plants.BeginningOfOperation.min(), "-", plants.BeginningOfOperation.max())
print("Statistics years:", stats.Year.min(), "-", stats.Year.max())
print("Empty values in plants:\n", plants[["Canton", "BeginningOfOperation", "TotalPower", "SubCategory"]].isna().sum())

plants = plants.rename(columns={"BeginningOfOperation": "Year"})
plants["Power_MW"] = plants["TotalPower"] / 1000  # kW -> MW


# Technology = shared link between the two files (my own grouping, see README of the figures)
def technology(row):
    sub, plant = row["SubCategory"], row["PlantCategory"]
    if sub == "Hydroelectric power":
        return "Hydro storage" if plant in ("Storage power plant", "Pumped storage power plant") else "Hydro run-of-river"
    return {"Nuclear energy": "Nuclear", "Photovoltaic": "Photovoltaic",
            "Wind energy": "Wind", "Biomass": "Biomass (wood, biogas)"}.get(sub)


plants["Technology"] = plants.apply(technology, axis=1)
print("Plants without a technology match (fossil, waste, ...):", plants.Technology.isna().sum())
tech_plants = plants.dropna(subset=["Technology"])

TECH_ORDER = ["Hydro run-of-river", "Hydro storage", "Nuclear", "Photovoltaic", "Wind", "Biomass (wood, biogas)"]
COLORS = ["#1f77b4", "#17becf", "#7f7f7f", "#ff7f0e", "#2ca02c", "#8c564b"]
tech_color = alt.Color("Technology:N", scale=alt.Scale(domain=TECH_ORDER, range=COLORS))

# ---------------------------------------------------------------- FIGURE A (time, capacity, technology)
by_year = tech_plants.groupby(["Year", "Technology"], as_index=False)["Power_MW"].sum()
by_year = by_year[by_year.Year >= 1900]

fig_a = alt.Chart(by_year).mark_bar().encode(
    x=alt.X("Year:Q", title="Year of commissioning", scale=alt.Scale(zero=False), axis=alt.Axis(format="d")),
    y=alt.Y("Power_MW:Q", title="Capacity added per year (MW)"),
    color=tech_color,
    tooltip=["Year:Q", "Technology:N", alt.Tooltip("Power_MW:Q", format=",.0f")],
).properties(width=700, height=300, title="A: capacity added per year, by technology")
save(fig_a, "figA_capacity_per_year")

# ---------------------------------------------------------------- FIGURE B (coarser level: decade + running total)
by_year["Decade"] = (by_year.Year // 10) * 10
by_decade = by_year.groupby(["Decade", "Technology"], as_index=False)["Power_MW"].sum()

total_year = by_year.groupby("Year", as_index=False)["Power_MW"].sum().sort_values("Year")
total_year["Installed_MW"] = total_year["Power_MW"].cumsum()

bars = alt.Chart(by_decade).mark_bar().encode(
    x=alt.X("Decade:O", title="Decade of commissioning"),
    y=alt.Y("Power_MW:Q", title="Capacity added per decade (MW)"),
    color=tech_color,
    tooltip=["Decade:O", "Technology:N", alt.Tooltip("Power_MW:Q", format=",.0f")],
)
line = alt.Chart(total_year).mark_line(color="black").encode(
    x=alt.X("Year:Q", axis=None, scale=alt.Scale(zero=False)),
    y=alt.Y("Installed_MW:Q", title="Installed capacity, running total (MW)"),
)
fig_b = alt.layer(bars, line).resolve_scale(x="independent", y="independent").properties(
    width=700, height=300, title="B: per decade (bars) and running total (line)")
save(fig_b, "figB_decade_and_running_total")

# ---------------------------------------------------------------- FIGURE C (space, capacity, technology)
by_canton = tech_plants.groupby(["Canton", "Technology"], as_index=False)["Power_MW"].sum()
canton_total = by_canton.groupby("Canton", as_index=False)["Power_MW"].sum()

# BFS canton number -> abbreviation (official numbering)
NUM2ABBR = dict(enumerate(
    "ZH BE LU UR SZ OW NW GL ZG FR SO BS BL SH AR AI SG GR AG TG TI VD VS NE GE JU".split(), start=1))
canton_total["KANTONSNUM"] = canton_total["Canton"].map({v: k for k, v in NUM2ABBR.items()})

map_chart = alt.Chart(alt.Data(values=cantons["features"])).mark_geoshape(stroke="white").transform_lookup(
    lookup="properties.KANTONSNUM",
    from_=alt.LookupData(canton_total, "KANTONSNUM", ["Canton", "Power_MW"]),
).encode(
    color=alt.Color("Power_MW:Q", title="Capacity (MW)", scale=alt.Scale(scheme="oranges")),
    tooltip=["Canton:N", alt.Tooltip("Power_MW:Q", format=",.0f")],
).project("mercator").properties(width=420, height=300, title="C1: installed capacity per canton")

order = canton_total.sort_values("Power_MW", ascending=False)["Canton"].tolist()
bars_c = alt.Chart(by_canton).mark_bar().encode(
    y=alt.Y("Canton:N", sort=order, title=None),
    x=alt.X("Power_MW:Q", title="Capacity (MW)"),
    color=tech_color,
    tooltip=["Canton:N", "Technology:N", alt.Tooltip("Power_MW:Q", format=",.0f")],
).properties(width=380, height=420, title="C2: capacity per canton and technology")
save(map_chart | bars_c, "figC_cantons")

# ---------------------------------------------------------------- FIGURE D (share of capacity vs share of production)
PROD_COLS = {
    "Hydro run-of-river": ["Production_run_of_river_GWh"],
    "Hydro storage": ["Production_storage_GWh"],
    "Nuclear": ["Production_nuclear_GWh"],
    "Photovoltaic": ["Production_photovoltaics_GWh"],
    "Wind": ["Production_wind_GWh"],
    "Biomass (wood, biogas)": ["Production_wood_GWh", "Production_biogas_GWh"],
}
prod = pd.DataFrame({"Year": stats.Year})
for tech, cols in PROD_COLS.items():
    prod[tech] = stats[cols].sum(axis=1, min_count=1)  # NaN stays NaN unless one column has a value
prod_long = prod.melt("Year", var_name="Technology", value_name="GWh").fillna({"GWh": 0})

# installed capacity per year and technology (running total), on a full year grid
grid = pd.MultiIndex.from_product([range(1960, int(stats.Year.max()) + 1), TECH_ORDER], names=["Year", "Technology"])
added = tech_plants.groupby(["Year", "Technology"])["Power_MW"].sum()
cap_before = added[added.index.get_level_values("Year") < 1960].groupby("Technology").sum()
cap = added.reindex(grid, fill_value=0).reset_index()
cap["Installed_MW"] = cap.groupby("Technology")["Power_MW"].cumsum() + cap["Technology"].map(cap_before).fillna(0)

d = cap.merge(prod_long, on=["Year", "Technology"])
d["Share of capacity"] = d["Installed_MW"] / d.groupby("Year")["Installed_MW"].transform("sum") * 100
d["Share of production"] = d["GWh"] / d.groupby("Year")["GWh"].transform("sum") * 100
d_long = d.melt(["Year", "Technology"], ["Share of capacity", "Share of production"],
                var_name="Measure", value_name="Share_percent")

fig_d = alt.Chart(d_long).mark_line().encode(
    x=alt.X("Year:Q", scale=alt.Scale(zero=False), axis=alt.Axis(format="d")),
    y=alt.Y("Share_percent:Q", title="Share of total (%)"),
    color=alt.Color("Measure:N", scale=alt.Scale(range=["#d62728", "#1f77b4"])),
    strokeDash="Measure:N",
    tooltip=["Year:Q", "Technology:N", "Measure:N", alt.Tooltip("Share_percent:Q", format=".1f")],
).properties(width=220, height=150).facet(facet=alt.Facet("Technology:N", sort=TECH_ORDER), columns=3,
                                          title="D: share of installed capacity vs share of production")
save(fig_d, "figD_share_capacity_vs_production")

# ---------------------------------------------------------------- CHECKS
print("\n=== CHECKS ===")
# 1 totals agree by year and by canton
print("1. total MW by year == by canton:",
      abs(by_year.Power_MW.sum() + tech_plants[tech_plants.Year < 1900].Power_MW.sum() - canton_total.Power_MW.sum()) < 1e-6)
# 2 odd years
print("2. rows with year < 1900 or > 2025:", int(((plants.Year < 1900) | (plants.Year > 2025)).sum()))
# 3 running total never decreases
print("3. running total only grows:", bool(total_year.Installed_MW.is_monotonic_increasing))
# 4 shares sum to 100
sums = d.groupby("Year")[["Share of capacity", "Share of production"]].sum().round(6)
print("4. shares sum to 100 in every year (capacity, production):",
      bool(((sums["Share of capacity"] - 100).abs() < 1e-6).all()), bool(((sums["Share of production"] - 100).abs() < 1e-6)[d.groupby("Year")["GWh"].sum() > 0].all()), "(years without mapped production skipped)")
# 5 cantons without a map shape
missing = set(canton_total.Canton) - {NUM2ABBR[f["properties"]["KANTONSNUM"]] for f in cantons["features"]}
print("5. cantons in data without a map shape:", missing or "none")
# 6 key numbers for the insight (latest year)
last = d[d.Year == d.Year.max()].set_index("Technology")[["Share of capacity", "Share of production"]].round(1)
print("6. shares in", int(d.Year.max()), "(%):\n", last)
print("\nNote: the register holds only plants that exist today; closed plants are missing,")
print("so capacity in earlier years is too low. kW and GWh are never compared directly, only shares.")
