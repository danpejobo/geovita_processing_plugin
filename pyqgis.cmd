@echo off
    SET OSGEO4W_ROOT=C:\OSGeo4W
    call "%OSGEO4W_ROOT%"\bin\o4w_env.bat
    call "%OSGEO4W_ROOT%"\apps\grass\grass78\etc\env.bat
@echo off
    path %PATH%;%OSGEO4W_ROOT%\apps\qgis\bin
    path %PATH%;%OSGEO4W_ROOT%\apps\grass\grass78\lib
    path %PATH%;%OSGEO4W_ROOT%\apps\Qt5\bin
    path %PATH%;%OSGEO4W_ROOT%\apps\Python36\Scripts

    set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python
    set PYTHONHOME=%OSGEO4W_ROOT%\apps\Python39

    set PATH=C:\Program Files\Git\bin;%PATH%

    start code .