Plugin Builder Results

Your plugin GeovitaProcessingPlugin was created in:
    C:/Development/geosuite_exporter\geovita_processing_plugin

Your QGIS plugin directory is located at:
    C:/Users/dpe/AppData/Roaming/QGIS/QGIS3/profiles/Daniel/python/plugins

What's Next:

  * Copy the entire directory containing your new plugin to the QGIS plugin
    directory

  * Run the tests (``make test``)

  * Test the plugin by enabling it in the QGIS plugin manager

  * Customize it by editing the implementation file: ``geovita_processing_plugin.py``

  * You can use the Makefile to compile your Ui and resource files when
    you make changes. This requires GNU make (gmake)

For more information, see the PyQGIS Developer Cookbook at:
http://www.qgis.org/pyqgis-cookbook/index.html

(C) 2011-2018 GeoApt LLC - geoapt.com

QGIS environment

@echo off
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
set savedpath=%PATH%
if not exist "%OSGEO4W_ROOT%\apps\qgis\bin\qgisgrass7.dll" (goto nograss) else (goto grass)
:grass
@echo off
call "%OSGEO4W_ROOT%\apps\grass\grass78\etc\env.bat"
set PATH=%savedpath%;%OSGEO4W_ROOT%\apps\grass\grass78\lib;%OSGEO4W_ROOT%\apps\grass\grass78\bin
goto AFTER
:nograss
@echo off
set PATH=%savedpath%;%OSGEO4W_ROOT%\apps\qgis\bin
goto AFTER
:AFTER
set git=C:\Program Files\Git\cmd
set editor=C:\Users\%USERNAME%\AppData\Local\atom\bin
set PATH=%PATH%;%git%;%editor%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis
set GDAL_FILENAME_IS_UTF8=YES
rem Set VSI cache to be used as buffer, see #6448
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis\python;%PYTHONPATH%
@echo on
@if [%1]==[] (echo run o-help for a list of available commands & cd /d "%~dp0" & cmd.exe /k) else (cmd /c "%*")
