import arcpy as  ARCPY
import os as OS
import sys as SYS
import SSDataObject as SSDO
import SSUtilities as UTILS
import WeightsUtilities as WU
import warnings as WARN

#### Disable PySAL Warnings ####
if not SYS.warnoptions:
    WARN.simplefilter("ignore")

FEATURETYPE = ['POINT', 'MULTIPOINT', 'POLYGON']
DISTMETHODS = ['Threshold Distance', 'K Nearest Neighbors', 'Inverse Distance']

def paramChanged(param, checkValue = False):
    changed = param.altered and not param.hasBeenValidated
    if checkValue:
        if param.value:
            return changed
        else:
            return False 
    else:
        return changed

class Toolbox(object):
    def __init__(self):
        self.label = "Python Spatial Analysis Library (PySAL)"
        self.alias = "pysal"
        self.tools = [ContiguityWeights, DistanceWeights,
                      OLS, SpatialError, SpatialLag]

class ContiguityWeights:
    def __init__(self):
        self.label = "Create Contiguity-Based Spatial Weights"
        self.description = ""
        self.category = "Spatial Weights Tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Input Feature Class",
                            name = "Input_Feature_Class",
                            datatype = "DEFeatureClass",
                            parameterType = "Required",
                            direction = "Input")
        param0.filter.list = ['Polygon']

        param1 = ARCPY.Parameter(displayName="Unique ID Field",
                            name = "Unique_ID_Field",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input")

        param1.filter.list = ['Short','Long']

        param1.parameterDependencies = ["Input_Feature_Class"]

        param2 = ARCPY.Parameter(displayName="Output Spatial Weights Matrix File",
                                 name = "Output_Spatial_Weights_Matrix_File",
                                 datatype = "DEFile",
                                 parameterType = "Required",
                                 direction = "Output")
        param2.filter.list = ['swm', 'gwt', 'gal']

        param3 = ARCPY.Parameter(displayName="Contiguity Type",
                            name = "Contiguity_Type",
                            datatype = "GPString",
                            parameterType = "Optional",
                            direction = "Input")

        param3.filter.type = "ValueList"
        param3.filter.list = ["Queen", "Rook"]
        param3.value = "Queen"

        param4 = ARCPY.Parameter(displayName="Order of Contiguity",
                            name = "Order_of_Contiguity",
                            datatype = "GPLong",
                            parameterType = "Optional",
                            direction = "Input")
        param4.filter.type = "Range"
        param4.value = 1
        param4.filter.list = [1, 9]

        param5 = ARCPY.Parameter(displayName="Include Lower Orders",
                                 name = "Include_Lower_Orders",
                                 datatype = "GPBoolean",
                                 parameterType = "Optional",
                                 direction = "Input")
        param5.filter.list = ['INCLUDE_LOWER_ORDERS', 'NO_LOWER_ORDERS']
        param5.value = True

        param6 = ARCPY.Parameter(displayName="Row Standardization",
                            name = "Row_Standardization",
                            datatype = "GPBoolean",
                            parameterType = "Optional",
                            direction = "Input")
        param6.filter.list = ['ROW_STANDARDIZATION', 'NO_STANDARDIZATION']
        param6.value = True

        return [param0,param1,param2,param3,param4,param5,param6]

    def updateParameters(self, parameters):
        pass

    def updateMessages(self, parameters):
        pass

    def execute(self, parameters, messages):
        import SSUtilities as UTILS
        import ContWeightsCreator as CONT


        inputFC = UTILS.getTextParameter(0, parameters)
        idField = UTILS.getTextParameter(1, parameters)
        outputFile = UTILS.getTextParameter(2, parameters)
        weightType = UTILS.getTextParameter(3, parameters)
        if weightType is None:
            weightType = "QUEEN"

        weightOrder = UTILS.getNumericParameter(4, parameters)
        if weightOrder is None:
            weightOrder = 1

        isLowerOrder = parameters[5].value
        rowStandard = parameters[6].value

        #### Run Cont Weights Creation ####
        contW = CONT.ContW_PySAL(inputFC, outputFile, idField, weightType, weightOrder, 
                                 isLowerOrder)
    
        #### Create Output ####
        contW.createOutput(rowStandard)


class DistanceWeights:
    def __init__(self):
        self.label = "Create Distance-Based Spatial Weights"
        self.description = ""
        self.category = "Spatial Weights Tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Input Feature Class",
                            name = "Input_Feature_Class",
                            datatype = "DEFeatureClass",
                            parameterType = "Required",
                            direction = "Input")

        param1 = ARCPY.Parameter(displayName="Unique ID Field",
                            name = "Unique_ID_Field",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input")

        param1.filter.list = ['Short','Long']
        param1.parameterDependencies = ["Input_Feature_Class"]

        param2 = ARCPY.Parameter(displayName="Output Spatial Weights Matrix File",
                                 name = "Output_Spatial_Weights_Matrix_File",
                                 datatype = "DEFile",
                                 parameterType = "Required",
                                 direction = "Output")
        param2.filter.list = ['swm', 'gwt', 'gal']

        param3 = ARCPY.Parameter(displayName="Distance Methods",
                            name = "Distance_Methods",
                            datatype = "GPString",
                            parameterType = "Optional",
                            direction = "Input")

        param3.filter.type = "ValueList"
        param3.filter.list = DISTMETHODS
        param3.value = "Threshold Distance"

        param4 = ARCPY.Parameter(displayName="Threshold Distance",
                            name = "Distance",
                            datatype = "GPDouble",
                            parameterType = "Optional",
                            direction = "Input")

        param5 = ARCPY.Parameter(displayName="# of Nearest Neighbors",
                                 name = "number_of_Nearest_Neighbors",
                                 datatype = "GPLong",
                                 parameterType = "Optional",
                                 direction = "Input")
        param5.filter.type = "Range"
        param5.filter.list = [1, 15]
        param5.value = 1

        param6 = ARCPY.Parameter(displayName="Power of Inverse Distance",
                                 name = "Power_of_Inverse_Distance",
                                 datatype = "GPLong",
                                 parameterType = "Optional",
                                 direction = "Input")
        param6.filter.type = "Range"
        param6.filter.list = [1, 5]
        param6.value = 1

        param7 = ARCPY.Parameter(displayName="Row Standardization",
                            name = "Row_Standardization",
                            datatype = "GPBoolean",
                            parameterType = "Optional",
                            direction = "Input")
        param7.filter.list = ['ROW_STANDARDIZATION', 'NO_STANDARDIZATION']
        param7.value = True

        return [param0, param1, param2, param3, param4, param5, param6, param7]
    
    def findFurthestPt(self, ptList, pt):
        dist = 0
        returnPt = 0
        for pt1 in ptList:
            dist1 = (pt1[0] - pt[0])**2 + (pt1[1] - pt[1])**2
            if dist1 > dist:
                dist = math.sqrt(dist1)
                returnPt = pt1
        return returnPt

    def updateParameters(self, parameters):
        if parameters[3].value == DISTMETHODS[0] or parameters[3].value == DISTMETHODS[2]:
            parameters[4].enabled = True
        else:
            parameters[4].enabled = False

        if parameters[3].value == DISTMETHODS[1]:
            parameters[5].enabled = True
        else:
            parameters[5].enabled = False
        
        if parameters[3].value == DISTMETHODS[2]:
            parameters[6].enabled = True
        else:
            parameters[6].enabled = False
        
        if parameters[0].Value and paramChanged(parameters[0]):
            curPath = str(parameters[0].Value)

            # deal with nearest neighbor
            if curPath[-4:] == ".shp":
                import pysal, math
                shapes = pysal.open(curPath, 'r')
                length = len(shapes)
                # deal with threshold distance
                pts = []
                if shapes.type == pysal.cg.Polygon:
                    pts = [poly.centroid for poly in shapes]
                elif shapes.type == pysal.cg.Point:
                    pts = [pt for pt in shapes]
                else:
                    return
                shapes.close()
                del pysal
            else:
                desc = arcpy.Describe(curPath)
                shpType = desc.ShapeType.upper()
                shpFld = desc.shapeFieldName
                cursor = 0
                length = 0
                pts = []
                if shpType == FEATURETYPE[0]:
                    cursor = arcpy.SearchCursor(curPath)
                    for row in cursor:
                        length += 1
                        pt = row.getValue(shpFld).getPart()
                        pts.append((pt.X, pt.Y))
                elif shpType == FEATURETYPE[1]:
                    cursor = arcpy.SearchCursor(curPath)
                    for row in cursor:
                        multiPt = row.getValue(shpFld)
                        length += multiPt.count
                        for pt in multiPt:
                            pts.append((pt.X, pt.Y))
                elif shpType == FEATURETYPE[2]:
                    cursor = arcpy.SearchCursor(curPath)
                    for row in cursor:
                        length += 1
                        polys = row.getValue(shpFld)
                        centroid = polys.centroid
                        pts.append((centroid.X, centroid.Y))
                else:
                    return

            import math
            # following geodaspace, use cubic root as default nearest neighbor num
            num = int(math.ceil(length**(1.0/3)))
            parameters[5].Filter.List = [1, length]
            parameters[5].Value = num
            l = len(pts)
            ranPt = pts[(l+1)//2]
            fPt = self.findFurthestPt(pts, ranPt)
            fPt2 = self.findFurthestPt(pts, fPt)
            dist = math.sqrt((fPt2[0] - fPt[0])**2 + (fPt2[1] - fPt[1])**2)
            parameters[4].Value = dist
            del math            
        return


    def updateMessages(self, parameters):
        pass

    def execute(self, parameters, messages):
        import SSUtilities as UTILS
        import DistWeightsCreator as DIST


        inputFC = UTILS.getTextParameter(0, parameters)
        idField = UTILS.getTextParameter(1, parameters)
        outputFile = UTILS.getTextParameter(2, parameters)
        distanceType = UTILS.getTextParameter(3, parameters)
        rowStandard = parameters[7].value

        #### Validate Input of Distance Type ####
        if not distanceType or distanceType not in DISTMETHODS:
            ARCPY.AddError("Distance type is not set, or it is not in the "
                        "predefined list...")
            raise SystemExit()

        #### Setup Default Values of Threshold/KnnNum/InverseDist ####
        threshold = UTILS.getNumericParameter(4, parameters) \
            if distanceType == DISTMETHODS[0] or distanceType == DISTMETHODS[2] else None
        knnNum = UTILS.getNumericParameter(5, parameters) \
            if distanceType == DISTMETHODS[1] else None
        inverseDist = UTILS.getNumericParameter(6, parameters) \
            if distanceType == DISTMETHODS[2] else None

        #### Run Dist Weights Creation ####
        distW = DIST.DistW_PySAL(inputFC, outputFile, idField, distanceType, threshold,\
                            knnNum, inverseDist)
        
        #### Create Output ####
        distW.createOutput(rowStandard)
       
        
# class KernelWeights:
#     def __init__(self):
#         self.label = "Create Kernel-Based Spatial Weights"
#         self.description = ""
#         self.category = "Spatial Weights Tools"
#         self.canRunInBackground = False

#     def getParameterInfo(self):
#         param0 = ARCPY.Parameter(displayName="Input Feature Class",
#                             name = "Input_Feature_Class",
#                             datatype = "DEFeatureClass",
#                             parameterType = "Required",
#                             direction = "Input")

#         param1 = ARCPY.Parameter(displayName="Unique ID Field",
#                             name = "Unique_ID_Field",
#                             datatype = "Field",
#                             parameterType = "Required",
#                             direction = "Input")

#         param1.filter.list = ['Short','Long']

#         param1.parameterDependencies = ["Input_Feature_Class"]

#         param2 = ARCPY.Parameter(displayName="Output Spatial Weights Matrix File",
#                                  name = "Output_Spatial_Weights_Matrix_File",
#                                  datatype = "DEFile",
#                                  parameterType = "Required",
#                                  direction = "Output")
#         param2.filter.list = ['kwt']

#         param3 = ARCPY.Parameter(displayName="Kernel Function",
#                             name = "Kernel_Function",
#                             datatype = "GPString",
#                             parameterType = "Optional",
#                             direction = "Input")

#         param3.filter.type = "ValueList"
#         param3.filter.list = ["Uniform", "Triangular", "Quadratic", "Quartic", "Gaussian"]
#         param3.value = "Uniform"

#         param4 = ARCPY.Parameter(displayName="Number of Neighbors",
#                                  name = "Number_of_Neighbors",
#                                  datatype = "GPLong",
#                                  parameterType = "Optional",
#                                  direction = "Input")
#         param4.filter.type = "Range"
#         param4.value = 1
#         param4.filter.list = [1, 99]

#         return [param0,param1,param2,param3,param4]

#     def updateParameters(self, parameters):
#         pass

#     def updateMessages(self, parameters):
#         pass

#     def execute(self, parameters, messages):
#         import SSUtilities as UTILS
#         import KernelWeightsCreator as KERNEL


#         inputFC = UTILS.getTextParameter(0, parameters)
#         idField = UTILS.getTextParameter(1, parameters)
#         outputFile = UTILS.getTextParameter(2, parameters)
#         kernelType = UTILS.getTextParameter(3, parameters)
#         if kernelType is None:
#             kernelType = "UNIFORM"

#         numNeighs = UTILS.getNumericParameter(4, parameters)
#         if numNeighs is None:
#             numNeighs = 1

#         #### Run Cont Weights Creation ####
#         contW = KERNEL.KernelW_PySAL(inputFC, outputFile, idField, kernelType,
#                                      numNeighs)
    
#         #### Create Output ####
#         contW.createOutput()

class OLS:
    def __init__(self):
        self.label = "Runs OLS with Residual Spatial Diagnostics"
        self.description = ""
        self.category = "Spatial Regression Tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Input Features",
                            name = "input_features",
                            datatype = "GPFeatureLayer",
                            parameterType = "Required",
                            direction = "Input")

        param1 = ARCPY.Parameter(displayName="Dependent Variable",
                            name = "dependent_variable",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input")
        param1.filter.list = ['Short','Long','Float','Double']
        param1.parameterDependencies = ["input_features"]

        param2 = ARCPY.Parameter(displayName="Explanatory Variable(s)",
                            name = "explanatory_variables",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input",
                            multiValue = True)
        param2.filter.list = ['Short','Long','Float','Double']
        param2.parameterDependencies = ["input_features"]
        param2.controlCLSID = "{38C34610-C7F7-11D5-A693-0008C711C8C1}"

        param3 = ARCPY.Parameter(displayName="Input Spatial Weights Matrix File",
                            name = "Input_Spatial_Weights_Matrix_File",
                            datatype = "DEFile",
                            parameterType = "Required",
                            direction = "Input")

        param3.filter.list = ['swm', 'gal', 'gwt']

        param4 = ARCPY.Parameter(displayName="Output Feature Class",
                            name = "Output_Feature_Class",
                            datatype = "DEFeatureClass",
                            parameterType = "Required",
                            direction = "Output")
        
        return [param0,param1,param2,param3,param4]

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import SSUtilities as UTILS
        import SSDataObject as SSDO
        import pysal2ArcUtils as AUTILS
        import OLSPySAL as OLS_PYSAL

        inputFC = UTILS.getTextParameter(0, parameters)
        depVarName = UTILS.getTextParameter(1, parameters).upper()
        indVarNames = UTILS.getTextParameter(2, parameters).upper()
        indVarNames = indVarNames.split(";")
        weightsFile = UTILS.getTextParameter(3, parameters)
        outputFC = UTILS.getTextParameter(4, parameters)

        #### Create SSDataObject ####
        fieldList = [depVarName] + indVarNames
        ssdo = SSDO.SSDataObject(inputFC, templateFC = outputFC)
        masterField = AUTILS.setUniqueIDField(ssdo, weightsFile)

        #### Populate SSDO with Data ####
        ssdo.obtainData(masterField, fieldList, minNumObs = 5) 

        #### Create Weights ####
        patW = AUTILS.PAT_W(ssdo, weightsFile)

        #### Run OLS ####
        ols = OLS_PYSAL.OLS_PySAL(ssdo, depVarName, indVarNames, patW)

        #### Create Output ####
        ols.createOutput(outputFC)

        #### Render Output ####
        templateDir = OS.path.join(SYS.path[0], "Scripts", "Layers")
        try:
            renderType = UTILS.renderType[ssdo.shapeType.upper()]
            if renderType == 0:
                renderLayerFile = "ResidPoints.lyr"
            elif renderType == 1:
                renderLayerFile = "ResidPolylines.lyr"
            else:
                renderLayerFile = "ResidPolygons.lyr"
            fullRLF = OS.path.join(templateDir, renderLayerFile)
            parameters[4].symbology = fullRLF
        except:
            ARCPY.AddIDMessage("WARNING", 973)

class SpatialError:
    def __init__(self):
        self.label = "Runs Spatial Error SAR Model"
        self.description = ""
        self.category = "Spatial Regression Tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Input Features",
                            name = "input_features",
                            datatype = "GPFeatureLayer",
                            parameterType = "Required",
                            direction = "Input")

        param1 = ARCPY.Parameter(displayName="Dependent Variable",
                            name = "dependent_variable",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input")
        param1.filter.list = ['Short','Long','Float','Double']
        param1.parameterDependencies = ["input_features"]

        param2 = ARCPY.Parameter(displayName="Explanatory Variable(s)",
                            name = "explanatory_variables",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input",
                            multiValue = True)
        param2.filter.list = ['Short','Long','Float','Double']
        param2.parameterDependencies = ["input_features"]
        param2.controlCLSID = "{38C34610-C7F7-11D5-A693-0008C711C8C1}"

        param3 = ARCPY.Parameter(displayName="Input Spatial Weights Matrix File",
                            name = "Input_Spatial_Weights_Matrix_File",
                            datatype = "DEFile",
                            parameterType = "Required",
                            direction = "Input")

        param3.filter.list = ['swm', 'gal', 'gwt']

        param4 = ARCPY.Parameter(displayName="Output Feature Class",
                            name = "Output_Feature_Class",
                            datatype = "DEFeatureClass",
                            parameterType = "Required",
                            direction = "Output")
        
        param5 = ARCPY.Parameter(displayName="Choice of Estimator",
                                 name = "choice_of_estimator",
                                 datatype = "GPString",
                                 parameterType = "Optional",
                                 direction = "Input")
        param5.filter.type = "ValueList"
        param5.filter.list = ['GMM','GMM HAC','ML']
        param5.value = 'GMM'

        return [param0,param1,param2,param3,param4,param5]

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import SSUtilities as UTILS
        import SSDataObject as SSDO
        import pysal2ArcUtils as AUTILS
        import SpError as ERROR

        inputFC = UTILS.getTextParameter(0, parameters)
        depVarName = UTILS.getTextParameter(1, parameters).upper()
        indVarNames = UTILS.getTextParameter(2, parameters).upper()
        indVarNames = indVarNames.split(";")
        weightsFile = UTILS.getTextParameter(3, parameters)
        outputFC = UTILS.getTextParameter(4, parameters)
        modelType = UTILS.getTextParameter(5, parameters).upper().replace(" ", "_")

        #### Create SSDataObject ####
        fieldList = [depVarName] + indVarNames
        ssdo = SSDO.SSDataObject(inputFC, templateFC = outputFC)
        masterField = AUTILS.setUniqueIDField(ssdo, weightsFile)

        #### Populate SSDO with Data ####
        ssdo.obtainData(masterField, fieldList, minNumObs = 5) 

        #### Create Weights ####
        patW = AUTILS.PAT_W(ssdo, weightsFile)

        #### Run Model ####
        error = ERROR.Error_PySAL(ssdo, depVarName, indVarNames, patW, modelType)

        #### Create Output ####
        error.createOutput(outputFC)

        #### Render Output ####
        templateDir = OS.path.join(SYS.path[0], "Scripts", "Layers")
        try:
            renderType = UTILS.renderType[ssdo.shapeType.upper()]
            if renderType == 0:
                renderLayerFile = "ResidPoints.lyr"
            elif renderType == 1:
                renderLayerFile = "ResidPolylines.lyr"
            else:
                renderLayerFile = "ResidPolygons.lyr"
            fullRLF = OS.path.join(templateDir, renderLayerFile)
            parameters[4].symbology = fullRLF
        except:
            ARCPY.AddIDMessage("WARNING", 973)


class SpatialLag:
    def __init__(self):
        self.label = "Runs Spatial Lag SAR Model"
        self.description = ""
        self.category = "Spatial Regression Tools"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = ARCPY.Parameter(displayName="Input Features",
                            name = "input_features",
                            datatype = "GPFeatureLayer",
                            parameterType = "Required",
                            direction = "Input")

        param1 = ARCPY.Parameter(displayName="Dependent Variable",
                            name = "dependent_variable",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input")
        param1.filter.list = ['Short','Long','Float','Double']
        param1.parameterDependencies = ["input_features"]

        param2 = ARCPY.Parameter(displayName="Explanatory Variable(s)",
                            name = "explanatory_variables",
                            datatype = "Field",
                            parameterType = "Required",
                            direction = "Input",
                            multiValue = True)
        param2.filter.list = ['Short','Long','Float','Double']
        param2.parameterDependencies = ["input_features"]
        param2.controlCLSID = "{38C34610-C7F7-11D5-A693-0008C711C8C1}"

        param3 = ARCPY.Parameter(displayName="Input Spatial Weights Matrix File",
                            name = "Input_Spatial_Weights_Matrix_File",
                            datatype = "DEFile",
                            parameterType = "Required",
                            direction = "Input")

        param3.filter.list = ['swm', 'gal', 'gwt']

        param4 = ARCPY.Parameter(displayName="Output Feature Class",
                            name = "Output_Feature_Class",
                            datatype = "DEFeatureClass",
                            parameterType = "Required",
                            direction = "Output")
        
        param5 = ARCPY.Parameter(displayName="Choice of Estimator",
                                 name = "choice_of_estimator",
                                 datatype = "GPString",
                                 parameterType = "Optional",
                                 direction = "Input")
        param5.filter.type = "ValueList"
        param5.filter.list = ['GMM Combo','GMM HAC','ML']
        param5.value = 'GMM Combo'

        param6 = ARCPY.Parameter(displayName="Kernel Function",
                            name = "Kernel_Function",
                            datatype = "GPString",
                            parameterType = "Optional",
                            direction = "Input")

        param6.filter.type = "ValueList"
        param6.filter.list = ["Uniform", "Triangular", "Quadratic", "Quartic", "Gaussian"]
        param6.value = "Uniform"

        param7 = ARCPY.Parameter(displayName="Number of Neighbors",
                                 name = "Number_of_Neighbors",
                                 datatype = "GPLong",
                                 parameterType = "Optional",
                                 direction = "Input")
        param7.filter.type = "Range"
        param7.value = 2
        param7.filter.list = [1, 99]

        return [param0,param1,param2,param3,param4,param5,param6,param7]

    def updateParameters(self, parameters):
        #### Enabled/Disable/Clear Kernel Weights for HAC ####
        if parameters[5].value:
            if parameters[5].value.upper() == "GMM HAC":
                parameters[6].enabled = True
                parameters[7].enabled = True
            else:
                parameters[6].enabled = False
                parameters[7].enabled = False

        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import SSUtilities as UTILS
        import SSDataObject as SSDO
        import pysal2ArcUtils as AUTILS
        import SpLag as LAG

        inputFC = UTILS.getTextParameter(0, parameters)
        depVarName = UTILS.getTextParameter(1, parameters).upper()
        indVarNames = UTILS.getTextParameter(2, parameters).upper()
        indVarNames = indVarNames.split(";")
        weightsFile = UTILS.getTextParameter(3, parameters)
        outputFC = UTILS.getTextParameter(4, parameters)
        modelType = UTILS.getTextParameter(5, parameters).upper().replace(" ", "_")
        kernelWeightType = UTILS.getTextParameter(6, parameters)
        if kernelWeightType is None:
            kernelWeightType = "UNIFORM"
        kernelWeightNumNeighs = UTILS.getNumericParameter(7, parameters)

        #### Create SSDataObject ####
        fieldList = [depVarName] + indVarNames
        ssdo = SSDO.SSDataObject(inputFC, templateFC = outputFC)
        masterField = AUTILS.setUniqueIDField(ssdo, weightsFile)

        #### Populate SSDO with Data ####
        ssdo.obtainData(masterField, fieldList, minNumObs = 5) 

        #### Create Weights ####
        patW = AUTILS.PAT_W(ssdo, weightsFile)

        lag = LAG.Lag_PySAL(ssdo, depVarName, indVarNames, patW, 
                            modelType=modelType, 
                            kernelWeightType=kernelWeightType, 
                            kernelWeightNumNeighs=kernelWeightNumNeighs)

        #### Create Output ####
        lag.createOutput(outputFC)

        #### Render Output ####
        templateDir = OS.path.join(SYS.path[0], "Scripts", "Layers")
        try:
            renderType = UTILS.renderType[ssdo.shapeType.upper()]
            if renderType == 0:
                renderLayerFile = "ResidPoints.lyr"
            elif renderType == 1:
                renderLayerFile = "ResidPolylines.lyr"
            else:
                renderLayerFile = "ResidPolygons.lyr"
            fullRLF = OS.path.join(templateDir, renderLayerFile)
            parameters[4].symbology = fullRLF
        except:
            ARCPY.AddIDMessage("WARNING", 973)
