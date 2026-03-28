# 3.4 Data Sources and Acquisition Strategy

This section details the primary data sources and acquisition methods used for soil moisture modeling. The study integrates multiple data types to ensure high model accuracy. Sentinel-2 Level-2A products serve as the main source of remotely sensed data. This mission provides Bottom-of-Atmosphere reflectance values which eliminate the need for further atmospheric correction. Main-Knorn et al. (2017) confirmed that these products are suitable for vegetation monitoring due to their high spectral fidelity. The research utilized multiple spectral channels to capture crop health signals. These bands are essential for computing indices that track plant water status.

Satellite data acquisition was performed through the Google Earth Engine Python API. This cloud-based platform allows for efficient processing of large geospatial datasets. The study focused on the 2024 to 2025 maize growing season in Chinhoyi. Images with less than 20 percent cloud cover were selected to maintain data quality. This filtering process ensures that the spectral signals represent the actual conditions of the maize canopy. Programmatic retrieval facilitated the rapid extraction of pixel values for the selected sampling locations. An automated cloud masking technique was applied using the Scene Classification Layer. This step excludes pixels contaminated by atmospheric noise or shadow effects. Such quality control measures are necessary for reliable analysis.

Ground-truth data collection involved measuring volumetric water content in the field. A calibrated Time Domain Reflectometry probe was used for these measurements. This instrument provides accurate readings of moisture levels within the root zone of the crop. Field sampling occurred at a depth of 30 centimetres to capture the primary water uptake area for maize. Allen et al. (1998) suggested that this depth is critical for assessing irrigation requirements. Measurements were taken on dates that coincided with satellite overpasses to ensure temporal alignment. A total of 60 sampling points across the study area provided the necessary observations for model training.

## References

Allen, R.G. et al. (1998) 'Crop evapotranspiration: Guidelines for computing crop water requirements', *FAO Irrigation and Drainage Paper*, 56.

Main-Knorn, M. et al. (2017) 'Sen2Cor for Sentinel-2', *Proceedings of SPIE*, 10427.
