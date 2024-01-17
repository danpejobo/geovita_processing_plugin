![Geovita Logo](icons/geovita.ico)

# Geovita Processing Provider

A QGIS plugin for different Geovita custom processing algorithms. This plugin is currently under development, so new features may be expected!

**New algorithms are added to this repo as they are developed, and new releases published!**

Status
=====

- Implemented [REMEDY GIS RiskTool](https://github.com/norwegian-geotechnical-institute/REMEDY_GIS_RiskTool) to run from QGIS processing
  - It is important to read the manual for this project. Especially if you want to perform `vulnerability analysis`. This will require you to edit the polygon layers containing the `building` features (see specifications section).

Tools
=====
- **REMEDY GIS RiskTool** - These algorithms create a log directory in this location `%user%/Downloads/REMEDY`. For the moment this is hardcoded.
  - `Begrens Skade - Excavation` The Begrens Skade - Excavation algorithm provides a comprehensive analysis of building settlements and risks associated with subsidence and inclination.
  - `Begrens Skade - ImpactMap` The BegrensSkade ImpactMap alorithm calculates both short-term and long-term settlements that occur due to the establishment of a construction pit.
  - `Begrens Skade - Tunnel` The BegrensSkade Tunnel alorithm provides a comprehensive analysis of building settlements and risks associated with subsidence and inclination due to tunnel excavation.

QGIS Plugin
===========

This provider functions as a QGIS plugin (for QGIS >= 3.4) and is available via the standard QGIS plugins repository, so you can install it directly from within QGIS itself.

The plugin adds a new group to the Processing Toolbox for "Geovita", containing sub-groups with tools and algorithms to perform different tasks.

If you enconter bugs of any sort, PLEASE consider reporting them through [the bugtracker at GitHub](https://github.com/danpejobo/geovita_processing_plugin/issues). Everyone benefits!

Specifications
==============

It is crucial to understand the limitations of the [REMEDY GIS RiskTool](https://github.com/norwegian-geotechnical-institute/REMEDY_GIS_RiskTool) calculation methods. I would highly suggest reading the paper and the manual within the REMEDY repository.

If you want to enable `vulnerability analysis` you will need some information on the buildings near the excavation/tunnel. You will need to add text fields to each feature in the building polygon layer for `Foundation`, `Structure` and `Condition`. See below for the allowed values! 
- Class A is the best and D the worst. 
- If i cell contains `-` it only means that this field only have 2 possible values.
- Copy/pasete the values so they match!

| Class | Foundation                                              | Structure                        | Condition              |
|-------|---------------------------------------------------------|----------------------------------|------------------------|
| A     | To bedrock                                              | Steel                            | Excellent              |
| A     | Peler                                                   | A - Stål                         | A - Meget god tilstand |
| A     | A - Til berg - Direktefundamentert, peler               | -                                | -                      |
| B     | Raft                                                    | Reinforced concrete              | Good                   |
| B     | Betong                                                  | B - Armert betong                | B - God tilstand       |
| B     | B - På løsmasser - Hel plate (betong, såle)             | -                                | -                      |
| C     | Strip                                                   | Mixed                            | -                      |
| C     | Grunnmur                                                | C - Tre eller varierende         | -                      |
| C     | C - På løsmasser - Stripefundament (heller)             | -                                | -                      |
| D     | Wooden piles                                            | Masonry                          | Medium                 |
| D     | Trepeler                                                | D - Murstein eller spesiell type | C - Brukbar tilstand   |
| D     | D - På løsmasser - Punkt- og trefundamenter (banketter) | -                                | -                      |