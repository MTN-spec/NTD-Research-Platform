# 3.1 Introduction

This chapter describes the methods used to build a soil moisture prediction system for maize farmers in Chinhoyi. The study area represents an important agricultural zone in Zimbabwe where rainfall patterns have become increasingly variable. Recent research by Mugandani et al. (2021) shows that these changes affect crop yields significantly. To address this problem, the research integrates satellite data with ground measurements using machine learning.

The methodology follows a quantitative approach to test the relationship between spectral signals and water content. Sentinel-2 imagery provides the primary data source for monitoring vegetation health. This satellite platform offers high spatial resolution which is suitable for small-scale farming. Ground data collection involved taking volumetric water content readings using a calibrated probe. These measurements occurred on dates that aligned with the satellite overpasses. This temporal synchronization ensures that the spectral index values match the actual moisture levels at the time of sensing.

Machine learning models process the combined dataset to estimate moisture levels. The study evaluates the Random Forest algorithm to determine its predictive power. It also uses Support Vector Regression as a comparative framework. Each model underwent training and validation using a split-dataset technique. This comparison helps in determining which method better handles the non-linear links between reflectance and soil water. Gwitira et al. (2022) suggested that ensemble methods often outperform single-kernel approaches in complex terrains.

The final stage of the methodology involves the deployment of an automated alert system. This system uses a Flask web application to display real-time predictions on an interactive map. It triggers email notifications when moisture falls below specific agronomic thresholds. The architecture ensures that farmers receives timely information for irrigation scheduling. Such digital tools support sustainable water management in regions prone to drought. Sibanda et al. (2021) highlighted the need for localized monitoring systems to improve food security in Zimbabwe. The following sections provide detailed descriptions of the study site and the technical implementation steps.

## References

Gwitira, I. et al. (2022) 'Estimating Soil Moisture Using Remote Sensing in Zimbabwe: A Review', in *Spatial Information Management for Sustainable Development*. Springer.

Mugandani, R. et al. (2021) 'Impacts of climate change on hydrological droughts in Zimbabwe', *Journal of Water and Climate Change*, 12(7), pp. 3034–3051.

Sibanda, M. et al. (2021) 'Remote Sensing Drought Indices and their Application in Mapping Spatial and Temporal Variations of Drought in Zimbabwe', *Journal of Spatial Science*, 66(1), pp. 123–141.
