"""Converts Spatial Weights Files Formats.

Author(s): Mark Janikas, Xing Kang, Sergio Rey
"""

import arcpy as ARCPY
import pysal as PYSAL
from pysal.weights import W
import SSUtilities as UTILS
import SSDataObject as SSDO
import pysal2ArcUtils as AUTILS
import WeightsUtilities as WU

EXTENSIONS = ['GAL', 'GWT', 'SWM']
WEIGHTTYPE = ['ROOK', 'QUEEN']

def setupParameters():
    """
    Basic idea is to get parameters from user input in the dialog,
    and execute associated weight matrix creating procedure
    based on user preference.
    """
    ### setup parameter info ###
    inputFC = ARCPY.GetParameterAsText(0)
    outputFile = ARCPY.GetParameterAsText(1)
    idField = UTILS.getTextParameter(2)
    weightType = UTILS.getTextParameter(3)
    weightOrder = UTILS.getNumericParameter(4)
    isLowOrder = ARCPY.GetParameter(5)

    if weightType:
        weightType = weightType.upper()
    if not weightType or weightType not in WEIGHTTYPE:
        ARCPY.AddError("Weights type can only be Rook or Queen...")
        raise SystemExit()

    ARCPY.SetProgressor("default", "Starting to create contiguity-based weights. Loading features...")
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
    master2Order = ssdo.master2Order
    polyNeighborDict = WU.polygonNeighborDict(inputFC, masterField, contiguityType=weightType)
    # assign empty list to deal with polygons without neighbors
    for masterKey in master2Order.keys():
        if not polyNeighborDict.has_key(masterKey):
            polyNeighborDict[masterKey] = []
    if not idField:
        polyNeighborCopy = {}
        for key in polyNeighborDict.keys():
            polyNeighborCopy[master2Order[key]] = []
            for item in polyNeighborDict[key]:
                polyNeighborCopy[master2Order[key]].append(master2Order[item])
        polyNeighborDict = polyNeighborCopy
    weightObj = W(polyNeighborDict)
    if idField:
        weightObj._varName = idField

    ARCPY.SetProgressor("default", "Building up Lower Order Spatial Weights...")
    # For higher orders, call pysal.higher_order func
    # use set operations to union all orders if lower order included
    if weightOrder > 1:
        origWeight = weightObj
        weightObj = PYSAL.higher_order(weightObj, weightOrder)
        if isLowOrder:
            for order in xrange(weightOrder-1, 1, -1):
                lowOrderW = PYSAL.higher_order(origWeight, order)
                weightObj = PYSAL.w_union(weightObj, lowOrderW)
            weightObj = PYSAL.w_union(weightObj, origWeight)

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
