'''
Created on 2011-9-23

The goal of this python script is to utilize the arcpy module,
to get access to the functionality of ArcGIS geoprocessing,
and serve as the functional basis of pysal weights plugin in ArcMap.

@author: Xing Kang
'''

EXTENSIONS = ['GAL', 'GWT', 'SWM']
### imports related library ###
import arcpy as ARCPY
import pysal as PYSAL
from pysal.weights.Distance import Kernel
import SSDataObject as SSDO
import SSUtilities as UTILS
import pysal2ArcUtils as AUTILS
import WeightsUtilities as WU

KERNELTYPE = ['UNIFORM', 'TRIANGULAR', 'QUADRATIC', 'QUARTIC', 'GAUSSIAN']
def setupParameters():
    """
    Basic idea is to get parameters from user input in the dialog,
    and execute associated weight matrix creating procedure
    based on user preference.
    """
    inputFC = ARCPY.GetParameterAsText(0)
    outputFile = ARCPY.GetParameterAsText(1)
    kernelType = ARCPY.GetParameterAsText(2).upper()
    neighborNum = UTILS.getNumericParameter(3)
    idField = UTILS.getTextParameter(4)

    if kernelType not in KERNELTYPE:
        ARCPY.AddError("Kernel type is not in the predefined list...")
        raise SystemExit()

    ARCPY.SetProgressor("default", "Loading features from dataset...")
    ssdo = SSDO.SSDataObject(inputFC)
    masterField = idField
    if not idField:
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

    ARCPY.SetProgressor("default", "Constructing spatial weights matrix...")
    dataArray = None
    weightObj = None
    if idField and AUTILS.returnWeightFileType(outputFile) != 'GAL':
        masterIDs = ssdo.master2Order.keys()
        masterIDs.sort()
        mapper = [ssdo.master2Order[id] for id in masterIDs]
        dataArray = ssdo.xyCoords[mapper]
        weightObj = Kernel(dataArray, fixed=False, k=neighborNum, function=kernelType, ids=masterIDs)
    else:
        dataArray = ssdo.xyCoords
        weightObj = Kernel(dataArray, fixed=False, k=neighborNum, function=kernelType)

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
