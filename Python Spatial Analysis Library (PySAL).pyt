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
        self.tools = [ContiguityWeights]

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
        param3.filter.list = ["QUEEN", "ROOK"]
        param3.value = "QUEEN"

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

