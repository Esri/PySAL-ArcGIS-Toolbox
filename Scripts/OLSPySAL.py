"""
This script calls OLS functionality from the PySAL Module within the ArcGIS
environment.

Author(s): Mark Janikas, Xing Kang, Sergio Rey
"""

import arcpy as ARCPY
import numpy as NUM
import pysal as PYSAL
import SSDataObject as SSDO
import SSUtilities as UTILS
import os as OS
import sys as SYS
import pysal2ArcUtils as AUTILS

FIELDNAMES = ["Estimated", "Residual", "StdResid"]

def setupParameters():

    #### Get User Provided Inputs ####
    inputFC = ARCPY.GetParameterAsText(0)
    depVarName = ARCPY.GetParameterAsText(1).upper()  
    indVarNames = ARCPY.GetParameterAsText(2).upper()  
    indVarNames = indVarNames.split(";")
    outputFC = UTILS.getTextParameter(3)
    weightsFile = UTILS.getTextParameter(4)

    #### Create SSDataObject ####
    fieldList = [depVarName] + indVarNames
    ssdo = SSDO.SSDataObject(inputFC, templateFC = outputFC)
    masterField = UTILS.setUniqueIDField(ssdo, weightsFile = weightsFile)

    #### Populate SSDO with Data ####
    ssdo.obtainData(masterField, fieldList, minNumObs = 5) 

    #### Resolve Weights File ####
    if weightsFile:
        patW = AUTILS.PAT_W(ssdo, weightsFile)
    else:
        patW = None

    #### Run OLS ####
    ols = OLS_PySAL(ssdo, depVarName, indVarNames, patW = patW)

    #### Create Output ####
    ols.createOutput(outputFC)


class OLS_PySAL(object):
    """Computes linear regression via Ordinary Least Squares using PySAL."""

    def __init__(self, ssdo, depVarName, indVarNames, patW = None):

        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Initialize Data ####
        self.initialize()

        #### Calculate Statistic ####
        self.calculate()

    def initialize(self):
        """Performs additional validation and populates the 
        SSDataObject."""

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

        #### Resolve Weights ####
        if self.patW:
            self.w = self.patW.w
            self.wName = self.patW.wName
        else:
            self.w = None
            self.wName = None

    def calculate(self):
        """Performs OLS and related diagnostics."""

        ARCPY.SetProgressor("default", "Executing the OLS regression...")

        if self.patW:
            ols = PYSAL.spreg.OLS(self.y, self.x, w = self.w,
                                  spat_diag = True, robust = 'white', 
                                  name_y = self.depVarName,
                                  name_x = self.indVarNames, 
                                  name_ds = self.ssdo.inputFC,
                                  name_w = self.wName)
        else:
            ols = PYSAL.spreg.OLS(self.y, self.x, robust = 'white', 
                                  name_y = self.depVarName, 
                                  name_x = self.indVarNames, 
                                  name_ds = self.ssdo.inputFC)

        self.ols = ols
        self.dof = self.ssdo.numObs - self.k - 1
        sdCoeff = NUM.sqrt(1.0 * self.dof / self.n)
        self.resData = sdCoeff * ols.u / NUM.std(ols.u)
        ARCPY.AddMessage(ols.summary)

    def createOutput(self, outputFC):

        self.templateDir = OS.path.dirname(SYS.argv[0])
        candidateFields = {}
        candidateFields[FIELDNAMES[0]] = SSDO.CandidateField(FIELDNAMES[0],
                                                             "Double",
                                                             self.ols.predy)
        candidateFields[FIELDNAMES[1]] = SSDO.CandidateField(FIELDNAMES[1], 
                                                             "Double",
                                                             self.ols.u)
        candidateFields[FIELDNAMES[2]] = SSDO.CandidateField(FIELDNAMES[2],
                                                             "Double", 
                                                             self.resData)

        self.ssdo.output2NewFC(outputFC, candidateFields, appendFields = self.allVars)

        #### Set the Default Symbology ####
        params = ARCPY.gp.GetParameterInfo()
        try:
            renderType = UTILS.renderType[self.ssdo.shapeType.upper()]
            if renderType == 0:
                renderLayerFile = "StdResidPoints.lyr"
            elif renderType == 1:
                renderLayerFile = "StdResidPolylines.lyr"
            else:
                renderLayerFile = "StdResidPolygons.lyr"
            fullRLF = OS.path.join(self.templateDir, "Layers", renderLayerFile)
            params[3].Symbology = fullRLF
        except:
            ARCPY.AddIDMessage("WARNING", 973)

if __name__ == '__main__':
    setupParameters()
