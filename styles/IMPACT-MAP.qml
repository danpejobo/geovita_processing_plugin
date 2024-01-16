<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" version="3.34.1-Prizren" maxScale="0" minScale="1e+08" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal mode="0" fetchMode="0" enabled="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <elevation zoffset="0" band="1" zscale="1" enabled="0" symbology="Line">
    <data-defined-properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </data-defined-properties>
    <profileLineSymbol>
      <symbol clip_to_extent="1" type="line" is_animated="0" alpha="1" frame_rate="10" name="" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer class="SimpleLine" locked="0" pass="0" enabled="1" id="{c4d4fbc6-9367-40cf-8a4a-4a8761ee08ce}">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="190,207,80,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.6" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </profileLineSymbol>
    <profileFillSymbol>
      <symbol clip_to_extent="1" type="fill" is_animated="0" alpha="1" frame_rate="10" name="" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer class="SimpleFill" locked="0" pass="0" enabled="1" id="{91d8d5ff-f1cb-42ed-b7af-50cbc6197d3f}">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="190,207,80,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="35,35,35,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="0.26" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="solid" type="QString" name="style"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </profileFillSymbol>
  </elevation>
  <customproperties>
    <Option type="Map">
      <Option value="false" type="bool" name="WMSBackgroundLayer"/>
      <Option value="false" type="bool" name="WMSPublishDataSourceUrl"/>
      <Option value="0" type="int" name="embeddedWidgets/count"/>
      <Option value="Value" type="QString" name="identify/format"/>
    </Option>
  </customproperties>
  <mapTip enabled="1"></mapTip>
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" type="QString" name="name"/>
      <Option name="properties"/>
      <Option value="collection" type="QString" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour" enabled="false"/>
    </provider>
    <rasterrenderer type="singlebandpseudocolor" nodataColor="" alphaBand="-1" band="1" classificationMax="0.4033085" classificationMin="0" opacity="0.7">
      <rasterTransparency>
        <singleValuePixelList>
          <pixelListEntry max="0.007" percentTransparent="100" min="0"/>
        </singleValuePixelList>
      </rasterTransparency>
      <minMaxOrigin>
        <limits>MinMax</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="DISCRETE" labelPrecision="2" minimumValue="0" classificationMode="1" clip="0" maximumValue="0.40330850000000001">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option value="166,252,124,255" type="QString" name="color1"/>
              <Option value="246,124,124,255" type="QString" name="color2"/>
              <Option value="ccw" type="QString" name="direction"/>
              <Option value="0" type="QString" name="discrete"/>
              <Option value="gradient" type="QString" name="rampType"/>
              <Option value="rgb" type="QString" name="spec"/>
              <Option value="0.0247949;166,252,124,255;rgb;ccw:0.0495898;193,252,124,255;rgb;ccw:0.0743847;220,252,124,255;rgb;ccw:0.0991797;247,252,124,255;rgb;ccw:0.123975;251,241,124,255;rgb;ccw:0.148769;251,229,124,255;rgb;ccw:0.173564;251,217,124,255;rgb;ccw:0.198359;250,200,124,255;rgb;ccw:0.223154;249,175,124,255;rgb;ccw:0.247949;247,149,124,255;rgb;ccw" type="QString" name="stops"/>
            </Option>
          </colorramp>
          <item value="0.01" color="#a6fc7c" alpha="255" label="&lt;= 0,01"/>
          <item value="0.02" color="#c1fc7c" alpha="255" label="0,01 - 0,02"/>
          <item value="0.03" color="#dcfc7c" alpha="255" label="0,02 - 0,03"/>
          <item value="0.04" color="#f7fc7c" alpha="255" label="0,03 - 0,04"/>
          <item value="0.05" color="#fbf17c" alpha="255" label="0,04 - 0,05"/>
          <item value="0.06" color="#fbe57c" alpha="255" label="0,05 - 0,06"/>
          <item value="0.07" color="#fbd97c" alpha="255" label="0,06 - 0,07"/>
          <item value="0.08" color="#fac87c" alpha="255" label="0,07 - 0,08"/>
          <item value="0.09" color="#f9af7c" alpha="255" label="0,08 - 0,09"/>
          <item value="0.1" color="#f7957c" alpha="255" label="0,09 - 0,10"/>
          <item value="inf" color="#f67c7c" alpha="255" label="> 0,10"/>
          <rampLegendSettings direction="0" minimumLabel="" orientation="2" prefix="" useContinuousLegend="1" maximumLabel="" suffix="">
            <numericFormat id="basic">
              <Option type="Map">
                <Option type="invalid" name="decimal_separator"/>
                <Option value="6" type="int" name="decimals"/>
                <Option value="0" type="int" name="rounding_type"/>
                <Option value="false" type="bool" name="show_plus"/>
                <Option value="true" type="bool" name="show_thousand_separator"/>
                <Option value="false" type="bool" name="show_trailing_zeros"/>
                <Option type="invalid" name="thousand_separator"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0" gamma="1"/>
    <huesaturation colorizeRed="255" colorizeOn="0" invertColors="0" grayscaleMode="0" saturation="0" colorizeBlue="128" colorizeGreen="128" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
