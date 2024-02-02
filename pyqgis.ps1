# Set OSGEO4W_ROOT variable
$env:OSGEO4W_ROOT = "C:\OSGeo4W"

# Call the o4w_env.bat script
& "$env:OSGEO4W_ROOT\bin\o4w_env.bat"

# Call the env.bat script for GRASS
& "$env:OSGEO4W_ROOT\apps\grass\grass78\etc\env.bat"

# Add directories to the system PATH
$env:PATH = $env:PATH + ";$env:OSGEO4W_ROOT\apps\qgis\bin"
$env:PATH = $env:PATH + ";$env:OSGEO4W_ROOT\apps\grass\grass78\lib"
$env:PATH = $env:PATH + ";$env:OSGEO4W_ROOT\apps\Qt5\bin"
$env:PATH = $env:PATH + ";$env:OSGEO4W_ROOT\apps\Python39\Scripts"

# Set PYTHONPATH
$env:PYTHONPATH = $env:PYTHONPATH + ";$env:OSGEO4W_ROOT\apps\qgis\python"

# Set PYTHONHOME
$env:PYTHONHOME = "$env:OSGEO4W_ROOT\apps\Python39"

# Add Git to the system PATH
$env:PATH = "C:\Program Files\Git\bin;" + $env:PATH

# Navigate to your project directory (replace with your actual project path)
Set-Location ""

# Start VS Code at this location
code .