import arcpy as  ARCPY
import os as OS
import sys as SYS
import SSDataObject as SSDO
import SSUtilities as UTILS
import WeightsUtilities as WU

class Toolbox(object):
    def __init__(self):
        self.label = "Python Spatial Analysis Library (PySAL)"
        self.alias = "pysal"
        self.tools = []
