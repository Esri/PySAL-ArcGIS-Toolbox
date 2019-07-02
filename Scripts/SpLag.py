"""
This script calls the Spatial Lag SAR functionality from the PySAL Module
within the ArcGIS environment.

Author(s): Mark Janikas, Xing Kang, Sergio Rey, Hu Shao
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
FIELDALIAS = ["Predicted {0}", "Residual", "Predicted {0} (Reduced Form)",
              "Prediced Error (Reduced Form)"]
MODELTYPES = ["GMM_COMBO", "GMM_HAC", "ML"]

class Lag_PySAL(object):
    """Computes SAR Lag linear regression via GMM/ML using PySAL."""

    def __init__(self, ssdo, depVarName, indVarNames, patW, 
                 modelType = "GMM_COMBO", gwkW = None):

        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Validate Model Type ####
        if modelType not in MODELTYPES:
            ARCPY.AddError("The input model type {0} is not in {1}".format(modelType, 
                                                                           ", ".join(MODELTYPES)))
            raise SystemExit()

        #### Assure Kernel Weights for HAC ####
        if modelType == "GMM_HAC" and gwkW is None:
            m = "You must provide kernel weights matrix when using the HAC Estimator"
            ARCPY.AddError(m)
            raise SystemExit()

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

        if self.gwkW is not None:
            self.gwk = self.gwkW.w
            self.gwkName = self.gwkW.wName

    def calculate(self):
        """Performs GM Error Model and related diagnostics."""

        ARCPY.SetProgressor("default", "Executing Spatial Lag regression...")

        #### Perform GM_Lag regression ####
        if self.modelType == "GMM_COMBO":
            self.lag = PYSAL.model.spreg.GM_Lag(self.y, self.x, w = self.w, 
                                                robust = 'white', spat_diag = True, 
                                                name_y = self.depVarName,
                                                name_x = self.indVarNames, 
                                                name_w = self.wName,
                                                name_ds = self.ssdo.inputFC)
        elif self.modelType == "GMM_HAC":
            self.lag = PYSAL.model.spreg.GM_Lag(self.y, self.x, w = self.w, 
                                                robust = 'hac', gwk = self.gwk,
                                                spat_diag = True, 
                                                name_y = self.depVarName,
                                                name_x = self.indVarNames, 
                                                name_w = self.wName,
                                                name_gwk = self.gwkName,
                                                name_ds = self.ssdo.inputFC)
        else:
            self.lag = PYSAL.model.spreg.ML_Lag(self.y, self.x, self.w,
                                                spat_diag = True,
                                                name_y = self.depVarName,
                                                name_x = self.indVarNames, 
                                                name_w = self.wName,
                                                name_ds = self.ssdo.inputFC)
        ARCPY.AddMessage(self.lag.summary)

    def createOutput(self, outputFC):

        #### Build fields for output table ####
        nullFlag = self.lag.e_pred is None
        if nullFlag:
            ePredOut = NUM.ones(self.ssdo.numObs) * NUM.nan
        else:
            ePredOut = self.lag.e_pred

        candidateFields = {}
        fieldData = [self.lag.predy.flatten(), self.lag.u.flatten(),
                     self.lag.predy_e.flatten(), ePredOut.flatten()]
        for i, fieldName in enumerate(FIELDNAMES):
            alias = FIELDALIAS[i]
            if i in [0, 2]:
                alias = alias.format(self.depVarName)
            candidateFields[fieldName] = SSDO.CandidateField(fieldName,
                                                             "Double", 
                                                             fieldData[i],
                                                             alias = alias,
                                                             checkNullValues = nullFlag)
        self.ssdo.output2NewFC(outputFC, candidateFields, 
                               appendFields = self.allVars,
                               fieldOrder = FIELDNAMES)

