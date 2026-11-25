"""Infographic 4 (draft): one A4 landscape page, static.

01  Which technology dominates each canton: one map.
    Hue = technology with the most installed MW in the canton (all plants commissioned up to 2025).
    Light -> dark = that technology's share of the canton's MW.
02  How the national production mix changed: 100% stacked area, share of each year's TWh by technology
    (1970-2025). Same data as in infographic3.py, shown as shares so both charts use %.

Run:  .venv/bin/python infographic4.py
Output: figures/infographic4.pdf and figures/infographic4.png
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

# ------------------------------------------------------------------ 01  DOMINANT TECHNOLOGY PER CANTON
# Share = MW of a SubCategory / all MW in the canton (plants commissioned up to 2025, same last year as 02).
# Only three SubCategories win anywhere: Hydroelectric power, Nuclear energy, Photovoltaic.
TOP = {"Hydroelectric power": "Hydro", "Nuclear energy": "Nuclear", "Photovoltaic": "Photovoltaic"}
STEPS = ["< 60%", "60–80%", "≥ 80%"]
# light -> dark per hue; the darkest step is the colour used in chart 02
SHADES = {"Hydro": ["#c6dbef", "#6baed6", "#1f77b4"],
          "Nuclear": ["#e0e0e0", "#bdbdbd", "#7f7f7f"],
          "Photovoltaic": ["#fee6ce", "#fdae6b", "#ff7f0e"]}

MAP_YEAR = 2025
mw = plants[plants["Year"] <= MAP_YEAR].groupby(["Canton", "SubCategory"])["MW"].sum().unstack(fill_value=0)
share = mw.div(mw.sum(axis=1), axis=0)
dom = pd.DataFrame({"Canton": share.index,
                    "Sub": share.idxmax(axis=1).values,
                    "Share": (share.max(axis=1) * 100).values})
dom["Tech"] = dom["Sub"].map(TOP)
dom["Step"] = pd.cut(dom["Share"], [0, 60, 80, 101], right=False, labels=STEPS).astype(str)
dom["Key"] = dom["Tech"] + " " + dom["Step"]
dom["Fill"] = [SHADES[t][STEPS.index(s)] for t, s in zip(dom["Tech"], dom["Step"])]
dom["TextCol"] = ["white" if s == STEPS[2] else INK for s in dom["Step"]]
dom["KANTONSNUM"] = dom["Canton"].map({v: k for k, v in NUM2ABBR.items()})


# label point per canton: mean of the vertices of its largest polygon part
def label_point(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    ring = max((p[0] for p in polys), key=len)
    return sum(c[0] for c in ring) / len(ring), sum(c[1] for c in ring) / len(ring)


pts = {}
for f in cantons["features"]:
    n = f["properties"]["KANTONSNUM"]
    lon, lat = label_point(f["geometry"])
    size = len(max((p[0] for p in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon"
                                   else [f["geometry"]["coordinates"]])), key=len))
    if n not in pts or size > pts[n][2]:
        pts[n] = (lon, lat, size)
dom["lon"] = dom["KANTONSNUM"].map(lambda n: pts[n][0])
dom["lat"] = dom["KANTONSNUM"].map(lambda n: pts[n][1])

MAP_W, MAP_H = 600, 340
shapes = alt.Data(values=cantons["features"])
fill = alt.Chart(shapes).mark_geoshape(stroke="white", strokeWidth=0.8).transform_lookup(
    lookup="properties.KANTONSNUM", from_=alt.LookupData(dom, "KANTONSNUM", ["Fill"])).encode(
    color=alt.Color("Fill:N", scale=None))
names = alt.Chart(dom).mark_text(fontSize=9, fontWeight="bold").encode(
    longitude="lon:Q", latitude="lat:Q", text="Canton:N", color=alt.Color("TextCol:N", scale=None))
dom_map = (fill + names).project("mercator").properties(width=MAP_W, height=MAP_H)

# legend: rows = technology, columns = share step
leg = pd.DataFrame([{"Tech": t, "Step": s, "Fill": SHADES[t][i]} for t in SHADES for i, s in enumerate(STEPS)])
legend = alt.Chart(leg).mark_rect(stroke="white", strokeWidth=2).encode(
    x=alt.X("Step:O", sort=STEPS, title="Share of canton's MW",
            axis=alt.Axis(orient="top", labelAngle=0, labelFontSize=11, titleFontSize=11,
                          titleColor=GREY, ticks=False, domain=False)),
    y=alt.Y("Tech:O", sort=list(SHADES), title=None,
            axis=alt.Axis(labelFontSize=11, labelFontWeight="bold", ticks=False, domain=False)),
    color=alt.Color("Fill:N", scale=None)).properties(width=180, height=90)
part1 = alt.hconcat(dom_map, legend, spacing=30)

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
               axis=alt.Axis(format="d", values=[1970, 1980, 1990, 2000, 2010, 2020, 2025], grid=False,
                             labelFontSize=11, ticks=False, domainColor=LINE))
tech_scale = alt.Scale(domain=GROUPS, range=GROUP_COL)
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
mix_chart = (area + labels).properties(width=AREA_W, height=AREA_H)


# ------------------------------------------------------------------ TEXT
def text(t, size, color=INK, weight="normal", height=None):
    return alt.Chart(pd.DataFrame({"t": [t]})).mark_text(
        align="left", baseline="top", fontSize=size, color=color, fontWeight=weight).encode(
        x=alt.value(0), y=alt.value(0), text="t:N").properties(width=W - 44, height=height or size * 1.3)


title = text("Electricity in Switzerland: where it was built, what it makes", 22, weight="bold")
h1 = text("01   Which technology dominates each canton (% of installed MW, 2025)", 14, weight="bold")
h2 = text("02   How the national production mix changed (% of TWh per year, 1970–2025)", 14, weight="bold")
footer = text("Sources: BFE/Pronovo plant register (plants operating today; closed plants missing), "
              "BFE electricity statistics, swisstopo swissBOUNDARIES3D.  "
              "Fossil and waste not shown in 02.", 8.5, color=GREY)


# ------------------------------------------------------------------ CHECKS
print("Check 1: every canton has a shape:",
      set(NUM2ABBR) == {f["properties"]["KANTONSNUM"] for f in cantons["features"]})
print("Check 2: 26 cantons, each with a known top technology:",
      len(dom) == 26 and dom["Tech"].notna().all())
print("Check 3: shares per canton sum to 100%:", bool((share.sum(axis=1).round(6) == 1).all()))
print(dom.sort_values(["Tech", "Share"])[["Canton", "Tech", "Share", "Step"]]
      .round(0).to_string(index=False))


# ------------------------------------------------------------------ PAGE
def strip(c):
    c = c.copy()
    c.config = alt.Undefined
    return c


page = alt.vconcat(
    strip(title), strip(h1), part1, strip(h2), mix_chart, strip(footer), spacing=10
).resolve_scale(color="independent").configure(
    background="white", font="Helvetica", view={"stroke": None}).configure_axis(labelColor=INK)
page = page.properties(padding={"left": PAD, "right": PAD, "top": 22, "bottom": 14})

page.save(OUT / "infographic4.png", scale_factor=2)
page.save(OUT / "infographic4.pdf")
print("saved figures/infographic4.pdf and .png")
