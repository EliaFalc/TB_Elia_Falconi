from osgeo import gdal
import numpy as np
from qgis.core import QgsProject, QgsRasterLayer

dem_name = "DHM25_Ticino"

out_non_alpino = r"C:\Users\eliaf\OneDrive\Documenti\HEI\TB\QGIS\Données\Critères\pot_altitudine_non_alpino.tif"
out_alpino = r"C:\Users\eliaf\OneDrive\Documenti\HEI\TB\QGIS\Données\Critères\pot_altitudine_alpino.tif"


# Tableau altitude-potentiel

alt = np.array([
    192, 250, 300, 400, 500, 600, 700, 800, 900, 1000,
    1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
    2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800,
    2900, 3000, 3100, 3200, 3286
], dtype=float)

non_alpino = np.array([
    0.2, 0.45, 0.6, 0.8, 0.92, 0.98, 0.995, 1, 1, 1,
    1, 0.99, 0.98, 0.9, 0.7, 0.3, 0.1, 0.02, 0.005,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
], dtype=float)

alpino = np.array([
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0.01, 0.03, 0.12, 0.35, 0.7, 0.9, 0.98, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 0.995, 0.99, 0.98,
    0.95, 0.9, 0.85
], dtype=float)


# Lire le fichier DEM depuis QGIS

layers = QgsProject.instance().mapLayersByName(dem_name)

if not layers:
    raise Exception(f"Layer DEM '{dem_name}' non trovato. Controlla il nome nel pannello layer.")

dem_layer = layers[0]
dem_path = dem_layer.source()

ds = gdal.Open(dem_path)
band = ds.GetRasterBand(1)
dem = band.ReadAsArray().astype(float)

nodata = band.GetNoDataValue()
if nodata is None:
    nodata = -9999

mask_nodata = dem == nodata


# Interpolation linéaire

pot_non_alpino = np.interp(
    dem,
    alt,
    non_alpino,
    left=non_alpino[0],
    right=non_alpino[-1]
)

pot_alpino = np.interp(
    dem,
    alt,
    alpino,
    left=alpino[0],
    right=alpino[-1]
)

# Conserve « NoData » là où le MNT indique « NoData »
pot_non_alpino[mask_nodata] = -9999
pot_alpino[mask_nodata] = -9999


# Écrit les fichiers de sortie raster

driver = gdal.GetDriverByName("GTiff")

def write_raster(output_path, array):
    out_ds = driver.Create(
        output_path,
        ds.RasterXSize,
        ds.RasterYSize,
        1,
        gdal.GDT_Float32
    )
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(array.astype(np.float32))
    out_band.SetNoDataValue(-9999)
    out_band.FlushCache()
    out_ds.FlushCache()
    out_ds = None

write_raster(out_non_alpino, pot_non_alpino)
write_raster(out_alpino, pot_alpino)


# Importez les résultats dans QGIS

QgsProject.instance().addMapLayer(QgsRasterLayer(out_non_alpino, "pot_altitudine_non_alpino"))
QgsProject.instance().addMapLayer(QgsRasterLayer(out_alpino, "pot_altitudine_alpino"))

print("Fatto: raster altitudine non alpino e alpino creati.")