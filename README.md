# Rhode Island Groundwater model determination

### Process

- Digitize RIWRCB / RIDC Groundwater Maps

- Watertable.gpkg
   - Fields:
     - serialnumber:
       typically upper figure (number)
       non-unique across maps
       unique within maps
     - watertable:
       typically middle figure (number)
       altitude of water level in feet
     - welldepth:
       typically lower figure(number)
       altitude of well or bedrock in feet (open or closed circle)
     - Bedrock:
       boolean
       well that penetrated bedrock or not
     - RockDepth:
       depth of rock (ledge) in feet below land surface
       on older maps
     - WaterDepth:
       depth of water (ledge) in feet below land surface
       on older maps
     - SurfaceWater:
       boolean
       is a surface water body

- Processing->Raster Analysis->Sample RasterValues:

    - Input Layer:  Watertable (EPSG:4326)
    - Raster Layer: RI_DEM_10m (EPGS:3438) 
    - Output Column Prefix: "topography"
    - Samples: [Create Temporary Layer]

- Export "Sampled" layer to Watertable2.gpkg
    - EPSG:3438

- Watertable2.gpkg:
   Fields:
   - See Watertable.gpkg
   - Topography
     Altitude in feet
     Value for surface water bodies may be different than topography

- Set the watertable value (from topography adn waterdepth)
  - if watertable is not currently set and
     - WaterDepth is set and
     - Topography is set
     -   watertable = topography - waterdepth

```
ogrinfo -sql 'update watertable
   set watertable = topography - WaterDepth
     where watertable is NULL
       and WaterDepth is NOT NULL
       and topography is NOT NULL` Watertable2.gpkg
```

- Interpolate surface
  - groundwater_model_new.py (requires raster.py)




