"""
This script calls the Spatial Lag SAR functionality from the PySAL Module
within the ArcGIS environment.

Author(s): Mark Janikas, Xing Kang, Sergio Rey
"""

import arcpy as ARCPY
import numpy as NUM
import pysal as PYSAL
import os as OS
import sys as SYS
import SSDataObject as SSDO
import SSUtilities as UTILS
import pysal2ArcUtils as AUTILS

FIELDNAMES = ["Predy", "Resid", "Predy_e", "e_Pred"]

def setupParameters():

    #### Get User Provided Inputs ####
    inputFC = ARCPY.GetParameterAsText(0)
    depVarName = ARCPY.GetParameterAsText(1).upper()
    indVarNames = ARCPY.GetParameterAsText(2).upper()
    indVarNames = indVarNames.split(";")
    weightsFile = ARCPY.GetParameterAsText(3)
    outputFC = ARCPY.GetParameterAsText(4)

    #### Create SSDataObject ####
    fieldList = [depVarName] + indVarNames
    ssdo = SSDO.SSDataObject(inputFC, templateFC = outputFC)
    masterField = AUTILS.setUniqueIDField(ssdo, weightsFile)

    #### Populate SSDO with Data ####
    ssdo.obtainData(masterField, fieldList, minNumObs = 5) 

    #### Resolve Weights File ####
    patW = AUTILS.PAT_W(ssdo, weightsFile)

    #### Run SpLag ####
    splag = GMLag_PySAL(ssdo, depVarName, indVarNames, patW)

    #### Create Output ####
    splag.createOutput(outputFC)

class GMLag_PySAL(object):
    """Computes linear regression via Ordinary Least Squares using PySAL."""

    def __init__(self, ssdo, depVarName, indVarNames, patW, useHAC = True):

        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Initialize Data ####
        self.initialize()

        #### Calculate Statistic ####
        self.calculate()

    def initialize(self):
        """Performs additional validation and populates the SSDataObject."""

        ARCPY.SetProgressor("default", ("Starting to perform Spatial Lag "
                                        "regression. Loading features..."))
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo

        #### MasterField Can Not Be The Dependent Variable ####
        if ssdo.masterField == self.depVarName:
            ARCPY.AddIDMessage("ERROR", 945, ssdo.masterField, 
                               ARCPY.GetIDMessage(84112))
            raise SystemExit()

        #### Remove the MasterField from Independent Vars #### 
        if ssdo.masterField in self.indVarNames:
            self.indVarNames.remove(ssdo.masterField)
            ARCPY.AddIDMessage("Warning", 736, ssdo.masterField)

        #### Remove the Dependent Variable from Independent Vars ####
        if self.depVarName in self.indVarNames:
            self.indVarNames.remove(self.depVarName)
            ARCPY.AddIDMessage("Warning", 850, self.depVarName)

        #### Raise Error If No Independent Vars ####
        if not len(self.indVarNames):
            ARCPY.AddIDMessage("Error", 737)
            raise SystemExit()

        #### Create Dependent Variable ####
        self.allVars = [self.depVarName] + self.indVarNames
        self.y = ssdo.fields[self.depVarName].returnDouble()
        self.n = ssdo.numObs
        self.y.shape = (self.n, 1)

        #### Assure that Variance is Larger than Zero ####
        yVar = NUM.var(self.y)
        if NUM.isnan(yVar) or yVar <= 0.0:
            ARCPY.AddIDMessage("Error", 906)
            raise SystemExit()

        #### Create Design Matrix ####
        self.k = len(self.indVarNames) + 1
        self.x = NUM.ones((self.n, self.k - 1), dtype = float)
        for column, variable in enumerate(self.indVarNames):
            self.x[:,column] = ssdo.fields[variable].data

        #### Set Weights Info ####
        self.w = self.patW.w
        self.wName = self.patW.wName

    def calculate(self):
        """Performs GM Error Model and related diagnostics."""

        ARCPY.SetProgressor("default", "Executing Spatial Lag regression...")

        #### Perform GM_Lag regression ####
        self.lag = PYSAL.spreg.GM_Lag(self.y, self.x, w = self.w, 
                                      robust = 'white', spat_diag = True, 
                                      name_y = self.depVarName,
                                      name_x = self.indVarNames, 
                                      name_w = self.wName,
                                      name_ds = self.ssdo.inputFC)
        ARCPY.AddMessage(self.lag.summary)

    def createOutput(self, outputFC):

        #### Build fields for output table ####
        if self.lag.e_pred == None:
            ePredOut = NUM.ones(self.ssdo.numObs) * NUM.nan
        else:
            ePredOut = self.lag.e_pred

        self.templateDir = OS.path.dirname(SYS.argv[0])
        candidateFields = {}
        candidateFields[FIELDNAMES[0]] = SSDO.CandidateField(FIELDNAMES[0],
                                                             "Double", 
                                                             self.lag.predy)
        candidateFields[FIELDNAMES[1]] = SSDO.CandidateField(FIELDNAMES[1],
                                                             "Double", 
                                                             self.lag.u)
        candidateFields[FIELDNAMES[2]] = SSDO.CandidateField(FIELDNAMES[2],
                                                             "Double", 
                                                             self.lag.predy_e)
        candidateFields[FIELDNAMES[3]] = SSDO.CandidateField(FIELDNAMES[3],
                                                             "Double", 
                                                             ePredOut)
        self.ssdo.output2NewFC(outputFC, candidateFields, 
                               appendFields = self.allVars)

        #### Set the Default Symbology ####
        params = ARCPY.gp.GetParameterInfo() 
        try:
            renderType = UTILS.renderType[self.ssdo.shapeType.upper()]
            if renderType == 0:
                renderLayerFile = "ResidPoints.lyr"
            elif renderType == 1:
                renderLayerFile = "ResidPolylines.lyr"
            else:
                renderLayerFile = "ResidPolygons.lyr"
            fullRLF = OS.path.join(self.templateDir, "Layers", renderLayerFile)
            params[4].Symbology = fullRLF
        except:
            ARCPY.AddIDMessage("WARNING", 973)

if __name__ == '__main__':
    setupParameters()

