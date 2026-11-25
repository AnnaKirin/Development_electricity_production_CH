import pandas as pd

el_production_plant_df = pd.read_csv(
    "data/ElectricityProductionPlant.csv",
    delimiter=",",
)
Plant_df = pd.read_csv(
    "data/PlantCategoryCatalogue.csv",
    delimiter=",",
)
maincategory_df = pd.read_csv(
    "data/MainCategoryCatalogue.csv",
    delimiter=",",
)
subcategory_df = pd.read_csv(
    "data/SubCategoryCatalogue.csv",
    delimiter=",",
)

mapping_maincat = dict(zip(maincategory_df["Catalogue_id"], maincategory_df["en"]))
el_production_plant_df["MainCategory"] = el_production_plant_df["MainCategory"].map(mapping_maincat)

mapping_subcat = dict(zip(subcategory_df["Catalogue_id"], subcategory_df["en"]))
el_production_plant_df["SubCategory"] = el_production_plant_df["SubCategory"].map(mapping_subcat)

mapping_plant = dict(zip(Plant_df["Catalogue_id"], Plant_df["en"]))
el_production_plant_df["PlantCategory"] = el_production_plant_df["PlantCategory"].map(mapping_plant)

el_production_plant_df["BeginningOfOperation"] = pd.to_datetime(el_production_plant_df["BeginningOfOperation"], errors="coerce").dt.year


#print(el_production_plant_df[["MainCategory", "SubCategory", "PlantCategory"]])
el_production_plant_df = el_production_plant_df.drop(columns=["Address","EGID","InitialPower"])

el_production_plant_df.to_csv("el_production_plant.csv", index=False)

#Plant_df = Plant_df.drop(columns=Plant_df.columns[[1, 2, 3]])
#maincategory_df = maincategory_df.drop(columns=maincategory_df.columns[[1, 2, 3]])
#subcategory_df = subcategory_df.drop(columns=subcategory_df.columns[[1, 2, 3]])
#pd.set_option("display.max_columns", None)
#pd.set_option("display.width", None)
#print(Plant_df,maincategory_df, subcategory_df)


df_2010 = el_production_plant_df[el_production_plant_df["BeginningOfOperation"] >= 2010]
df_2010.to_csv("production_data_from_2010.csv", index=False)

df_2020 = el_production_plant_df[el_production_plant_df["BeginningOfOperation"] >= 2020]
df_2020.to_csv("production_data_from_2020.csv", index=False)