"""Infographic 2: where and when new electricity capacity was built in Switzerland (1900-2026).

One A4 landscape page, static. Small multiples: one canton map per period.
Colour = NEW capacity commissioned in that period (MW), not total operating capacity.

Run:  .venv/bin/python infographic2.py
Output: figures/infographic2.pdf and figures/infographic2.png
Reads only cleaned_data/.
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

PAGE_W, PAGE_H = 1123, 794           # A4 landscape at 96 dpi
PAD = 30
W = PAGE_W - 2 * PAD                 # content width
INK, GREY = "#222222", "#666666"

# ------------------------------------------------------------------ LOAD
plants = pd.read_csv(DATA / "Plants_cleaned.csv").rename(columns={"BeginningOfOperation": "Year"})
cantons = json.load(open(DATA / "swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson"))
plants["MW"] = plants["TotalPower"] / 1000           # register gives kW

NUM2ABBR = dict(enumerate("ZH BE LU UR SZ OW NW GL ZG FR SO BS BL SH AR AI SG GR AG TG TI VD VS NE GE JU".split(), start=1))
ABBR2NUM = {v: k for k, v in NUM2ABBR.items()}

PERIODS = [(1900, 1919), (1920, 1939), (1940, 1959), (1960, 1979),
           (1980, 1999), (2000, 2009), (2010, 2019), (2020, 2026)]
LABEL = {p: f"{p[0]}–{p[1]}" for p in PERIODS}


def period_of(year):
    for p in PERIODS:
        if p[0] <= year <= p[1]:
            return LABEL[p]
    return None


plants["Period"] = plants["Year"].map(period_of)
before_1900 = plants[plants["Period"].isna()]
p = plants.dropna(subset=["Period"])

GROUPS = ["Hydro", "Nuclear", "Solar", "Wind", "Other"]
GROUP_COL = ["#1f77b4", "#7f7f7f", "#e8b500", "#2ca02c", "#8c564b"]
p = p.assign(Group=p["SubCategory"].map({"Hydroelectric power": "Hydro", "Nuclear energy": "Nuclear",
                                         "Photovoltaic": "Solar", "Wind energy": "Wind"}).fillna("Other"))

# ------------------------------------------------------------------ NEW CAPACITY PER CANTON AND PERIOD
# A canton with no plant in a period is "no new plants" (missing), kept apart from small values.
new = p.groupby(["Period", "Canton"]).agg(MW=("MW", "sum"), Plants=("MW", "size")).reset_index()

BINS = ["No new plants", "under 10 MW", "10–100 MW", "100–500 MW", "500 MW or more"]
BIN_COL = ["#e9e9e9", "#fff1bf", "#fdbb6c", "#f17c25", "#b54708"]


def bin_of(mw):
    if pd.isna(mw):
        return BINS[0]
    if mw < 10:
        return BINS[1]
    if mw < 100:
        return BINS[2]
    if mw < 500:
        return BINS[3]
    return BINS[4]


wide = pd.DataFrame({"KANTONSNUM": list(NUM2ABBR)})
wide["Canton"] = wide["KANTONSNUM"].map(NUM2ABBR)
for i, per in enumerate(LABEL.values()):
    mw = wide["Canton"].map(new[new.Period == per].set_index("Canton")["MW"])
    wide[f"b{i}"] = mw.map(bin_of)
    wide[f"mw{i}"] = mw.fillna(0).round(0)

nat = p.groupby("Period").agg(MW=("MW", "sum"), Plants=("MW", "size")).reindex(LABEL.values())
top = new.loc[new.groupby("Period")["MW"].idxmax()].set_index("Period")

# ------------------------------------------------------------------ CHECKS
print("Check 1: canton sums equal national sums per period:",
      bool((new.groupby("Period")["MW"].sum().reindex(nat.index) - nat["MW"]).abs().max() < 1e-6))
print("Check 2: every canton has a shape:",
      set(NUM2ABBR) == {f["properties"]["KANTONSNUM"] for f in cantons["features"]})
print(f"Check 3: plants before 1900 left out: {len(before_1900)} ({before_1900.MW.sum():.0f} MW)")
print("Check 4: cantons per colour class and period")
print(pd.DataFrame({per: wide[f"b{i}"].value_counts() for i, per in enumerate(LABEL.values())})
      .reindex(BINS).fillna(0).astype(int).to_string())
print(nat.assign(Top=top["Canton"], TopMW=top["MW"].round(0)).round(0).to_string())

# ------------------------------------------------------------------ MAPS (space x time x capacity)
def centre(feature):
    geom = feature["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    ring = max((pl[0] for pl in polys), key=len)
    xs, ys = [pt[0] for pt in ring], [pt[1] for pt in ring]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, len(ring)


cent = pd.DataFrame([dict(zip(["lon", "lat", "n"], centre(f)), Canton=NUM2ABBR[f["properties"]["KANTONSNUM"]])
                     for f in cantons["features"]])
cent = cent.sort_values("n", ascending=False).drop_duplicates("Canton").set_index("Canton")

MAP_W, MAP_H = 248, 161
shapes = alt.Data(values=cantons["features"])
color_scale = alt.Scale(domain=BINS, range=BIN_COL)


def one_map(i, per):
    t = top.loc[per]
    sub = f"{nat.loc[per, 'MW']:,.0f} MW · {nat.loc[per, 'Plants']:,.0f} plants"
    geo = alt.Chart(shapes).mark_geoshape(stroke="#8a8a8a", strokeWidth=0.4).transform_lookup(
        lookup="properties.KANTONSNUM", from_=alt.LookupData(wide, "KANTONSNUM", [f"b{i}", f"mw{i}"])).encode(
        color=alt.Color(f"b{i}:N", scale=color_scale, legend=None))
    lab = pd.DataFrame([{"lon": cent.loc[t.Canton, "lon"], "lat": cent.loc[t.Canton, "lat"],
                         "t": f"{t.Canton} {t.MW:,.0f}"}])
    halo = alt.Chart(lab).mark_text(fontSize=10, fontWeight="bold", color="white", stroke="white",
                                    strokeWidth=3).encode(longitude="lon:Q", latitude="lat:Q", text="t:N")
    txt = alt.Chart(lab).mark_text(fontSize=10, fontWeight="bold", color=INK).encode(
        longitude="lon:Q", latitude="lat:Q", text="t:N")
    return (geo + halo + txt).project("mercator").properties(
        width=MAP_W, height=MAP_H,
        title=alt.TitleParams(per, subtitle=sub, anchor="start", fontSize=15, fontWeight="bold",
                              subtitleFontSize=10, subtitleColor=GREY, offset=4))


maps = [one_map(i, per) for i, per in enumerate(LABEL.values())]
map_grid = alt.vconcat(alt.hconcat(*maps[:4], spacing=10), alt.hconcat(*maps[4:], spacing=10), spacing=14)

# ------------------------------------------------------------------ LEGEND (colour classes)
leg = pd.DataFrame({"Bin": BINS, "x": [0, 120, 230, 330, 440]})
legend = alt.layer(
    alt.Chart(leg).mark_square(size=170, stroke="#8a8a8a", strokeWidth=0.4, opacity=1).encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, 1063])), y=alt.value(9),
        color=alt.Color("Bin:N", scale=color_scale, legend=None)),
    alt.Chart(leg).mark_text(align="left", dx=10, fontSize=11, color=INK).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1063])), y=alt.value(9), text="Bin:N"),
    alt.Chart(pd.DataFrame({"x": [580], "t": ["New capacity per canton  ·  label = canton with most new MW"]}))
    .mark_text(align="left", fontSize=11, color=GREY).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1063])), y=alt.value(9), text="t:N"),
).properties(width=W - 8, height=18)

# ------------------------------------------------------------------ NATIONAL BARS (time x capacity x technology)
by_group = p.groupby(["Period", "Group"], as_index=False)["MW"].sum()
order = list(LABEL.values())
x_enc = alt.X("Period:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=11, ticks=False))
bars = alt.Chart(by_group).mark_bar(size=62).encode(
    x=x_enc,
    y=alt.Y("MW:Q", axis=None),
    color=alt.Color("Group:N", sort=GROUPS, scale=alt.Scale(domain=GROUPS, range=GROUP_COL), title=None,
                    legend=alt.Legend(orient="right", labelFontSize=11, symbolType="square", symbolSize=150)),
    order=alt.Order("order:Q")).transform_calculate(
    order="indexof(" + json.dumps(GROUPS) + ", datum.Group)")
totals = alt.Chart(nat.reset_index()).mark_text(dy=-6, baseline="bottom", fontSize=10, fontWeight="bold",
                                                color=INK).encode(x=x_enc, y="MW:Q",
                                                                  text=alt.Text("MW:Q", format=",.0f"))
notes = pd.DataFrame({"Period": ["1960–1979", "2020–2026"],
                      "MW": [nat.loc["1960–1979", "MW"], nat.loc["2020–2026", "MW"]],
                      "t": ["dams + nuclear", "rooftop solar"]})
annot = alt.Chart(notes).mark_text(dy=-20, baseline="bottom", fontSize=10, fontStyle="italic",
                                   color=GREY).encode(x=x_enc, y="MW:Q", text="t:N")
national = (bars + totals + annot).properties(
    width=W - 117, height=120,
    title=alt.TitleParams("New MW per period, all of Switzerland", anchor="start", fontSize=13, fontWeight="bold"))

# ------------------------------------------------------------------ TEXT
def text_block(lines, chars, size=11, color=INK, weight="normal", width=W):
    wrapped = [w for ln in lines for w in (textwrap.wrap(ln, chars) or [""])]
    df = pd.DataFrame({"i": range(len(wrapped)), "t": wrapped})
    return alt.Chart(df).mark_text(align="left", baseline="top", fontSize=size, color=color, fontWeight=weight).encode(
        x=alt.value(0), y=alt.Y("i:O", axis=None), text="t:N").properties(width=width, height=size * 1.4 * len(wrapped))


title = text_block(["The Geographical Development of Electricity Infrastructure in Switzerland (1900–2026)"],
                   120, size=22, weight="bold")
subtitle = text_block(["From a few large Alpine plants to hundreds of thousands of small plants in every canton"],
                      140, size=13, color=GREY)
footer = text_block([
    "New capacity = sum of installed capacity (MW) of plants commissioned in the period, by canton; not total operating capacity. "
    "The register lists only plants operating today, so closed plants are missing. Periods differ in length; 2026 is a part year. "
    f"{len(before_1900)} plants built before 1900 ({before_1900.MW.sum():.0f} MW) are not shown.",
    "Sources: BFE / Pronovo, Elektrizitaetsproduktionsanlagen (opendata.swiss); canton borders: swisstopo swissBOUNDARIES3D."],
    200, size=8.5, color=GREY)

# ------------------------------------------------------------------ PAGE
def strip(c):
    c = c.copy()
    c.config = alt.Undefined
    return c


page = alt.vconcat(strip(title), strip(subtitle), legend, map_grid, national, strip(footer), spacing=12).resolve_scale(
    color="independent").configure(background="white", font="Helvetica", view={"stroke": None}).configure_axis(
    labelColor=INK, titleColor=INK, domainColor="#999999")
page = page.properties(padding={"left": PAD, "right": PAD, "top": 24, "bottom": 20})

page.save(OUT / "infographic2.png", scale_factor=2)
page.save(OUT / "infographic2.pdf")
print("saved figures/infographic2.pdf and .png")
