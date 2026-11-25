"""Infographic 3 (simplified draft): one A4 landscape page, static.

01  Map series: installed capacity per canton in selected years (1900-2026), small multiples.
    Colour = MW of all plants commissioned up to that year (running total).
02  How the national production mix changed: stacked area, TWh per year by technology (1970-2025).

Run:  .venv/bin/python infographic3.py
Output: figures/infographic3.pdf and figures/infographic3.png
Reads only cleaned_data/.
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

PAGE_W, PAGE_H = 1123, 794           # A4 landscape at 96 dpi
PAD = 29
W = PAGE_W - 2 * PAD
INK, GREY, LINE = "#222222", "#777777", "#bbbbbb"

# ------------------------------------------------------------------ LOAD
plants = pd.read_csv(DATA / "Plants_cleaned.csv").rename(columns={"BeginningOfOperation": "Year"})
stats = pd.read_csv(DATA / "Electricity_statistics.csv")
cantons = json.load(open(DATA / "swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson"))
plants["MW"] = plants["TotalPower"] / 1000           # register gives kW

NUM2ABBR = dict(enumerate("ZH BE LU UR SZ OW NW GL ZG FR SO BS BL SH AR AI SG GR AG TG TI VD VS NE GE JU".split(), start=1))

YEARS = [1900, 1920, 1940, 1960, 1980, 2000, 2020, 2026]
LABELS = [str(y) for y in YEARS]

# ------------------------------------------------------------------ 01  INSTALLED CAPACITY PER CANTON IN A YEAR
# Installed in year Y = sum of MW of all plants commissioned in or before Y (running total, plants before 1900 included).

BINS = ["No plants", "< 10 MW", "10–100 MW", "100–1,000 MW", "≥ 1,000 MW"]
BIN_COL = ["#ececec", "#dadaeb", "#9e9ac8", "#6a51a3", "#3f007d"]   # ColorBrewer Purples: light = little, dark = much


def bin_of(mw):
    if pd.isna(mw):
        return BINS[0]
    return BINS[1] if mw < 10 else BINS[2] if mw < 100 else BINS[3] if mw < 1000 else BINS[4]


wide = pd.DataFrame({"KANTONSNUM": list(NUM2ABBR)})
wide["Canton"] = wide["KANTONSNUM"].map(NUM2ABBR)
for i, y in enumerate(YEARS):
    installed = plants[plants["Year"] <= y].groupby("Canton")["MW"].sum()
    wide[f"b{i}"] = wide["Canton"].map(installed).map(bin_of)

color_scale = alt.Scale(domain=BINS, range=BIN_COL)
shapes = alt.Data(values=cantons["features"])
MAP_W, MAP_H = 236, 155


def one_map(i, per):
    return alt.Chart(shapes).mark_geoshape(stroke="white", strokeWidth=0.5).transform_lookup(
        lookup="properties.KANTONSNUM", from_=alt.LookupData(wide, "KANTONSNUM", [f"b{i}"])).encode(
        color=alt.Color(f"b{i}:N", scale=color_scale, legend=None)).project("mercator").properties(
        width=MAP_W, height=MAP_H,
        title=alt.TitleParams(per, anchor="start", fontSize=13, fontWeight="bold", color=INK, offset=2))


maps = [one_map(i, per) for i, per in enumerate(LABELS)]
map_grid = alt.vconcat(alt.hconcat(*maps[:4], spacing=28), alt.hconcat(*maps[4:], spacing=28), spacing=8)

leg = pd.DataFrame({"Bin": BINS, "x": [0, 100, 180, 285, 410]})
xs = alt.Scale(domain=[0, W])
legend = alt.layer(
    alt.Chart(leg).mark_square(size=150, opacity=1).encode(
        x=alt.X("x:Q", axis=None, scale=xs), y=alt.value(8),
        color=alt.Color("Bin:N", scale=color_scale, legend=None)),
    alt.Chart(leg).mark_text(align="left", dx=10, fontSize=11, color=INK).encode(
        x=alt.X("x:Q", scale=xs), y=alt.value(8), text="Bin:N"),
).properties(width=W - 44, height=16)

# ------------------------------------------------------------------ 02  NATIONAL PRODUCTION MIX
# Technology mapping and colours as in EXPLORATION_LOG.md (decisions 3, 4, 7) and infographic.py.
# Fossil and waste are left out: the register has no clean match for them.
GROUPS = ["Hydro run-of-river", "Hydro storage", "Nuclear", "Biomass", "Wind", "Photovoltaic"]  # bottom -> top
GROUP_COL = ["#1f77b4", "#17becf", "#7f7f7f", "#8c564b", "#2ca02c", "#ff7f0e"]
cols = {"Hydro run-of-river": ["Production_run_of_river_GWh"],
        "Hydro storage": ["Production_storage_GWh"],
        "Nuclear": ["Production_nuclear_GWh"],
        "Biomass": ["Production_wood_GWh", "Production_biogas_GWh"],
        "Wind": ["Production_wind_GWh"],
        "Photovoltaic": ["Production_photovoltaics_GWh"]}
s = stats[stats["Year"] >= 1970]                               # no split by technology before 1970
mix = pd.DataFrame({"Year": s["Year"]})
for g, c in cols.items():
    mix[g] = s[c].fillna(0).sum(axis=1) / 1000                 # GWh -> TWh; NA = not yet recorded
long = mix.melt("Year", var_name="Tech", value_name="TWh")
long["order"] = long["Tech"].map(GROUPS.index)

AREA_W, AREA_H = W - 200, 235
Y_MAX = 10 * -(-mix[GROUPS].sum(axis=1).max() // 10)          # round up to next 10 TWh

last = mix.iloc[-1]
ends = pd.DataFrame({"Tech": GROUPS, "TWh": [last[g] for g in GROUPS]})
ends["mid"] = ends["TWh"].cumsum() - ends["TWh"] / 2
share = ends["TWh"] / ends["TWh"].sum() * 100
ends["t"] = ends["Tech"] + "  " + share.map(lambda v: f"{v:.1f}%" if v < 1 else f"{v:.0f}%")
gap = 13 * Y_MAX / AREA_H                                      # 13 px between labels, in TWh
for k in range(1, len(ends)):                                  # push thin bands' labels apart
    ends.loc[k, "mid"] = max(ends.loc[k, "mid"], ends.loc[k - 1, "mid"] + gap)
x_area = alt.X("Year:Q", title=None, scale=alt.Scale(domain=[1970, 2025], nice=False),
               axis=alt.Axis(format="d", values=[1970, 1980, 1990, 2000, 2010, 2020, 2025], grid=False,
                             labelFontSize=11, ticks=False, domainColor=LINE))
tech_scale = alt.Scale(domain=GROUPS, range=GROUP_COL)
area = alt.Chart(long).mark_area(opacity=0.95).encode(
    x=x_area,
    y=alt.Y("TWh:Q", title="TWh per year", stack="zero", scale=alt.Scale(domain=[0, Y_MAX], nice=False),
            axis=alt.Axis(tickCount=4, labelFontSize=11, titleFontSize=11, titleColor=GREY,
                          ticks=False, domain=False, gridColor="#eeeeee")),
    color=alt.Color("Tech:N", scale=tech_scale, legend=None),
    order=alt.Order("order:Q"))
# faint lines at the map years, to link 02 to 01
rules = alt.Chart(pd.DataFrame({"Year": [1980, 2000, 2020]})).mark_rule(
    color="white", strokeDash=[3, 3], strokeWidth=1).encode(x="Year:Q")
labels = alt.Chart(ends).mark_text(align="left", dx=8, fontSize=11, fontWeight="bold").encode(
    x=alt.value(AREA_W), y=alt.Y("mid:Q", scale=alt.Scale(domain=[0, Y_MAX], nice=False)), text="t:N",
    color=alt.Color("Tech:N", scale=tech_scale, legend=None))
mix_chart = (area + rules + labels).properties(width=AREA_W, height=AREA_H)


# ------------------------------------------------------------------ TEXT
def text(t, size, color=INK, weight="normal", height=None):
    return alt.Chart(pd.DataFrame({"t": [t]})).mark_text(
        align="left", baseline="top", fontSize=size, color=color, fontWeight=weight).encode(
        x=alt.value(0), y=alt.value(0), text="t:N").properties(width=W - 44, height=height or size * 1.3)


title = text("Electricity in Switzerland: where it was built, what it makes", 22, weight="bold")
h1 = text("01   Evolution of installed electricity capacity (MW per canton, 1900–2026)", 14, weight="bold")
h2 = text("02   How the national production mix changed (TWh per year, share in 2025)", 14, weight="bold")
footer = text("Sources: BFE/Pronovo plant register (plants operating today; closed plants missing), "
              "BFE electricity statistics, swisstopo swissBOUNDARIES3D.  "
              "Fossil and waste not shown.", 8.5, color=GREY)


# ------------------------------------------------------------------ CHECKS
print("Check 1: every canton has a shape:",
      set(NUM2ABBR) == {f["properties"]["KANTONSNUM"] for f in cantons["features"]})
print("Check 2: mix sum + fossil/waste equals net production + storage pumps (2025):",
      round((last[GROUPS].sum()) * 1000 + s.iloc[-1]["Production_other_total_GWh"]), "vs",
      int(s.iloc[-1]["Production_net_GWh"] + s.iloc[-1]["Consumption_storage_pumps_GWh"]))
print("Check 3: cantons per colour class and year")
print(pd.DataFrame({per: wide[f"b{i}"].value_counts() for i, per in enumerate(LABELS)})
      .reindex(BINS).fillna(0).astype(int).to_string())
print(ends[["Tech", "TWh", "t"]].round(1).to_string(index=False))


# ------------------------------------------------------------------ PAGE
def strip(c):
    c = c.copy()
    c.config = alt.Undefined
    return c


page = alt.vconcat(
    strip(title), strip(h1), legend, map_grid, strip(h2), mix_chart, strip(footer), spacing=10
).resolve_scale(color="independent").configure(
    background="white", font="Helvetica", view={"stroke": None}).configure_axis(labelColor=INK)
page = page.properties(padding={"left": PAD, "right": PAD, "top": 22, "bottom": 14})

page.save(OUT / "infographic3.png", scale_factor=2)
page.save(OUT / "infographic3.pdf")
print("saved figures/infographic3.pdf and .png")
