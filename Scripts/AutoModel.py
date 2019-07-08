"""
Automatic Model Search.

Author(s): Luc Anselin, Xun Li
"""

import arcpy as ARCPY
import numpy as NUM
import pysal as PYSAL
import os as OS
import SSDataObject as SSDO
import SSUtilities as UTILS
import sys as SYS
import pysal2ArcUtils as AUTILS

# OLS Error result uses first 2, Lag result uses all 4
FIELDNAMES = ["Predy", "Resid", "Predy_e", "e_Pred"]
FIELDALIAS = ["Predicted {0}", "Residual", "Predicted {0} (Reduced Form)",
              "Prediced Error (Reduced Form)"]

MODELTYPES = ["GMM_COMBO", "GMM_HAC"]

class AutoSpace_PySAL(object):
    """Computes linear regression via Ordinary Least Squares using PySAL."""

    def __init__(self, ssdo, depVarName, indVarNames, patW,  
                 pValue = 0.1, modelType = "GMM_COMBO", 
                 kernelType = "Uniform", kernelKNN = 2):

        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Validate Model Type ####
        if modelType not in MODELTYPES:
            ARCPY.AddError("The input model type {0} is not in {1}".format(modelType, 
                                                                           ", ".join(MODELTYPES)))
            raise SystemExit()
        self.useCombo = modelType == "GMM_COMBO"

        #### Initialize Data ####
        self.initialize()

        #### Variables for Output ####
        self.oPredy = None
        self.oResid = None
        self.oPredy_e= None
        self.oE_Predy= None
        
        #### Calculate Statistic ####
        self.calculate()

    def initialize(self):
        """Performs additional validation and populates the SSDataObject."""

        ARCPY.SetProgressor("default", ("Starting to perform Automatic Model "
                                        "Search. Loading features..."))
        
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

        #### Assure that p-Value is Between 0 and 1 ####
        if self.pValue <= 0 or self.pValue >= 1.0:
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

        if self.modelType == "GMM_HAC":
            import pysal.lib.weights as WEIGHTS
            self.w.transform = 'r'
            dataArray = self.ssdo.xyCoords
            kernelName = "{0} function with knn = {1}"
            kernelName = kernelName.format(self.kernelType, self.kernelKNN)
            kernelWeights = WEIGHTS.Kernel(dataArray, fixed = True, k = self.kernelKNN,
                                           function = self.kernelType, diagonal = True)
            self.gwk = kernelWeights
            self.gwkName = kernelName
        else:
            self.gwk = None
            self.gwkName = None

    def calculate(self):
        """Performs Auto Model and related diagnostics."""

        ARCPY.SetProgressor("default", "Executing Automatic Model Search...")
       
        #### Performance AutoModel #### 
        autoTestResult = None
        try:
            autoTestResult = AUTILS.autospace(self.y, self.x, self.w, self.gwk,
                                          opvalue = self.pValue,
                                          combo = self.useCombo,
                                          name_y = self.depVarName,
                                          name_x = self.indVarNames,
                                          name_w = self.wName,
                                          name_gwk = self.gwkName,
                                          name_ds = self.ssdo.inputFC)
        except:
            import traceback
            ARCPY.AddError(("There is an error occurred when automatically "
                            "search spatial model. Details: " + \
                            traceback.format_exc()))
            raise SystemExit()
      
        #### Extract final model from autoTestResult ####
        olsModel = autoTestResult['regression1']
        finalModel = autoTestResult['regression2']
        
        summary = None 
        
        if autoTestResult["final model"].startswith('No Space') or \
           autoTestResult["final model"].startswith('Robust'):
            self.oPredy = olsModel.predy
            self.oResid = olsModel.u
            summary = olsModel.summary
            
        elif autoTestResult["final model"].startswith('Spatial Lag'):
            self.oPredy = finalModel.predy
            self.oResid = finalModel.u
            self.oPredy_e = finalModel.predy_e
            self.oE_Predy = finalModel.e_pred if finalModel.e_pred is not None else \
                NUM.ones(self.ssdo.numObs) * NUM.nan
            summary = finalModel.summary
            
        elif autoTestResult["final model"].startswith('Spatial Error'):
            self.oPredy = finalModel.predy
            self.oResid = finalModel.u
            summary = finalModel.summary
        
        else:
            msg = ("There is an error in Automatic Model Search. Please check "
                   "the input setup and weights files.")
            ARCPY.AddError(msg)
            raise SystemExit()
       
        #### Add "Het" in field name if "hetroskedasticity" in model ####
        if autoTestResult['heteroskedasticity'] == True:
            for i in range(len(FIELDNAMES)):
                FIELDNAMES[i] = "Het" + FIELDNAMES[i]
       
        #### Print model summary #### 
        if finalModel:
            ARCPY.AddMessage("OLS diagnostics:")
            ARCPY.AddMessage(olsModel.summary)
            ARCPY.AddMessage("")
            
        msg = "Final model:" + autoTestResult["final model"] 
        ARCPY.AddMessage(msg)
        
        if summary:
            ARCPY.AddMessage(summary)

        self.olsModel = olsModel
        self.finalModel = finalModel
        
    def createOutput(self, outputFC):

        #### Build fields for output table ####
        self.templateDir = OS.path.dirname(SYS.argv[0])
        candidateFields = {}
        fieldOrder = FIELDNAMES[0:2]
        alias = FIELDALIAS[0].format(self.depVarName)
        candidateFields[FIELDNAMES[0]] = SSDO.CandidateField(FIELDNAMES[0],
                                                             "Double", 
                                                             self.oPredy.ravel(),
                                                             alias = alias)
        alias = FIELDALIAS[1]
        candidateFields[FIELDNAMES[1]] = SSDO.CandidateField(FIELDNAMES[1],
                                                             "Double", 
                                                             self.oResid.ravel(),
                                                             alias = alias)
        if self.oPredy_e is not None: 
            fieldOrder = FIELDNAMES
            alias = FIELDALIAS[2].format(self.depVarName)
            candidateFields[FIELDNAMES[2]] = SSDO.CandidateField(FIELDNAMES[2],
                                                                 "Double", 
                                                                 self.oPredy_e.ravel(),
                                                                 alias = alias)
        if self.oE_Predy is not None:
            alias = FIELDALIAS[3]
            candidateFields[FIELDNAMES[3]] = SSDO.CandidateField(FIELDNAMES[3],
                                                                 "Double", 
                                                                 self.oE_Predy.ravel(),
                                                                 alias = alias)

        self.ssdo.output2NewFC(outputFC, candidateFields, 
                               appendFields = self.allVars,
                               fieldOrder = fieldOrder)

if __name__ == '__main__':
    setupParameters()
