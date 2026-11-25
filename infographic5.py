"""Infographic 5 (draft): one A4 landscape page, static.

01  Which technology leads each canton, through time: 6 small maps in 2 rows (1970, 1980, 2000 | 2014, 2022, 2025).
    Row labels "Hydro era" and "Solar spreads" name the two rows (no grey panels).
    Short annotations under the maps are worked out from the data.
    Colour = technology with the most installed MW in the canton, counting plants commissioned up to that year.
    All technologies are included; natural gas, crude oil and waste form one group "Fossil + waste".
    Black edge = the canton's leading technology changed since the previous map.
02  How the national production mix changed: 100% stacked area, share of each year's TWh by technology
    (1970-2025). Same groups and colours as the maps. Year ticks, triangles and dashed lines mark the map years.
    Both charts start in 1970, the first year
    with hydro and nuclear in the statistics file. "Fossil + waste" = Production_other_total_GWh,
    because fossil and waste are only split from 1990.

Run:  .venv/bin/python infographic5.py
Output: figures/infographic5.pdf and figures/infographic5.png
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

# ------------------------------------------------------------------ 01  LEADING TECHNOLOGY PER CANTON, 8 YEARS
# 6 years: row 1 before solar, row 2 solar spreads (2010 and 2018 dropped: fewest changes).
YEARS = [1970, 1980, 2000, 2014, 2022, 2025]
ROWS = [("Hydro era", YEARS[:3]), ("Solar spreads", YEARS[3:])]
FW = "Fossil + waste"
TECH = {"Hydroelectric power": "Hydro", "Nuclear energy": "Nuclear", "Photovoltaic": "Photovoltaic",
        "Wind energy": "Wind", "Biomass": "Biomass", "Natural gas": FW, "Crude oil": FW, "Waste": FW}
NONE = "No plants"
# one colour per group, shared by the maps and chart 02
ORDER = ["Hydro", "Nuclear", FW, "Biomass", "Wind", "Photovoltaic", NONE]
ORDER_COL = ["#1f77b4", "#7f7f7f", "#d62728", "#8c564b", "#2ca02c", "#ff7f0e", "#ececec"]
plants["Tech"] = plants["SubCategory"].map(TECH)

wide = pd.DataFrame({"KANTONSNUM": list(NUM2ABBR)})
wide["Canton"] = wide["KANTONSNUM"].map(NUM2ABBR)
for i, y in enumerate(YEARS):
    mw = plants[plants["Year"] <= y].groupby(["Canton", "Tech"])["MW"].sum().unstack(fill_value=0)
    wide[f"L{i}"] = wide["Canton"].map(mw.idxmax(axis=1)).fillna(NONE)
    wide[f"C{i}"] = 0 if i == 0 else (wide[f"L{i}"] != wide[f"L{i - 1}"]).astype(int)
used = [t for t in ORDER if t != NONE or (wide[[f"L{i}" for i in range(len(YEARS))]] == t).any().any()]  # legend serves both charts
tech_map_scale = alt.Scale(domain=ORDER, range=ORDER_COL)

shapes = alt.Data(values=cantons["features"])
CELL_W, MAP_H = 300, 140                                       # 3 cells per row
CELL_GAP = 20
TOP_H, NOTE_H = 20, 18
panel_view = alt.ViewBackground(stroke=None)                   # no panel fill (common region not used)


def note_for(i):
    """Short annotation, worked out from the data (empty when nothing to say)."""
    y = YEARS[i]
    if y == 1980:
        nuc = wide.loc[(wide["C1"] == 1) & (wide["L1"] == "Nuclear"), "Canton"].sort_values()
        return ", ".join(nuc) + " → nuclear"
    if y == 2014:
        return f"Solar leads {int((wide[f'L{i}'] == 'Photovoltaic').sum())} cantons"
    if y == YEARS[-1]:
        return f"Solar leads {int((wide[f'L{i}'] == 'Photovoltaic').sum())} of 26"
    return ""


def cell_text(left, right="", size=13, height=TOP_H, weight="bold"):
    d = pd.DataFrame({"l": [left], "r": [right]})
    base = alt.Chart(d)
    return alt.layer(
        base.mark_text(align="left", baseline="middle", fontSize=size, fontWeight=weight, color=INK).encode(
            x=alt.value(8), y=alt.value(height / 2), text="l:N"),
        base.mark_text(align="right", baseline="middle", fontSize=11, fontStyle="italic", color=GREY).encode(
            x=alt.value(CELL_W - 8), y=alt.value(height / 2), text="r:N"),
    ).properties(width=CELL_W, height=height, view=panel_view)


def one_map(i, year, row_label=""):
    fill = alt.Chart(shapes).mark_geoshape(stroke="white", strokeWidth=0.5).transform_lookup(
        lookup="properties.KANTONSNUM", from_=alt.LookupData(wide, "KANTONSNUM", [f"L{i}"])).encode(
        color=alt.Color(f"L{i}:N", scale=tech_map_scale, legend=None))
    edge = alt.Chart(shapes).mark_geoshape(fill=None, stroke="black", strokeWidth=1.6).transform_lookup(
        lookup="properties.KANTONSNUM", from_=alt.LookupData(wide, "KANTONSNUM", [f"C{i}"])).transform_filter(
        f"datum.C{i} == 1")
    m = (fill + edge).project("mercator").properties(width=CELL_W, height=MAP_H, view=panel_view)
    note = cell_text(note_for(i), size=11, height=NOTE_H, weight="normal")
    return alt.vconcat(cell_text(str(year), row_label), m, note, spacing=0)


rows = []
for label, ys in ROWS:
    cells = [one_map(YEARS.index(y), y, label if k == len(ys) - 1 else "") for k, y in enumerate(ys)]
    rows.append(alt.hconcat(*cells, spacing=CELL_GAP))
map_grid = alt.vconcat(*rows, spacing=10)

# legend: one row of swatches + the black edge, centred under the map grid
GRID_W = 3 * CELL_W + 2 * CELL_GAP                             # same width as map_grid
STEP = 110
LEG_W = len(used) * STEP + 105                                 # swatches + "Leader changed" (about 105 px)
x0 = (GRID_W - LEG_W) / 2
xs = alt.Scale(domain=[0, GRID_W], nice=False)
leg = pd.DataFrame({"Tech": used})
leg["x"] = [x0 + k * STEP for k in range(len(used))]
x_edge = x0 + len(used) * STEP
legend = alt.layer(
    alt.Chart(leg).mark_square(size=150, opacity=1).encode(
        x=alt.X("x:Q", axis=None, scale=xs), y=alt.value(8),
        color=alt.Color("Tech:N", scale=tech_map_scale, legend=None)),
    alt.Chart(leg).mark_text(align="left", dx=10, fontSize=11, color=INK).encode(
        x=alt.X("x:Q", scale=xs), y=alt.value(8), text="Tech:N"),
    alt.Chart(pd.DataFrame({"x": [x_edge], "t": ["Leader changed"]})).mark_square(
        size=150, fill="white", stroke="black", strokeWidth=1.6, opacity=1).encode(
        x=alt.X("x:Q", scale=xs), y=alt.value(8)),
    alt.Chart(pd.DataFrame({"x": [x_edge], "t": ["Leader changed"]})).mark_text(
        align="left", dx=10, fontSize=11, color=INK).encode(
        x=alt.X("x:Q", scale=xs), y=alt.value(8), text="t:N"),
).properties(width=GRID_W, height=16)

# ------------------------------------------------------------------ 02  NATIONAL PRODUCTION MIX
# Technology mapping and colours as in EXPLORATION_LOG.md (decisions 3, 4, 7) and infographic.py.
# Same groups and colours as the maps. Fossil + waste = Production_other_total_GWh
# (= Production_other_fossil_GWh + Production_other_renewables_waste_GWh; only split from 1990).
GROUPS = ["Hydro", "Nuclear", FW, "Biomass", "Wind", "Photovoltaic"]  # bottom -> top
cols = {"Hydro": ["Production_run_of_river_GWh", "Production_storage_GWh"],
        "Nuclear": ["Production_nuclear_GWh"],
        FW: ["Production_other_total_GWh"],
        "Biomass": ["Production_wood_GWh", "Production_biogas_GWh"],
        "Wind": ["Production_wind_GWh"],
        "Photovoltaic": ["Production_photovoltaics_GWh"]}
s = stats[stats["Year"] >= 1970]                               # no hydro split before 1970
mix = pd.DataFrame({"Year": s["Year"]})
for g, c in cols.items():
    mix[g] = s[c].fillna(0).sum(axis=1) / 1000                 # GWh -> TWh; NA = not yet recorded
long = mix.melt("Year", var_name="Tech", value_name="TWh")
long["order"] = long["Tech"].map(GROUPS.index)

AREA_W, AREA_H = W - 200, 180
Y_MAX = 1                                                      # shares: 0 to 100% of each year's TWh

last = mix.iloc[-1]
ends = pd.DataFrame({"Tech": GROUPS, "TWh": [last[g] for g in GROUPS]})
ends["frac"] = ends["TWh"] / ends["TWh"].sum()
ends["mid"] = ends["frac"].cumsum() - ends["frac"] / 2
pct = ends["frac"] * 100
ends["t"] = ends["Tech"] + "  " + pct.map(lambda v: f"{v:.1f}%" if v < 1 else f"{v:.0f}%")
gap = 13 * Y_MAX / AREA_H                                      # 13 px between labels, as a share
for k in range(1, len(ends)):                                  # push thin bands' labels apart
    ends.loc[k, "mid"] = max(ends.loc[k, "mid"], ends.loc[k - 1, "mid"] + gap)
x_area = alt.X("Year:Q", title=None, scale=alt.Scale(domain=[1970, 2025], nice=False),
               axis=alt.Axis(format="d", values=YEARS, grid=False, labelPadding=10,   # ticks = map years
                             labelFontSize=11, labelFontWeight="bold", ticks=False, domainColor=LINE))
tech_scale = tech_map_scale                                    # one colour scale for both charts
area = alt.Chart(long).mark_area(opacity=0.95).encode(
    x=x_area,
    y=alt.Y("TWh:Q", title="Share of TWh per year", stack="normalize", scale=alt.Scale(domain=[0, Y_MAX], nice=False),
            axis=alt.Axis(format="%", values=[0, 0.25, 0.5, 0.75, 1], labelFontSize=11, titleFontSize=11, titleColor=GREY,
                          ticks=False, domain=False, gridColor="#eeeeee")),
    color=alt.Color("Tech:N", scale=tech_scale, legend=None),
    order=alt.Order("order:Q"))
labels = alt.Chart(ends).mark_text(align="left", dx=8, fontSize=11, fontWeight="bold").encode(
    x=alt.value(AREA_W), y=alt.Y("mid:Q", scale=alt.Scale(domain=[0, Y_MAX], nice=False)), text="t:N",
    color=alt.Color("Tech:N", scale=tech_scale, legend=None))
# reference lines at the inner map years + markers on the axis: connect each map to its place in time
ref = pd.DataFrame({"Year": YEARS})
rules = alt.Chart(ref[~ref["Year"].isin([YEARS[0], YEARS[-1]])]).mark_rule(
    color="white", strokeDash=[3, 3], strokeWidth=1).encode(x="Year:Q")
marks = alt.Chart(ref).mark_point(shape="triangle-up", filled=True, size=45, color=INK, opacity=1).encode(
    x="Year:Q", y=alt.value(AREA_H + 5))
mix_chart = (area + rules + labels + marks).properties(width=AREA_W, height=AREA_H)


# ------------------------------------------------------------------ TEXT
def text(t, size, color=INK, weight="normal", height=None):
    return alt.Chart(pd.DataFrame({"t": [t]})).mark_text(
        align="left", baseline="top", fontSize=size, color=color, fontWeight=weight).encode(
        x=alt.value(0), y=alt.value(0), text="t:N").properties(width=W - 44, height=height or size * 1.3)


title = text("Electricity in Switzerland: where it was built, what it makes", 22, weight="bold")
_i_last = len(YEARS) - 1
_solar_n = int((wide[f"L{_i_last}"] == "Photovoltaic").sum())
_hn = round(ends.loc[ends["Tech"].isin(["Hydro", "Nuclear"]), "frac"].sum() * 100)
subtitle = text(f"Solar now leads {_solar_n} of 26 cantons, but hydro and nuclear still make "
                f"{_hn}% of the electricity ({YEARS[-1]}).", 13, color=GREY)
h1 = text("01   Which technology leads each canton (most installed MW, 1970–2025)", 14, weight="bold")
footer = text("Sources: BFE/Pronovo plant register (plants operating today; closed plants missing), "
              "BFE electricity statistics, swisstopo swissBOUNDARIES3D.", 8.5, color=GREY)


# ------------------------------------------------------------------ CHECKS
print("Check 1: every canton has a shape:",
      set(NUM2ABBR) == {f["properties"]["KANTONSNUM"] for f in cantons["features"]})
print("Check 2: every SubCategory has a technology:", plants["Tech"].notna().all())
print("Check 4: chart 02 sum equals net production + storage pumps (2025):",
      round(last[GROUPS].sum() * 1000), "vs",
      int(s.iloc[-1]["Production_net_GWh"] + s.iloc[-1]["Consumption_storage_pumps_GWh"]))
print(ends[["Tech", "TWh", "t"]].round(1).to_string(index=False))
print("Check 3: cantons per leading technology and year (each column sums to 26)")
counts = pd.DataFrame({y: wide[f"L{i}"].value_counts() for i, y in enumerate(YEARS)}).reindex(ORDER).fillna(0).astype(int)
print(counts.to_string())
print("  sums:", counts.sum().tolist())
print("Changed cantons per map:")
for i, y in enumerate(YEARS[1:], start=1):
    ch = wide[wide[f"C{i}"] == 1]
    print(f"  {y}:", ", ".join(f"{c} {a}->{b}" for c, a, b in zip(ch["Canton"], ch[f"L{i - 1}"], ch[f"L{i}"])) or "none")


# ------------------------------------------------------------------ PAGE
def strip(c):
    c = c.copy()
    c.config = alt.Undefined
    return c


gap_below_legend = text("", 1, height=16)                     # free space between 01 and 02
page = alt.vconcat(
    strip(title), strip(subtitle), strip(h1), map_grid, legend, strip(gap_below_legend), mix_chart, strip(footer),
    spacing=10
).resolve_scale(color="independent").configure(
    background="white", font="Helvetica", view={"stroke": None}).configure_axis(labelColor=INK)
page = page.properties(padding={"left": PAD, "right": PAD, "top": 22, "bottom": 14})

page.save(OUT / "infographic5.png", scale_factor=2)
page.save(OUT / "infographic5.pdf")
print("saved figures/infographic5.pdf and .png")
