EXTENSIONS = ["GAL", "GWT", "SWM"]

### imports related library ###
import arcpy as ARCPY
import pysal as PYSAL
import pysal2ArcUtils as AUTILS
import SSDataObject as SSDO
import SSUtilities as UTILS
import WeightsUtilities as WU

def setupParameters():
    """
    Basic idea is to get parameters from user input in the dialog,
    and execute associated weight matrix creating procedure
    based on user preference.
    """

    inputFile = ARCPY.GetParameterAsText(0)
    outputFile = ARCPY.GetParameterAsText(1)
    inputFC = UTILS.getTextParameter(2)
    inputIDField = UTILS.getTextParameter(3)

    inputExt = AUTILS.returnWeightFileType(inputFile)
    outputExt = AUTILS.returnWeightFileType(outputFile)
    weightObj = None
    fileIDField = None
    needFCandID = False


    if inputExt.upper() not in EXTENSIONS:
        msg = 'Input spatial weights file not supported! Please only use GAL, GWT and SWM files...'
        ARCPY.AddError(msg)
        raise SystemExit()
    else:
        fileIDField = AUTILS.getIDFieldFromWeights(inputFile)
        if not fileIDField:
            if (inputExt in [EXTENSIONS[1], EXTENSIONS[2]]) or AUTILS.isNewGalFormat(inputFile):
                msg = 'Unique ID Field is missing from the input spatial weights...'
                ARCPY.AddError(msg)
                raise SystemExit()
            else:
                msg = 'The input spatial weights file does not contain a unique ID Field. Please provide the spatial feature class and unique ID Field...'
                ARCPY.AddWarning(msg)
                needFCandID = True
        else:
            if inputExt == EXTENSIONS[1]:
                needFCandID = True

    if needFCandID and (not inputFC or not inputIDField):
        msg = 'The unique ID field and spatial feature class are necessary for conversion...'
        ARCPY.AddError(msg)
        raise SystemExit()

    ARCPY.SetProgressor("default", "Loading original spatial weights file...")

    weight2Master = None
    ssdo = None
    if inputIDField and inputFC:
        weight2Master = {}
	ssdo = SSDO.SSDataObject(inputFC)
        masterField = fileIDField
        if not fileIDField:
            masterField = UTILS.setUniqueIDField(ssdo)
        ssdo.obtainData(masterField, fields=[inputIDField])
        isGDB = (0 not in ssdo.master2Order)
        if isGDB and not fileIDField:
            for weightKey in ssdo.master2Order.keys():
                weight2Master[weightKey-1] = ssdo.fields[inputIDField].data[ssdo.master2Order[weightKey]]
        else:
            for weightKey in ssdo.master2Order.keys():
                weight2Master[weightKey] = ssdo.fields[inputIDField].data[ssdo.master2Order[weightKey]]

    if inputExt == EXTENSIONS[2]:
        weightObj = AUTILS.swm2Weights(inputFile, master2Order=weight2Master)
    else:
        weightObj = AUTILS.text2Weights(inputFile, master2Order=weight2Master)

    if not inputIDField:
        weightObj._varName = fileIDField
    else:
        weightObj._varName = inputIDField

    createWeightFile(outputFile, weightObj, ssdo)

def createWeightFile(outputFile, weightObj, ssdo, rowStandard = False):

    # Set progressor for visual
    ARCPY.SetProgressor("default", "Writing new spatial weights file as output...")
    outputExt = AUTILS.returnWeightFileType(outputFile)

    # manually write the gal format, otherwise, use default pysal weights writer
    if outputExt == EXTENSIONS[0]:
        outputWriter = open(outputFile, 'w')

        # write header in the first line
        line = str(0) + ' ' + str(len(weightObj.id_order)) + ' ' + weightObj._varName + ' ' + 'UNKNOWN\n'
        outputWriter.write(line)
        masterIDs = weightObj.neighbors.keys()
        masterIDs.sort()
        for id in masterIDs:
            neighbors = weightObj.neighbors[id]
            line = str(id) + ' ' + str(len(neighbors)) + '\n'
            outputWriter.write(line)
            if neighbors != None:
                line = ''
                for item in neighbors:
                    line += str(item)+' '
                if line != '':
                    line = line[:-1] + '\n'
                else:
                    line = '\n'
                outputWriter.write(line)
        outputWriter.close()
    elif outputExt == EXTENSIONS[1]:
        outputWriter = PYSAL.open(outputFile, 'w')
        outputWriter.varName = weightObj._varName
        outputWriter.write(weightObj)
        outputWriter.close()
    else:
        if ssdo:
            swmWriter = WU.SWMWriter(outputFile, weightObj._varName, ssdo.spatialRefName, weightObj.n, rowStandard)
        else:
            swmWriter = WU.SWMWriter(outputFile, weightObj._varName, '#', weightObj.n, rowStandard)
        masterIDs = weightObj.neighbors.keys()
        masterIDs.sort()
        for key in masterIDs:
            swmWriter.swm.writeEntry(key, weightObj.neighbors[key], weightObj.weights[key])
        swmWriter.close()

if __name__ == '__main__':
    setupParameters()
