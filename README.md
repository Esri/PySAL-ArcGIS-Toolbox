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

### Step 1: Basic ArcGIS - Python Setup
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
|10.1	|2.7.2	|1.6.1	|1.1.0 |
|10.2	|2.7.3	|1.6.1	|1.1.1 |
|10.2.1 |2.7.5  |1.7.1  |1.3.0 |

Note that in  the **PyParsing Python Package** is no longer installed with this version of **Matplotlib 1.3.0**, however, it is required in order for **Matplotlib** to function
properly.  It is advised that you install **PyParsing 1.5.7** if you are managing your own **Python Installation**.   

### Step 2: SciPy Setup
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

### Step 3: PySAL Setup

#### As a Python Package

#### From GitHub

   1. Clone the latest **PySAL** repository: [PySAL GitHub Site](https://github.com/pysal/pysal).  
       Please note the directory you cloned it to: E.g. **C:\Data\git**.
   1. Append the base **PySAL** directory (in above example: **C:\Data\git\pysal**) 
       to your Python Path using the
       **desktop10.x.pth** file that the ArcGIS Installation Process created.
       The file is located in your **$PYTHONHOME\Lib\site-packages**
       directory (Most common location is
       **C:\Python27\Desktop10.x\Lib\site-packages**).  

### Step 4: PySAL-ArcGIS-Toolbox Setup

   1. Clone the latest **PySAL-ArcGIS-Toolbox** repository: 
       [PySAL-ArcGIS-Toolbox GitHub Site](https://github.com/Esri/PySAL-ArcGIS-Toolbox).  
   1. If you are only going to use the Toolbox and supporting scripts as
       **ArcGIS Script Tools** then you do not need to continue with the 
       steps below.  However, if you want to be able to call the functions
       provided by this project from within the **Python Window** or
       **Terminal** then you must
       add the **PySAL-ArcGIS-Toolbox\Scripts** directory to your **Python Path** 
       the same way you did this for **PySAL** in **Step 3 (GitHub Version)**.  
   1. Append the base **PySAL-ArcGIS-Toolbox** directory
       (E.g. **C:\Data\git\PySAL-ArcGIS-Toolbox**) 
       to your **Python Path** using the
       **desktop10.x.pth** file that the **ArcGIS Installation Process** created.
       Again, the most common location is
       **C:\Python27\Desktop10.x\Lib\site-packages**).  
       
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
