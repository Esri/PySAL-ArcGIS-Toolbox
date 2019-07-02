"""
This script calls the Spatial Error SAR functionality from the PySAL Module
within the ArcGIS environment.

Author(s): Mark Janikas, Xing Kang, Sergio Rey, Hu SHao
"""

import arcpy as ARCPY
import numpy as NUM
import pysal as PYSAL
import os as OS
import SSDataObject as SSDO
import SSUtilities as UTILS
import sys as SYS
import pysal2ArcUtils as AUTILS

FIELDNAMES = ["Predy", "Resid"]
FIELDALIAS = ["Predicted {0}", "Residual"]
HET_FIELDNAMES = ["HetPredy", "HetResid", "FiltResid"]
HET_FIELDALIAS = ["Predicted {0} (Het Adjusted)", "Residual (Het Adjusted)", 
                  "Residual (Spatially Filtered)"]
MODELTYPES = ["GMM", "GMM_HAC", "ML"]

class Error_PySAL(object):
    """Computes linear regression via Ordinary Least Squares using PySAL."""

    def __init__(self, ssdo, depVarName, indVarNames, patW, modelType = "GMM"):

        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Validate Model Type ####
        if modelType not in MODELTYPES:
            ARCPY.AddError("The input model type {0} is not in {1}".format(modelType, 
                                                                           ", ".join(MODELTYPES)))
            raise SystemExit()

        #### Initialize Data ####
        self.initialize()

        #### Calculate Statistic ####
        self.calculate()

    def initialize(self):
        """Performs additional validation and populates the SSDataObject."""
        
        ARCPY.SetProgressor("default", ("Starting to perform Spatial Error "
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

        ARCPY.SetProgressor("default", "Executing Spatial Error regression...")

        #### Perform GM_Error/GMError_Het regression ####
        if self.modelType == "ML":
            error = PYSAL.model.spreg.ML_Error(self.y, self.x, w = self.w,
                                               name_y = self.depVarName,
                                               name_x = self.indVarNames,
                                               name_w = self.wName,
                                               name_ds = self.ssdo.inputFC)

        elif self.modelType == "GMM":
            error = PYSAL.model.spreg.GM_Error(self.y, self.x, w = self.w, 
                                               name_y = self.depVarName,
                                               name_x = self.indVarNames, 
                                               name_w = self.wName,
                                               name_ds = self.ssdo.inputFC)
        else:
            error = PYSAL.model.spreg.GM_Error_Het(self.y, self.x, w = self.w, 
                                                   name_y = self.depVarName,
                                                   name_x = self.indVarNames, 
                                                   name_w = self.wName,
                                                   name_ds = self.ssdo.inputFC)
        self.error = error
        ARCPY.AddMessage(self.error.summary)

    def createOutput(self, outputFC):
        
        #### Build fields for output table ####
        candidateFields = {}
        fieldData = [self.error.predy.flatten(), self.error.u.flatten()]
        if self.modelType == "GMM_HAC":
            fieldData.append(self.error.e_filtered.ravel())
            fieldNames = HET_FIELDNAMES
            aliases = HET_FIELDALIAS
        else:
            fieldNames = FIELDNAMES
            aliases = FIELDALIAS

        for i, fieldName in enumerate(fieldNames):
            alias = aliases[i]
            if not i:
                alias = alias.format(self.depVarName)
            candidateFields[fieldName] = SSDO.CandidateField(fieldName,
                                                             "Double", 
                                                             fieldData[i],
                                                             alias = alias)

        self.ssdo.output2NewFC(outputFC, candidateFields, 
                               appendFields = self.allVars,
                               fieldOrder = fieldNames)
