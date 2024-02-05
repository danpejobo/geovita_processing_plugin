Status and Limitations
=====
- [REMEDY GIS RiskTool](https://github.com/norwegian-geotechnical-institute/REMEDY_GIS_RiskTool)
  - It is important to read the manual for this project. Especially if you want to perform `vulnerability analysis`. This will require you to edit the polygon layers containing the `building` features (see specifications section below).
  - Supported filetypes: `.shp` `.tif` `.tiff`
    - If you have an "in memory" layer or other fileformats you will need to save it to a `.shp` file. This is a restriction imposed by the underlaying submodule.
  - Projection of layers:
    - All layers `are reprojected on the fly` as they need the same projection

Tools
=====
- **REMEDY GIS RiskTool** - These algorithms create a log directory in this location `%user%/Downloads/REMEDY`. For the moment this is hardcoded.
  - `Begrens Skade - Excavation` The Begrens Skade - Excavation algorithm provides a comprehensive analysis of building settlements and risks associated with subsidence and inclination.
  - `Begrens Skade - ImpactMap` The BegrensSkade ImpactMap alorithm calculates both short-term and long-term settlements that occur due to the establishment of a construction pit (this alg. takes a bit of time to run, open the log and refresh it to see the logged progress).
  - `Begrens Skade - Tunnel` The BegrensSkade Tunnel alorithm provides a comprehensive analysis of building settlements and risks associated with subsidence and inclination due to tunnel excavation.

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
