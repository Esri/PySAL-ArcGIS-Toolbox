'''
Created on 2011-9-23

The goal of this python script is to utilize the arcpy module,
to get access to the functionality of ArcGIS geoprocessing,
and serve as the functional basis of pysal weights plugin in ArcMap.

@author: Xing Kang
'''

FEATURETYPE = ['POINT', 'MULTIPOINT', 'POLYGON']
DISTTYPE = ['THRESHOLD DISTANCE', 'K NEAREST NEIGHBORS', 'INVERSE DISTANCE']
EXTENSIONS = ['GAL', 'GWT', 'SWM']
### imports related library ###
import arcpy as ARCPY
import pysal as PYSAL
from pysal.weights import W
import SSDataObject as SSDO
import SSUtilities as UTILS
import pysal2ArcUtils as AUTILS
import WeightsUtilities as WU

def setupParameters():
    """
    Basic idea is to get parameters from user input in the dialog,
    and execute associated weight matrix creating procedure
    based on user preference.
    """

    inputFC = ARCPY.GetParameterAsText(0)
    outputFile = ARCPY.GetParameterAsText(1)
    distanceType = UTILS.getTextParameter(2)
    idField = UTILS.getTextParameter(3)

    if distanceType:
        distanceType = distanceType.upper()
    if not distanceType or distanceType not in DISTTYPE:
        ARCPY.AddError("Distance type is not set, or it is not in the predefined list...")
        raise SystemExit()

    threshold = None
    knnNum = None
    inverseDist = None
    if distanceType == DISTTYPE[0]:
        threshold = UTILS.getNumericParameter(4)
    elif distanceType == DISTTYPE[1]:
        knnNum = UTILS.getNumericParameter(5)
    elif distanceType == DISTTYPE[2]:
        threshold = UTILS.getNumericParameter(4)
        inverseDist = UTILS.getNumericParameter(6)

    ARCPY.SetProgressor("default", "Starting to create distance-based weights. Loading features...")
    weightObj = None
    ssdo = SSDO.SSDataObject(inputFC)
    if idField:
        masterField = idField.upper()
    else:
        outputExt = AUTILS.returnWeightFileType(outputFile)
        if outputExt != EXTENSIONS[0]:
            msg = 'The unique ID Field is required to create GWT and/or SWM spatial weights files...'
            ARCPY.AddError(msg)
            raise SystemExit()
        else:
            msg = 'The unique ID Field is not provided. The zero-based indexing order will be used to create the spatial weights file.'
            ARCPY.AddWarning(msg)
            masterField = UTILS.setUniqueIDField(ssdo)
    ssdo.obtainData(masterField)
    if ssdo.shapeType == 'Polygon':
        ARCPY.AddWarning("Input shapefile contains polygon data. The centroids of polygons would be used for calculation...")

    dataArray = []
    order2Master = {}
    if idField and AUTILS.returnWeightFileType(outputFile) != 'GAL':
        masterIDs = ssdo.master2Order.keys()
        for id in masterIDs:
            oid = ssdo.master2Order[id]
            order2Master[oid] = id
    dataArray = ssdo.xyCoords

    ARCPY.SetProgressor("default", "Constructing spatial weights object...")
    if distanceType == DISTTYPE[0]:
        weightObj = PYSAL.threshold_binaryW_from_array(dataArray, threshold)
    elif distanceType == DISTTYPE[1]:
        weightObj = PYSAL.knnW_from_array(dataArray, knnNum)
    elif distanceType == DISTTYPE[2]:
        weightObj = PYSAL.threshold_continuousW_from_array(dataArray, threshold, alpha=-1*inverseDist)
    if idField and AUTILS.returnWeightFileType(outputFile) != 'GAL':
        neighborDict = {}
        weightDict = {}
        for oid in order2Master.keys():
            if weightObj.neighbors.has_key(oid):
                curMasterID = order2Master[oid]
                neighborDict[curMasterID] = []
                if weightObj.neighbors[oid]:
                    for neighborOID in weightObj.neighbors[oid]:
                        neighborDict[curMasterID].append(order2Master[neighborOID])
                weightDict[curMasterID] = weightObj.weights[oid]
        weightObj = W(neighborDict, weightDict)
    if idField:
        weightObj._varName = idField
    createWeightFile(outputFile, weightObj, ssdo, setVarName=(idField != None))

def createWeightFile(outputFile, weightObj, ssdo, setVarName=False, rowStandard = False):
    ARCPY.SetProgressor("default", "Writing Spatial Weights to Output File...")
    ext = AUTILS.returnWeightFileType(outputFile)

    if ext == EXTENSIONS[0] and setVarName:
        outputWriter = open(outputFile, 'w')

        # write header in the first line
        line = [str(0), str(len(weightObj.id_order)), weightObj._varName, 'UNKNOWN\n']
        line = " ".join(line)
        outputWriter.write(line)
        masterIDs = weightObj.neighbors.keys()
        masterIDs.sort()
        for id in masterIDs:
            neighbors = weightObj.neighbors[id]
            line = [str(id), str(len(neighbors))]
            line = " ".join(line) + "\n"
            outputWriter.write(line)
            if neighbors != None:
                line = ''
                contents = []
                for item in neighbors:
                    contents.append(str(item))
                if contents:
                    line = " ".join(contents)
                line += "\n"
                outputWriter.write(line)
        outputWriter.close()
    else:
        if ext != EXTENSIONS[2]:
            outputWriter = PYSAL.open(outputFile, 'w')
            if setVarName:
                outputWriter.varName = weightObj._varName
            outputWriter.write(weightObj)
            outputWriter.close()
        else:
            if setVarName:
                masterField = weightObj._varName
            else:
                masterField = 'UNKNOWN'
            swmWriter = WU.SWMWriter(outputFile, masterField, ssdo.spatialRefName, weightObj.n, rowStandard)
            masterIDs = weightObj.neighbors.keys()
            masterIDs.sort()
            for key in masterIDs:
                swmWriter.swm.writeEntry(key, weightObj.neighbors[key], weightObj.weights[key])
            swmWriter.close()

if __name__ == '__main__':
    setupParameters()
