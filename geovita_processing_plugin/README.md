Introduction
=====
Processing providers and algorithms overview

Status and Limitations
=====
- [REMEDY GIS RiskTool](https://github.com/norwegian-geotechnical-institute/REMEDY_GIS_RiskTool)
  - REMEDY_GIS_RiskTool is an open-source GIS-based tool using the GIBV method to quantify building damage risks from deep excavation, analyzing settlements due to wall deformation and groundwater drawdown, developed under the REMEDY/Begrens Skade 2 research project (2017–2022).
  
  - It is important to read the manual for this project. Especially if you want to perform `vulnerability analysis`. This will require you to edit the polygon layers containing the `building` features (see specifications section below).
  - Supported filetypes: `.shp` `.tif` `.tiff`
    - If you have an "in memory" layer or other fileformats you will need to save it to a `.shp` file. This is a restriction imposed by the underlaying submodule.
  - Projection of layers:
    - All layers `are reprojected on the fly` as they need the same projection

Tools
=====
- **REMEDY GIS RiskTool** - These algorithms create a log directory in this location `%user%/Downloads/REMEDY`. For the moment this is hardcoded.
  - `Begrens Skade - Excavation` Analyzes building settlement risks in soft clays caused by deep excavation wall deformation, using the GIBV method to calculate vertical greenfield settlements based on empirical data from retaining wall behavior (developed under the REMEDY/Begrens Skade 2 project).
  - `Begrens Skade - ImpactMap` Quantifies short- and long-term consolidation settlements from groundwater drawdown during construction pit establishment, employing the GIBV method and empirical datasets to model spatiotemporal risk distribution in soft clays (part of the NFR-funded REMEDY initiative).
  - `Begrens Skade - Tunnel` Evaluates subsidence and inclination risks in buildings adjacent to tunnel excavations, leveraging the GIBV framework to predict settlements induced by tunneling activities in soft clay environments (developed through the REMEDY/Begrens Skade 2 research collaboration).

Specifications
==============

It is crucial to understand the limitations of the [REMEDY GIS RiskTool](https://github.com/norwegian-geotechnical-institute/REMEDY_GIS_RiskTool) calculation methods. I would highly suggest reading the paper and the manual within the REMEDY repository.

If you want to enable `vulnerability analysis` you will need some information on the buildings near the excavation/tunnel. You will need to add text fields to each feature in the building polygon layer for `Foundation`, `Structure` and `Condition`. See below for the allowed values! 
- Class A is the best and D the worst. 
- If i cell contains `-` it only means that this field only have 2 possible values.
- Copy/paste the values so they match!

| Class | Foundation                                              | Structure                        | Condition              |
|-------|---------------------------------------------------------|----------------------------------|------------------------|
| A     | To bedrock                                              | Steel                            | Excellent              |
| A     | Peler                                                   | A - Stål                         | A - Meget god tilstand |
| A     | A - Til berg - Direktefundamentert, peler               | -                                | -                      |
| B     | Raft                                                    | Reinforced concrete              | Good                   |
| B     | Betong                                                  | B - Armert betong                | B - God tilstand       |
| B     | B - På løsmasser - Hel plate (betong, såle)             | -                                | -                      |
| C     | Strip                                                   | Mixed                            | Medium                 |
| C     | Grunnmur                                                | C - Tre eller varierende         | C - Brukbar tilstand   |
| C     | C - På løsmasser - Stripefundament (heller)             | -                                | -                      |
| D     | Wooden piles                                            | Masonry                          | Bad                    |
| D     | Trepeler                                                | D - Murstein eller spesiell type | D - Dårlig             |
| D     | D - På løsmasser - Punkt- og trefundamenter (banketter) | -                                | -                      |
