"""
Create Kernel-based Spatial Weights File.

Author(s): Xun Li, Xing Kang, Sergio Rey
"""

import arcpy as ARCPY
import pysal as PYSAL
import pysal.lib.io as FileIO
import pysal.lib.weights as WEIGHTS
import SSDataObject as SSDO
import SSUtilities as UTILS
import pysal2ArcUtils as AUTILS
import WeightsUtilities as WU

EXTENSIONS = ['KWT', 'SWM']
KERNELTYPE = ['UNIFORM', 'TRIANGULAR', 'QUADRATIC', 'QUARTIC', 'GAUSSIAN']

def setupParameters():
    """ Setup Parameters for Kernel-based Weights Creation """
    inputFC = ARCPY.GetParameterAsText(0)
    outputFile = ARCPY.GetParameterAsText(1)
    kernelType = ARCPY.GetParameterAsText(2).upper()
    neighborNum = UTILS.getNumericParameter(3)
    idField = UTILS.getTextParameter(4)

    if kernelType not in KERNELTYPE:
        ARCPY.AddError("Kernel type is not in the predefined list...")
        raise SystemExit()

    #### Run Kernel Weights Creation ####
    kernW = KernelW_PySAL(inputFC, outputFile, kernelType, neighborNum, idField)
    
    #### Create Output ####
    kernW.createOutput()
    
class KernelW_PySAL(object):
    """ Create Kernel-based Spatial Weights Using PySAL """
    
    def __init__(self, inputFC, outputFile, idField, kernelType, neighborNum):
        
        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Set Object for Weights Creation ####
        self.ssdo = None
        self.weightObj = None
        self.outputExt = AUTILS.returnWeightFileType(outputFile)
        
        #### Initialize Data ####
        self.initialize()

        #### Build Weights ####
        self.buildWeights()

    def initialize(self):       
        """Performs additional validation and populates the 
        SSDataObject."""
        ARCPY.SetProgressor("default", \
                            "Starting to create kernel-based weights. "
                            "Loading features...")
        
        #### Shorthand Attributes ####
        idField = self.idField
        inputFC = self.inputFC
        
        #### Create SSDataObject ####
        self.ssdo = SSDO.SSDataObject(inputFC)
        ssdo = self.ssdo
        
        #### Raise Error If Valid Unique ID Not Provided ####
        masterField = idField
        if not masterField:
            msg = ("The unique ID Field is required to create KWT and/or "
                   "SWM spatial weights files...")
            ARCPY.AddError(msg)
            raise SystemExit()
            
        #### Populate SSDO with Data ####
        ssdo.obtainData(masterField)

    def buildWeights(self):
        """Performs Distance-based Weights Creation"""
        ARCPY.SetProgressor("default", "Constructing spatial weights matrix...")
        
        #### Shorthand Attributes ####
        kernelType = self.kernelType
        neighborNum = self.neighborNum
        idField = self.idField
        outputExt = self.outputExt
        ssdo = self.ssdo
        
        #### Create Kernel-based WeightObj (0-based IDs) ####
        dataArray = ssdo.xyCoords
        masterIDs = range(ssdo.numObs)
        if idField: 
            masterIDs = [ssdo.order2Master[i] for i in masterIDs]
        weightObj = WEIGHTS.Kernel(dataArray, fixed=True, k=neighborNum, \
                                   function=kernelType, ids=masterIDs)
    
        #### Save weightObj Class Object for Writing Result #### 
        self.weightObj = weightObj 
    
    def createOutput(self, rowStandard = False):
        """ Write Kernel-based Weights to File. """
        ARCPY.SetProgressor("default", \
                            "Writing Spatial Weights to Output File...")
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo
        idField = self.idField
        weightObj = self.weightObj
        outputFile = self.outputFile
        outputExt = self.outputExt
        
        #### Get File Name Without Extension ####
        fileName = ssdo.inName.rsplit('.', 1)[0]
        
        if outputExt == EXTENSIONS[0]:
            # KWT file
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
