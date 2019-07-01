"""
Create Distance-based Spatial Weights File.

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

FEATURETYPE = ['POINT', 'MULTIPOINT', 'POLYGON']
DISTTYPE = ['THRESHOLD DISTANCE', 'K NEAREST NEIGHBORS', 'INVERSE DISTANCE']
EXTENSIONS = ['GAL', 'GWT', 'SWM']

def setupParameters():
    """ Setup Parameters for Distance-based Weights Creation """
    
    #### Get User Provided Inputs ####
    inputFC = ARCPY.GetParameterAsText(0)
    outputFile = ARCPY.GetParameterAsText(1)
    distanceType = UTILS.getTextParameter(2).upper() #
    idField = UTILS.getTextParameter(3)
    
    #### Validate Input of Distance Type ####
    if not distanceType or distanceType not in DISTTYPE:
        ARCPY.AddError("Distance type is not set, or it is not in the "
                       "predefined list...")
        raise SystemExit()

    #### Setup Default Values of Threshold/KnnNum/InverseDist ####
    threshold = UTILS.getNumericParameter(4) \
        if distanceType == DISTTYPE[0] or distanceType == DISTTYPE[2] else None
    knnNum = UTILS.getNumericParameter(5) \
        if distanceType == DISTTYPE[1] else None
    inverseDist = UTILS.getNumericParameter(6) \
        if distanceType == DISTTYPE[2] else None
    
    #### Run Dist Weights Creation ####
    distW = DistW_PySAL(inputFC, outputFile, idField, distanceType, threshold,\
                        knnNum, inverseDist)
    
    #### Create Output ####
    distW.createOutput()
    
class DistW_PySAL(object):
    """ Create Distant-based Spatial Weights Using PySAL """

    def __init__(self, inputFC, outputFile, idField, distanceType, threshold,\
                 knnNum, inverseDist):
        
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
                            "Starting to create distance-based weights. "
                            "Loading features...")
        
        #### Shorthand Attributes ####
        idField = self.idField
        inputFC= self.inputFC
        
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
        
        #### Raise Warning for POLYGON data ####
        if ssdo.shapeType == 'Polygon':
            ARCPY.AddWarning(("Input Shapefile contains polygon data. The "
                              "centroids of polygons would be used for "
                              "calculation..."))
            
    def buildWeights(self):
        """Performs Distance-based Weights Creation"""
        ARCPY.SetProgressor("default", "Constructing spatial weights object...")
        
        #### Shorthand Attributes ####
        distanceType = self.distanceType
        threshold = self.threshold
        knnNum = self.knnNum
        idField = self.idField
        outputExt = self.outputExt
        ssdo = self.ssdo
        
        #### Create Distance-based WeightObj (0-based IDs) ####
        dataArray = ssdo.xyCoords
        if distanceType.upper() == DISTTYPE[0]:
            weightObj = WEIGHTS.DistanceBand(dataArray, threshold)
        elif distanceType.upper() == DISTTYPE[1]:
            weightObj = WEIGHTS.KNN(dataArray, knnNum)
        elif distanceType.upper() == DISTTYPE[2]:
            alpha = -1 * self.inverseDist
            weightObj = WEIGHTS.DistanceBand(\
                dataArray, threshold, alpha=alpha)
          
        #### Re-Create WeightObj for NOT 0-based idField #### 
        if idField:
            if ssdo.master2Order.keys() != ssdo.master2Order.values(): 
                o2M = ssdo.order2Master
                neighborDict = {o2M[oid] : [o2M[nid] for nid in nbrs] \
                                for oid,nbrs in weightObj.neighbors.items()}
                weightDict = {o2M[oid] : weights \
                              for oid, weights in weightObj.weights.items()}
                weightObj = WEIGHTS.W(neighborDict, weightDict)
            
        #### Save weightObj Class Object for Writing Result #### 
        self.weightObj = weightObj

    def createOutput(self, rowStandard = False):
        """ Write Distance-based Weights to File. """
        
        ARCPY.SetProgressor("default", \
                            "Writing Spatial Weights to Output File...")
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo
        idField = self.idField
        weightObj = self.weightObj
        outputFile = self.outputFile
        outputExt = self.outputExt
    
        #### Get File Name Without Extension ####
        fileName = ssdo.inName.rsplit('.',1)[0]
        
        if outputExt == EXTENSIONS[0]:
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
                outputWriter.write("%s %s\n" % (id, len(neighbors)))
                outputWriter.write("%s\n" % \
                                   (" ".join([str(nbr) for nbr in neighbors])))
            outputWriter.close()
        elif outputExt == EXTENSIONS[1]:
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
