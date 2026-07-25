import os
import numpy as np
from osgeo import gdal
from qgis.core import QgsProject, QgsRasterLayer

layer_name = "hs_reference_1991_2020"

out_path = r"C:\Users\eliaf\OneDrive\Documenti\HEI\TB\QGIS\Geodati\neve\giorni_neve_annui_1991_2020.tif"

# Seuil de neige [m]
snow_threshold = 0.05

layers = QgsProject.instance().mapLayersByName(layer_name)
if not layers:
    raise Exception(f"Layer non trovato: {layer_name}")

layer = layers[0]
src = layer.source()

ds = gdal.Open(src)
if ds is None:
    raise Exception("Impossibile aprire il NetCDF con GDAL.")

cols = ds.RasterXSize
rows = ds.RasterYSize
band_count = ds.RasterCount

print("Numero bande:", band_count)
print("Dimensioni:", cols, rows)

# Grille finale : jours avec de la neige
snow_days = np.zeros((rows, cols), dtype=np.uint16)

# Utilisation de la médiane:
# day 0 = bande 1,2,3
# day 1 = bande 4,5,6
# donc la médiane = bande 2,5,8,11,...
median_bands = range(2, band_count + 1, 3)

for band_id in median_bands:
    band = ds.GetRasterBand(band_id)
    arr = band.ReadAsArray()

    nodata = band.GetNoDataValue()

    if nodata is not None:
        valid = arr != nodata
        snow = (arr > snow_threshold) & valid
    else:
        snow = arr > snow_threshold

    snow_days += snow.astype(np.uint16)

    print(f"Elaborata banda {band_id}")

# GeoTIFF final
driver = gdal.GetDriverByName("GTiff")
out_ds = driver.Create(
    out_path,
    cols,
    rows,
    1,
    gdal.GDT_UInt16,
    options=["COMPRESS=LZW", "TILED=YES"]
)

out_ds.SetGeoTransform(ds.GetGeoTransform())
out_ds.SetProjection(ds.GetProjection())

out_band = out_ds.GetRasterBand(1)
out_band.WriteArray(snow_days)
out_band.SetNoDataValue(0)
out_band.FlushCache()

out_ds = None
ds = None

# Importer dans QGIS
result = QgsRasterLayer(out_path, "Giorni_neve_annui_1991_2020")
QgsProject.instance().addMapLayer(result)

print("Finito.")
print("Raster creato:", out_path)