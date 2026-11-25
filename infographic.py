"""B.2 Information graphic (one A4 page, portrait, static).

Run:  .venv/bin/python infographic.py
Output: figures/B2_infographic.pdf and figures/B2_infographic.png
Reads only cleaned_data/. Does not change exploration.py.
"""
import json
import textwrap
from pathlib import Path

import altair as alt
import pandas as pd

BASE = Path(__file__).parent
DATA = BASE / "cleaned_data"
OUT = BASE / "figures"
OUT.mkdir(exist_ok=True)
alt.data_transformers.disable_max_rows()

PAGE_W, PAGE_H = 794, 1123          # A4 portrait at 96 dpi
W = 685                              # content width
INK, GREY = "#222222", "#666666"
CAP_COL, PROD_COL = "#d62728", "#1f77b4"

# ------------------------------------------------------------------ LOAD
plants = pd.read_csv(DATA / "Plants_cleaned.csv").rename(columns={"BeginningOfOperation": "Year"})
stats = pd.read_csv(DATA / "Electricity_statistics.csv")
cantons = json.load(open(DATA / "swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson"))
plants["Power_MW"] = plants["TotalPower"] / 1000


def technology(row):
    sub, plant = row["SubCategory"], row["PlantCategory"]
    if sub == "Hydroelectric power":
        return "Hydro storage" if plant in ("Storage power plant", "Pumped storage power plant") else "Hydro run-of-river"
    return {"Nuclear energy": "Nuclear", "Photovoltaic": "Photovoltaic",
            "Wind energy": "Wind", "Biomass": "Biomass"}.get(sub)


plants["Technology"] = plants.apply(technology, axis=1)
tp = plants.dropna(subset=["Technology"])

TECH = ["Photovoltaic", "Nuclear", "Hydro run-of-river", "Hydro storage", "Wind", "Biomass"]
TECH_COL = {"Hydro run-of-river": "#1f77b4", "Hydro storage": "#17becf", "Nuclear": "#7f7f7f",
            "Photovoltaic": "#ff7f0e", "Wind": "#2ca02c", "Biomass": "#8c564b"}
PROD_COLS = {"Hydro run-of-river": ["Production_run_of_river_GWh"], "Hydro storage": ["Production_storage_GWh"],
             "Nuclear": ["Production_nuclear_GWh"], "Photovoltaic": ["Production_photovoltaics_GWh"],
             "Wind": ["Production_wind_GWh"], "Biomass": ["Production_wood_GWh", "Production_biogas_GWh"]}

# ------------------------------------------------------------------ SHARES (time, technology, capacity, production)
LAST = int(stats.Year.max())
prod = pd.DataFrame({"Year": stats.Year})
for t, cols in PROD_COLS.items():
    prod[t] = stats[cols].sum(axis=1, min_count=1)
prod = prod.melt("Year", var_name="Technology", value_name="GWh").fillna({"GWh": 0})
START = 1970   # the statistics file has no production values before 1970 (empty, not zero)
prod = prod[prod.Year >= START]

grid = pd.MultiIndex.from_product([range(1960, LAST + 1), TECH], names=["Year", "Technology"])
added = tp.groupby(["Year", "Technology"])["Power_MW"].sum()
before = added[added.index.get_level_values("Year") < 1960].groupby("Technology").sum()
cap = added.reindex(grid, fill_value=0).reset_index()
cap["Installed_MW"] = cap.groupby("Technology")["Power_MW"].cumsum() + cap["Technology"].map(before).fillna(0)

d = cap.merge(prod, on=["Year", "Technology"])
d["Capacity"] = d["Installed_MW"] / d.groupby("Year")["Installed_MW"].transform("sum") * 100
d["Production"] = d["GWh"] / d.groupby("Year")["GWh"].transform("sum") * 100
d = d[d.Year >= START]
d_long = d.melt(["Year", "Technology"], ["Capacity", "Production"], var_name="Measure", value_name="Share")

now = d[d.Year == LAST].set_index("Technology")
pv_c, pv_p = now.loc["Photovoltaic", ["Capacity", "Production"]]
nu_c, nu_p = now.loc["Nuclear", ["Capacity", "Production"]]
print(f"{LAST}: PV capacity {pv_c:.1f}% production {pv_p:.1f}% | nuclear capacity {nu_c:.1f}% production {nu_p:.1f}%")

# ------------------------------------------------------------------ TEXT BLOCKS
def text_block(lines, width_chars, size=11, color=INK, weight="normal", line_h=None, width=W):
    wrapped = []
    for ln in lines:
        wrapped += textwrap.wrap(ln, width_chars) or [""]
    lh = line_h or size * 1.45
    df = pd.DataFrame({"i": range(len(wrapped)), "t": wrapped})
    return alt.Chart(df).mark_text(align="left", baseline="top", fontSize=size, color=color,
                                   fontWeight=weight).encode(
        x=alt.value(0), y=alt.Y("i:O", axis=None), text="t:N").properties(width=width, height=lh * len(wrapped))


def block(lines, chars, **kw):
    c = text_block(lines, chars, **kw)
    return c


title = block([f"Solar: {pv_c:.0f}% of Swiss power capacity, {pv_p:.0f}% of electricity.",
               f"Nuclear: {nu_c:.0f}% of capacity, {nu_p:.0f}% of electricity ({LAST})"],
              60, size=18, weight="bold")
intro = block([
    "Capacity (MW) is how much power plants could deliver. Production (GWh) is what they delivered over a year. "
    "A technology can hold a big share of one and a small share of the other. "
    "Solar panels only work in daylight. Nuclear plants run almost all year. "
    "The gap between the two lines below is the effect, technology by technology, from 1970."],
    112, size=11, color=GREY)

# ------------------------------------------------------------------ PANELS: share of capacity vs share of production
x_enc = alt.X("Year:Q", title=None, scale=alt.Scale(domain=[START, LAST + 20], nice=False),
              axis=alt.Axis(format="d", values=[1970, 1990, 2010], labelFontSize=9, grid=False))
y_enc = alt.Y("Share:Q", title="Share of total (%)", scale=alt.Scale(domain=[0, 80]),
              axis=alt.Axis(values=[0, 20, 40, 60, 80], labelFontSize=9, titleFontSize=9))
meas = alt.Color("Measure:N", title=None, sort=["Capacity", "Production"],
                 scale=alt.Scale(domain=["Capacity", "Production"], range=[CAP_COL, PROD_COL]),
                 legend=alt.Legend(orient="bottom", direction="horizontal", labelFontSize=11, symbolType="stroke", symbolStrokeWidth=3,
                                   symbolSize=500, labelLimit=400, columnPadding=25,
                                   labelExpr="datum.label == 'Capacity' ? 'Share of installed capacity (dashed)' : 'Share of electricity produced (solid)'"))

base = alt.Chart(d_long)
gap = base.mark_area(color="#bbbbbb", opacity=0.45).transform_pivot(
    "Measure", value="Share", groupby=["Year", "Technology"]).encode(
    x=x_enc, y=alt.Y("Capacity:Q", scale=alt.Scale(domain=[0, 80])), y2="Production:Q")
lines = base.mark_line(strokeWidth=2).encode(
    x=x_enc, y=y_enc, color=meas,
    strokeDash=alt.StrokeDash("Measure:N", legend=None, sort=["Capacity", "Production"],
                              scale=alt.Scale(domain=["Capacity", "Production"], range=[[5, 3], [1, 0]])))
ends_base = base.transform_filter(alt.datum.Year == LAST).transform_pivot(
    "Measure", value="Share", groupby=["Year", "Technology"]).transform_calculate(
    yc="datum.Capacity + (datum.Capacity >= datum.Production ? 1 : -1) * 4",
    yp="datum.Production + (datum.Capacity >= datum.Production ? -1 : 1) * 4")
ends = alt.layer(
    ends_base.mark_text(align="left", dx=4, fontSize=10, fontWeight="bold", color=CAP_COL).encode(
        x=x_enc, y=alt.Y("yc:Q", scale=alt.Scale(domain=[0, 80])), text=alt.Text("Capacity:Q", format=".0f")),
    ends_base.mark_text(align="left", dx=4, fontSize=10, fontWeight="bold", color=PROD_COL).encode(
        x=x_enc, y=alt.Y("yp:Q", scale=alt.Scale(domain=[0, 80])), text=alt.Text("Production:Q", format=".0f")))
panels = alt.layer(gap, lines, ends).properties(width=207, height=118).facet(
    facet=alt.Facet("Technology:N", sort=TECH, title=None,
                    header=alt.Header(labelFontSize=12, labelFontWeight="bold", labelPadding=2)),
    columns=3).properties(spacing=6)
panels_title = block(["1  Time, technology, capacity and production: the gap is big for solar and nuclear"],
                     88, size=12, weight="bold")

# ------------------------------------------------------------------ MAP: where the solar capacity is (space)
NUM2ABBR = dict(enumerate("ZH BE LU UR SZ OW NW GL ZG FR SO BS BL SH AR AI SG GR AG TG TI VD VS NE GE JU".split(), start=1))
pv = tp[(tp.Technology == "Photovoltaic") & (tp.Year <= LAST)].groupby("Canton", as_index=False)["Power_MW"].sum()
pv["Share"] = pv["Power_MW"] / pv["Power_MW"].sum() * 100
pv["KANTONSNUM"] = pv["Canton"].map({v: k for k, v in NUM2ABBR.items()})


def centre(feature):
    geom = feature["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    ring = max((p[0] for p in polys), key=len)
    xs = [pt[0] for pt in ring]
    ys = [pt[1] for pt in ring]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def ring_len(f):
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return max(len(p[0]) for p in polys)


cent = pd.DataFrame([{"Canton": NUM2ABBR[f["properties"]["KANTONSNUM"]], "lon": centre(f)[0], "lat": centre(f)[1],
                      "n": ring_len(f)} for f in cantons["features"]])
cent = cent.sort_values("n", ascending=False).drop_duplicates("Canton").drop(columns="n").merge(pv, on="Canton")
top = cent.nlargest(6, "Share")
top["Label"] = top["Canton"] + " " + top["Share"].round(0).astype(int).astype(str) + "%"

MAP_W, MAP_H = 320, 270
shape = alt.Chart(alt.Data(values=cantons["features"])).mark_geoshape(stroke="white", strokeWidth=0.8).transform_lookup(
    lookup="properties.KANTONSNUM", from_=alt.LookupData(pv, "KANTONSNUM", ["Share"])).encode(
    color=alt.Color("Share:Q", title="Share of Swiss solar capacity (%)",
                    scale=alt.Scale(scheme="oranges", domain=[0, float(pv.Share.max())]),
                    legend=alt.Legend(orient="bottom", direction="horizontal", titleFontSize=10, labelFontSize=9,
                                      gradientLength=170, format=".0f")))
labels = alt.layer(
    alt.Chart(top).mark_text(fontSize=10, fontWeight="bold", color="white", stroke="white", strokeWidth=3).encode(
        longitude="lon:Q", latitude="lat:Q", text="Label:N"),
    alt.Chart(top).mark_text(fontSize=10, fontWeight="bold", color="black").encode(
        longitude="lon:Q", latitude="lat:Q", text="Label:N"))
map_chart = (shape + labels).project("mercator").properties(width=MAP_W, height=MAP_H)
map_title = block(["2  Space: where the solar capacity stands"], 42, size=12, weight="bold", width=MAP_W)

# ------------------------------------------------------------------ BARS: full-load hours (why the gap exists)
hrs = []
for t in TECH:
    r = d[(d.Year == LAST) & (d.Technology == t)].iloc[0]
    hrs.append({"Technology": t, "Hours": r["GWh"] / r["Installed_MW"] * 1000})
hrs = pd.DataFrame(hrs)
print(hrs.round(0).to_string(index=False))
order = hrs.sort_values("Hours", ascending=False)["Technology"].tolist()
BAR_W = 215
bars = alt.Chart(hrs).mark_bar().encode(
    y=alt.Y("Technology:N", sort=order, title=None, axis=alt.Axis(labelFontSize=10, ticks=False, domain=False)),
    x=alt.X("Hours:Q", title=None, scale=alt.Scale(domain=[0, 9500]), axis=alt.Axis(values=[0, 2000, 4000, 6000, 8000], labelFontSize=9, grid=False)),
    color=alt.Color("Technology:N", legend=None, scale=alt.Scale(domain=TECH, range=[TECH_COL[t] for t in TECH])))
bar_txt = alt.Chart(hrs).mark_text(align="left", dx=3, fontSize=10, fontWeight="bold").encode(
    y=alt.Y("Technology:N", sort=order), x="Hours:Q", text=alt.Text("Hours:Q", format=",.0f"))
year_rule = alt.Chart(pd.DataFrame({"x": [8760], "t": ["8,760 h = a full year"]})).mark_rule(strokeDash=[4, 3], color=GREY).encode(x="x:Q")
year_txt = alt.Chart(pd.DataFrame({"x": [8760], "t": ["full year"]})).mark_text(
    align="right", dx=-3, dy=-4, baseline="bottom", fontSize=9, color=GREY).encode(x="x:Q", y=alt.value(0), text="t:N")
bars_chart = (bars + bar_txt + year_rule + year_txt).properties(width=BAR_W, height=MAP_H - 40)
bar_title = block([f"3  Why: hours at full power per year ({LAST})"], 30, size=12, weight="bold", width=BAR_W)

# ------------------------------------------------------------------ NOTES
notes = block([
    f"How to read: a share is one technology's part of the total of six technologies (photovoltaic, nuclear, hydro run-of-river, hydro storage, wind, biomass), in each year. "
    f"Capacity = running total of plants by year of commissioning. Production = yearly GWh. Hours at full power = GWh / MW x 1000.",
    "Limits: the plant register holds only plants that exist today, so capacity in earlier years is too low. "
    "Hydro storage includes pumped storage. Biomass is wood plus biogas. Waste and fossil plants (217) are left out. "
    "The map shows capacity only: Switzerland publishes production only for the whole country.",
    "Sources: BFE / Pronovo, Elektrizitaetsproduktionsanlagen (register of plants), opendata.swiss. "
    "BFE Elektrizitaetsbilanz der Schweiz, Jahreswerte (OGD32), annual values 1970 to 2025. "
    "Canton borders: swisstopo swissBOUNDARIES3D. All data are open government data."],
    132, size=9, color=GREY)

# ------------------------------------------------------------------ PAGE
def v(*items, spacing=6):
    return alt.vconcat(*items, spacing=spacing).configure_view(stroke=None)


row = alt.hconcat(alt.vconcat(map_title, map_chart, spacing=4), alt.vconcat(bar_title, bars_chart, spacing=4), spacing=30)
# configure_view per sub-chart is not allowed inside concat, so strip configs from the text blocks
def strip(c):
    c = c.copy()
    c.config = alt.Undefined
    return c


page = alt.vconcat(strip(title), strip(intro), strip(panels_title), panels, row, strip(notes), spacing=20).configure(
    background="white", font="Helvetica", view={"stroke": None}).configure_axis(labelColor=INK, titleColor=INK)
page = page.properties(padding={"left": 38, "right": 38, "top": 34, "bottom": 37})

page.save(OUT / "B2_infographic.png", scale_factor=2)
page.save(OUT / "B2_infographic.pdf")
print("saved figures/B2_infographic.pdf and .png")
