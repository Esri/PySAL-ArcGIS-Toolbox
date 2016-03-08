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
FIELDNAMES = ["Predy", "Resid", "Predy_e", "e_Predy"]

def setupParameters():

    #### Get User Provided Inputs ####
    inputFC = ARCPY.GetParameterAsText(0)
    depVarName = ARCPY.GetParameterAsText(1).upper()
    indVarNames = ARCPY.GetParameterAsText(2).upper()
    indVarNames = indVarNames.split(";")
    weightsFile = ARCPY.GetParameterAsText(3)
    kernelWeightsFile = ARCPY.GetParameterAsText(4)
    pValue = ARCPY.GetParameter(5)
    useCombo = ARCPY.GetParameter(6)
    outputFC = ARCPY.GetParameterAsText(7)

    #### Create SSDataObject ####
    fieldList = [depVarName] + indVarNames
    ssdo = SSDO.SSDataObject(inputFC, templateFC = outputFC)
    
    #### Setup masterField for ssdo from Model weights file ####
    masterField1 = AUTILS.setUniqueIDField(ssdo, weightsFile)
    if masterField1 == None:
        ARCPY.AddError("The Model weights file format is not valid.")
        raise SystemExit()
        
    #### Setup masterField for ssdo from Kernel weights file ####
    masterField2 = None
    wType = kernelWeightsFile[-3:].lower()
    if wType == "kwt" or wType == "swm":
        masterField2 = AUTILS.setUniqueIDField(ssdo, kernelWeightsFile)
    if masterField2 == None:
        ARCPY.AddError("The Kernel weights file format is not valid.")
        raise SystemExit()
    
    #### Detect if Two Weights Files Are Matched (Same Unique Field) ####
    if masterField1 != masterField2:
        ARCPY.AddError("The Model weights file and Kernel weights file have "
                       "different unique ID fields.")
        raise SystemExit()
    
    #### Populate SSDO with Data ####
    ssdo.obtainData(masterField1, fieldList) 

    #### Resolve Weights File ####
    patW = None
    patKW = None
    try:
        patW = AUTILS.PAT_W(ssdo, weightsFile)
        patKW = AUTILS.PAT_W(ssdo, kernelWeightsFile)
    except:
        ARCPY.AddError("There is an error occurred when read weights files.")
        raise SystemExit()

    #### Run AutoSpace ####
    auto = AutoSpace_PySAL(ssdo, depVarName, indVarNames, patW, patKW, pValue,
                           useCombo)

    #### Create Output ####
    auto.createOutput(outputFC)


class AutoSpace_PySAL(object):
    """Computes linear regression via Ordinary Least Squares using PySAL."""

    def __init__(self, ssdo, depVarName, indVarNames, patW, patKW, 
                 pValue = 0.01, useCombo = False):

        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

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
        self.gwk = self.patKW.w
        self.gwkName = self.patKW.wName

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
        
    def createOutput(self, outputFC):

        #### Build fields for output table ####
        self.templateDir = OS.path.dirname(SYS.argv[0])
        candidateFields = {}
        candidateFields[FIELDNAMES[0]] = SSDO.CandidateField(FIELDNAMES[0],
                                                             "Double", 
                                                             self.oPredy)
        candidateFields[FIELDNAMES[1]] = SSDO.CandidateField(FIELDNAMES[1],
                                                             "Double", 
                                                             self.oResid)
        if self.oPredy_e != None: 
            candidateFields[FIELDNAMES[2]] = SSDO.CandidateField(FIELDNAMES[2],
                                                                 "Double", 
                                                                 self.oPredy_e)
        if self.oE_Predy != None:
            candidateFields[FIELDNAMES[3]] = SSDO.CandidateField(FIELDNAMES[3],
                                                                 "Double", 
                                                                 self.oE_Predy)

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
            if FIELDNAMES[0].startswith('Het'):
                renderLayerFile = "Het" + renderLayerFile
            fullRLF = OS.path.join(self.templateDir, "Layers", renderLayerFile)
            params[7].Symbology = fullRLF
        except:
            ARCPY.AddIDMessage("WARNING", 973)

if __name__ == '__main__':
    setupParameters()
