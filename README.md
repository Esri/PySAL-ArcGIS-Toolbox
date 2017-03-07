# PySAL-ArcGIS-Toolbox
Infrastructure designed to enhance the usability of 
innovative spatial econometric methods within the
**Python Spatial Analysis Library (PySAL)**. 
The integration framework leverages the user interface 
and data management capabilities
provided in **ArcGIS** making analytical techniques
developed in **PySAL** more accessible to the general **GIS** User.

## Features

* Ordinary Least Squares
* LM Tests for Alternative Spatial Model Selection
* Spatial Error Model
* Spatial Lag Model
* Spatial Weights Utilities

## Instructions

-------------

### ArcGIS Pro with Conda (1.3+)
Conda makes the installation of additional Python Packages simple.  See
[The Python Package Manager](http://pro.arcgis.com/en/pro-app/arcpy/get-started/what-is-conda.htm)
for a detailed explanation.  For Pro 1.4 and beyond, Pro Users can install
**pysal** through the GUI in the *Python* tab in the *Project* options.  All
others must install **pysal** using the command-line: 
[Using ArcGIS .bat Files to Install Conda Packages](http://pro.arcgis.com/en/pro-app/arcpy/get-started/using-conda-with-arcgis-pro.htm).  `conda install pysal` is the only command required once you have initialized the *arcgispro-py3* environment.

-------------

### ArcGIS Pro (1.0 - 1.2) and ArcGIS Desktop 10.4.1+
#### Step 1: Add Full Python Installation (Pro Users Only)
The first several releases of ArcGIS Pro came with a stripped down version of
Python.  This made the footprint on disk small but denied the User the ability
to run Python Scripts from a terminal or IDE.  If you find yourself in this
group please [log-in and download full Python Distribution](http://links.esri.com/pro/download/current)

#### Step 2: Install pysal Using pip
**SciPy** is a required Python Package for **pysal**.  Users with
installations from this section (and the previous) already have **SciPy** in their Python Setup.
As such, the only additional package required is **pysal**.  You must use a
[pip](https://pip.pypa.io/en/stable/) command to install the software, but
first you need to identify the location the of the script.  For most ArcGIS
Desktop Users the **pip.exe** resides in the **C:\Python27\Desktop10.x/Scripts**
directory.  The corresponding directory for Pro Users is typically **C:\Python34\Desktop10.x\Scripts**.
Open a terminal and change into this directory and execute `pip
install pysal`.

-------------

### ArcGIS Desktop 10.1 - 10.4
#### Step 1: Basic ArcGIS - Python Setup
For the majority of Users,
the **ArcGIS Installation Process** will have already installed the 
correct version of **Python** and the supporting packages and therefore can skip to the next
Step.

For those that used the advanced installation option to allow you to install Python yourself it is
up to you to make sure the packages conform.  The easiest way to do this is to
just install the correct **Python Package Versions** related to your own **ArcGIS**
install:

|ArcGIS	|Python	|NumPy	|Matplotlib |
|:------|:------|:------|:-----------|
|10.1	  | 2.7.2 | 1.6.1	| 1.1.0 |
|10.2   | 2.7.3 | 1.6.1	| 1.1.1 |
|10.2.1 | 2.7.5 | 1.7.1 | 1.3.0 |
|10.3   | 2.7.5 | 1.7.1 | 1.3.0 | 
|10.3.1 | 2.7.8 | 1.7.1 | 1.3.0 |
|10.4   | 2.7.10| 1.9.2 | 1.4.3 |

Note that in  the **PyParsing Python Package** is no longer installed with this version of **Matplotlib 1.3.0**, however, it is required in order for **Matplotlib** to function
properly.  It is advised that you install **PyParsing 1.5.7** if you are managing your own **Python Installation**.   

#### Step 2: SciPy Setup
This project requires the **SciPy Python Package**, however, confusion/problems
may arise due to the emergence of the **SciPy Stack**.  The latter package
contains an all-in-one suite of packages to support analytics in **Python**, yet it
often includes a version of **NumPy** or **MatPlotLib** that does not conform with
the **ArcGIS** release.  It is advised that you install **SciPy** by itself and
avoid the **SciPy Stack** unless you are willing to fix any issues that may
arise.

We are not aware of any constraints concerning the version of **SciPy** and how it
relates to the **Python Packages** listed in **Step 1**.  We suggest that you
obtain version **0.13.0** from the **SourceForge Download Site**:

[Download SciPy](http://sourceforge.net/projects/scipy/files/scipy)

-------------

### Alternative PySAL Setup Using GitHub for Non-Conda Setups
   1. Clone the latest **PySAL** repository: [PySAL GitHub Site](https://github.com/pysal/pysal).  
       Please note the directory you cloned it to: E.g. **C:\Data\git**.
   1. Follow the directions in the **Adding a Git Project to your ArcGIS Installation Python Path**
      section below to place the path to the **PySAL** repository in your
      **Python Path** .

-------------

# PySAL-ArcGIS-Toolbox Setup Using GitHub
   1. Clone the latest **PySAL-ArcGIS-Toolbox** repository: 
       [PySAL-ArcGIS-Toolbox GitHub Site](https://github.com/Esri/PySAL-ArcGIS-Toolbox).  
   1. If you are only going to use the Toolbox and supporting scripts as
       **ArcGIS Script Tools** then you do not need to continue with the 
       steps below.  However, if you want to be able to call the functions
       provided by this project from within the **Python Window** or
       **Terminal** then you must
       add the **PySAL-ArcGIS-Toolbox\Scripts** directory to your **Python Path** 
       using the directions outlined in section
       **Adding a Git Project to your ArcGIS Installation Python Path**.  

# Adding a Git Project to your ArcGIS Installation Python Path
   1. Append the base **PySAL** directory (if you installed via git)
       and **PySAL-ArcGIS-Toolbox** directory
       to your Python Path.  ArcGIS Desktop Users must add the path to the 
       **desktop10.x.pth** file that the ArcGIS Installation Process created.
       The file is located in your **$PYTHONHOME\Lib\site-packages**
       directory (Most common location is
       **C:\Python27\Desktop10.x\Lib\site-packages**).  
       For ArcGIS Pro Users with versions 1.0 - 1.2 that have installed the full version of Python 
       will find the **ArcGISPro.pth** file in the 
       **C:\Python34\Lib\site-packages** directory.  All other Pro users will
       be using the **arcgispro-py3** Conda environment and will find the **ArcGISPro.pth**
       file in the
       **C:\$ARCHOME$\bin\Python\envs\arcgispro-py3\lib\site-packages**
       directory.

   1. Optionally, users may create their own personal **.pth** file(s) so
       that they do not mess with the original one that ArcGIS installs for
       them.  This is probably your safest bet and all you have to do is place
       it in the same installation directory described previously.  The prefix
       of the file does not matter, just make sure that the extension is
       **.pth**.
       
## Requirements

* ArcGIS 
* SciPy 
* PySAL

**(Please see Instructions)**

## Resources

* [Integrating Open-Source Statistical Packages with ArcGIS (UC2012)](http://video.esri.com/watch/1925/integrating-open_dash_source-statistical-packages-with-arcgis)
* [Spatial Statistics Resources Blog](http://blogs.esri.com/esri/arcgis/2010/07/13/spatial-statistics-resources/)


## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing
Copyright 2016 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [license.txt]( https://raw.github.com/Esri/PySAL-ArcGIS-Toolbox/master/license.txt) file.

[](Esri Tags: Python Spatial Analysis Library PySAL)
[](Esri Language: Python)
