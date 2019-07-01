"""
Create Contiguity-based Spatial Weights Files.

Author(s): Mark Janikas, Xing Kang, Sergio Rey, Xun Li
"""

import arcpy as ARCPY
import pysal as PYSAL
import pysal.lib.io as FileIO
import pysal.lib.weights as WEIGHTS
import SSUtilities as UTILS
import SSDataObject as SSDO
import pysal2ArcUtils as AUTILS
import WeightsUtilities as WU

EXTENSIONS = ['GAL', 'GWT', 'SWM']
WEIGHTTYPE = ['ROOK', 'QUEEN']

def setupParameters():
    
    #### Get User Provided Inputs ####
    inputFC = ARCPY.GetParameterAsText(0) 
    outputFile = ARCPY.GetParameterAsText(1)
    idField = UTILS.getTextParameter(2)
    weightType = UTILS.getTextParameter(3).upper() 
    weightOrder = UTILS.getNumericParameter(4)
    isLowOrder = ARCPY.GetParameter(5)
    
    #### Validate Input of WeightType ####
    if not weightType or weightType not in WEIGHTTYPE:
        ARCPY.AddError("Weights type can only be Rook or Queen...")
        raise SystemExit()

    #### Run Cont Weights Creation ####
    contW = ContW_PySAL(inputFC, outputFile, idField, weightType, weightOrder, \
                        isLowOrder)
    
    #### Create Output ####
    contW.createOutput()
    
class ContW_PySAL(object):
    """Create Contiguity-based Weights Using PySAL."""
    
    def __init__(self, inputFC, outputFile, idField, weightType, weightOrder,\
                 isLowOrder=False):
        
        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Set Object for Weights Creation ####
        self.ssdo = None
        self.weightObj = None
        self.polyNeighborDict = None
        self.outputExt = AUTILS.returnWeightFileType(outputFile)
        
        #### Initialize Data ####
        self.initialize()

        #### Build Weights ####
        self.buildWeights()

    def initialize(self):
        """Performs additional validation and populates the  SSDataObject."""
        ARCPY.SetProgressor("default", ("Starting to create contiguity-based "
                                        "weights. Loading features..."))
        
        #### Shorthand Attributes ####
        idField = self.idField
        inputFC = self.inputFC
        
        #### Create SSDataObject ####
        self.ssdo = SSDO.SSDataObject(inputFC)
        ssdo = self.ssdo
        
        #### Raise Error If Valid Unique ID Not Provided ####
        masterField = idField
        if not masterField:
            if self.outputExt in EXTENSIONS[1:]:
                msg = ("The unique ID Field is required to create GWT and/or "
                       "SWM spatial weights files...")
                ARCPY.AddError(msg)
                raise SystemExit()
            else:
                msg = ("The unique ID Field is not provided. The zero-based "
                       "indexing order will be used to create the spatial "
                       "weights file.")
                ARCPY.AddWarning(msg)
                masterField = UTILS.setUniqueIDField(ssdo)
                
        #### Populate SSDO with Data ####
        ssdo.obtainData(masterField)
        self.masterField = masterField
        
    def buildWeights(self):
        """Performs Contiguity-based Weights Creation."""
        ARCPY.SetProgressor("default", "Constructing spatial weights object...")
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo
        isLowOrder = self.isLowOrder
        weightOrder = self.weightOrder
        
        #### Get Neighbor Dictionary for All Polygons #### 
        master2Order = ssdo.master2Order
        polyNeighborDict = WU.polygonNeighborDict(self.inputFC, \
                                                  self.masterField, \
                                                  contiguityType=self.weightType)
        
        #### Assign empty list to polygons without neighbors ####
        if ssdo.numObs > len(polyNeighborDict):
            for masterKey in master2Order.keys():
                if not polyNeighborDict.has_key(masterKey):
                    polyNeighborDict[masterKey] = []
        
        #### Convert DefaultDict to Real Dict ?####
        if not self.idField:
            polyNeighborCopy = {}
            for key in polyNeighborDict.keys():
                polyNeighborCopy[master2Order[key]] = []
                for item in polyNeighborDict[key]:
                    polyNeighborCopy[master2Order[key]].\
                        append(master2Order[item])
            polyNeighborDict = polyNeighborCopy
       
        #### Create a PySAL W Object ####
        weightObj = WEIGHTS.W(polyNeighborDict)
            
        #### Building up Lower Order Spatial Weights ####
        if weightOrder > 1:
            ARCPY.SetProgressor("default", \
                                "Building up Lower Order Spatial Weights...")
            origWeight = weightObj
            weightObj = WEIGHTS.higher_order(weightObj, weightOrder)
            if isLowOrder:
                for order in range(weightOrder-1, 1, -1):
                    lowOrderW = WEIGHTS.higher_order(origWeight, order)
                    weightObj = WEIGHTS.w_union(weightObj, lowOrderW)
                weightObj = WEIGHTS.w_union(weightObj, origWeight)        
    
        #### Save weightObj Class Object for Writing Result #### 
        self.weightObj = weightObj
        
    def createOutput(self, rowStandard = False):
        """ Write Contiguity-based Weights to File """
        ARCPY.SetProgressor("default", \
                            "Writing Spatial Weights to Output File...")
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo
        idField = self.idField
        weightObj = self.weightObj
        outputFile = self.outputFile
  
        #### Get File Name Without Extension ####
        fileName = ssdo.inName.rsplit('.',1)[0]
        
        if self.outputExt == EXTENSIONS[0]:
            # GAL file
            outputWriter = open(outputFile, 'w')
            # write header in the first line
            header = "%s\n" % weightObj.n if not idField else \
                "%s %s %s %s\n" %  (0, weightObj.n, idField, 'UNKNOWN')
            outputWriter.write(header)
            # write content
            masterIDs = list(weightObj.neighbors.keys())
            masterIDs.sort()
            for id in masterIDs:
                neighbors = weightObj.neighbors[id]
                outputWriter.write("%s %s\n" % (id, len(neighbors)) )
                line = " ".join([str(item) for item in neighbors])
                outputWriter.write("%s\n" % line)
            outputWriter.close()
            
        elif self.outputExt == EXTENSIONS[1]:
            # GWT file
            outputWriter = FileIO.open(outputFile, 'w')
            outputWriter.shpName = fileName
            if idField:
                outputWriter.varName = idField
            outputWriter.write(weightObj)
            outputWriter.close()
        else:
            # SWM file
            masterField = idField if idField else 'UNKNOWN'
            swmWriter = WU.SWMWriter(outputFile, masterField, \
                                     ssdo.spatialRefName, weightObj.n, \
                                     rowStandard)
            masterIDs = list(weightObj.neighbors.keys())
            masterIDs.sort()
            for key in masterIDs:
                swmWriter.swm.writeEntry(key, weightObj.neighbors[key], \
                                         weightObj.weights[key])
            swmWriter.close()        
    
if __name__ == '__main__':
    setupParameters()
