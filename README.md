![Geovita Logo](geovita_processing_plugin/icons/geovita.ico)

Geovita Processing Provider
===========================

The Geovita processing provider for QGIS!

**New algorithms are added to the provider as they are developed**

QGIS Plugin
===========

This provider functions as a QGIS plugin (for QGIS >= 3.28) and is available via the standard QGIS plugins repository, so you can install it directly from within QGIS itself.

The plugin adds a new group to the Processing Toolbox for "Geovita", containing sub-groups with tools and algorithms to perform different tasks.

If you enconter bugs of any sort, PLEASE consider reporting them through [the bugtracker at GitHub](https://github.com/danpejobo/geovita_processing_plugin/issues). Everyone benefits!

Check it out [here!](/geovita_processing_plugin/)

Overview
========
- Implemented [REMEDY GIS RiskTool](https://github.com/norwegian-geotechnical-institute/REMEDY_GIS_RiskTool) to run from QGIS processing

## Example results from the REMEDY GIS RiskTool
The following images show some example results. Both the excavation and the tunnel algorithm produces results for short and/or longterm settlements, but uses different calculation methods. The impact map calculates and illustrate total settlements in the impaced soil around the excavation.

| Loaded Layers | Short term | Long term | Impact map |
|---------------|------------|-----------|------------|
| ![Loaded layers](resources/example-short-term-layers.png) <br><br> The symbology of the loaded layers | ![Short term](resources/example-short-term.png) <br><br> Blue hatch is the excavation. Status of corners, walls and buildings | ![Long term](resources/example-long-short-term.png) <br><br> Blue hatch is the excavation. Dark background is the depth to bedrock raster used for long term settlements. | ![Impact map](resources/example-impact-map.png) <br><br> Red hatch is the excavation. The impact map for total settlements around the excavation. |
