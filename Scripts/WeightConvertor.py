"""
Convert betwen different Spatial Weights File.

Author(s): Xun Li, Xing Kang, Sergio Rey
"""

import os
import arcpy as ARCPY
import pysal as PYSAL
import pysal2ArcUtils as AUTILS
import SSDataObject as SSDO
import SSUtilities as UTILS
import WeightsUtilities as WU

EXTENSIONS = ["GAL", "GWT", "KWT", "SWM"]

def setupParameters():
    """ Setup Parameters for Weights Convertion """
    
    #### Get User Provided Inputs ####
    inputFile = UTILS.getTextParameter(0)
    outputFile = UTILS.getTextParameter(1)
    inputFC = ARCPY.GetParameterAsText(2)
    inputIDField = UTILS.getTextParameter(3)
    
    #### Raise Error If Input Weights File is Not Valid ####  
    inputExt = AUTILS.returnWeightFileType(inputFile)
    if inputExt.upper() not in EXTENSIONS:
        msg = ("Input spatial weights file not supported! Please only use GAL, "
               "GWT, KWT and SWM files...")
        ARCPY.AddError(msg)
        raise SystemExit()
    
    #### Raise Error If Output Weights File is Not Valid ####  
    outputExt = AUTILS.returnWeightFileType(outputFile)
    if outputExt.upper() not in EXTENSIONS:
        msg = ("Output spatial weights file not supported! Please only use "
               "GAL, GWT, KWT and SWM files...")
        ARCPY.AddError(msg)
        raise SystemExit()
    
    #### Raise Error If Input Weights File is Empty ####
    if not os.path.isfile(inputFile) or os.path.getsize(inputFile) == 0:
        msg = ("Input spaital weights file is empty! Please use a valid "
               "weights file")
        ARCPY.AddError(msg)
        raise SystemExit()

    #### Copy if convert to same file formats ####
    if not inputFC and not inputIDField and inputExt == outputExt:
        from shutil import copyfile
        copyfile(inputFile, outputFile) 
        return
     
    #### Run Weights Convertor ####
    wConvertor = WeightConvertor(inputFile, outputFile, inputFC, inputIDField,\
                                 inputExt, outputExt)
    
    #### Create New Weights File ####    
    wConvertor.createOutput()

class WeightConvertor(object):
    """ Convert Between Different Weights """
    
    def __init__(self, inputFile, outputFile, inputFC, inputIDField, \
                 inputExt, outputExt):
        
        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())

        #### Set Object for Weights Creation ####
        self.ssdo = None
        self.weightObj = None
        self.needFCandID = False
        self.fileIDField = None
        
        #### Initialize Data ####
        self.initialize()

        #### Convert Weights ####
        self.loadWeights()
        
    def initialize(self):
        """Performs additional validation and populates the 
        SSDataObject."""
        ARCPY.SetProgressor("default", \
                            "Starting to create kernel-based weights. "
                            "Loading features...")
        
        #### Shorthand Attributes ####
        inputFile = self.inputFile
        inputExt = self.inputExt
        inputFC = self.inputFC
        inputIDField = self.inputIDField
        
        needFCandID = False
        
        #### Get IDField From Input Weights File ####
        fileIDField = AUTILS.getIDFieldFromWeights(inputFile)
        
        #### Raise Error/Warning If Proper ID Field Is NOT Provided ####
        if inputExt == EXTENSIONS[0]:
            # GAL
            needFCandID = False
            if not fileIDField:            
                #msg = "The input spatial weights file does not contain a "\
                #    "unique ID Field. Please provide the spatial feature "\
                #    "class and unique ID Field..."
                #ARCPY.AddWarning(msg)
                needFCandID = True
                
        elif inputExt == EXTENSIONS[1] or inputExt == EXTENSIONS[2]:
            # GWT, KWT
            needFCandID = False
            if not fileIDField:
                msg = ("Unique ID Field is missing from the input spatial "
                       "weights...")
                ARCPY.AddError(msg)
                raise SystemExit()
            
        elif inputExt == EXTENSIONS[3]:
            # SWM
            needFCandID = False
            if not fileIDField:
                msg = ("Unique ID Field is missing from the input spatial "
                       "weights...")
                ARCPY.AddError(msg)
                raise SystemExit()
    
        #### Raise Error If FC and IDField are Required but Not Provided ####
        if needFCandID and (not inputFC or not inputIDField):
            msg = ("The unique ID field and spatial feature class are "
                   "necessary for weights conversion...")
            ARCPY.AddError(msg)
            raise SystemExit()
    
        self.fileIDField = fileIDField
    
    def loadWeights(self):
        """ Convert Weights by Reading From Input Weights File """
        
        ARCPY.SetProgressor("default", \
                            "Loading original spatial weights file...")
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo
        weightObj = self.weightObj
        inputFC = self.inputFC
        inputExt = self.inputExt
        inputFile = self.inputFile
        inputIDField = self.inputIDField
        fileIDField = self.fileIDField
        
        weight2Master = None
        
        #### If FC and IDField are Required and Provided ####
        if inputIDField and inputFC:
            ssdo = SSDO.SSDataObject(inputFC)
            masterField = fileIDField if fileIDField else \
                UTILS.setUniqueIDField(ssdo) # 0-based Weights
            ssdo.obtainData(masterField, fields=[inputIDField])
            
            # Create Mapping From Weights IDs to Master IDs
            weight2Master = {}
            isGDB = (0 not in ssdo.master2Order)
            for weightKey in ssdo.master2Order.keys():
                weight2Master[weightKey-1 if isGDB and not fileIDField \
                              else weightKey] = \
                    ssdo.fields[inputIDField].data[ssdo.master2Order[weightKey]]

        #### Create WeightObj from Input File ####    
        weightObj = AUTILS.swm2Weights(inputFile, master2Order=weight2Master) \
            if inputExt == EXTENSIONS[3] else \
            AUTILS.text2Weights(inputFile, master2Order=weight2Master)
    
        #### Save weightObj Class Object for Writing Result #### 
        self.weightObj = weightObj
    
    def createOutput(self, rowStandard = False):
        """ Write New Weights File. """
        
        ARCPY.SetProgressor("default", \
                            "Writing new spatial weights file as output...")
        
        #### Shorthand Attributes ####
        ssdo = self.ssdo
        weightObj = self.weightObj
        inputIDField = self.inputIDField
        outputFile = self.outputFile
        outputExt = self.outputExt

        #### Write WeightObj to New Weights File ####
        uniqueID = weightObj._varName 
        if not uniqueID:
            uniqueID = inputIDField
            
        if outputExt == EXTENSIONS[0]:
            # GAL file
            outputWriter = open(outputFile, 'w')
            header = "%s %s %s %s\n" % \
                (0, weightObj.n, uniqueID, 'UNKNOWN')
            outputWriter.write(header)
            masterIDs = list(weightObj.neighbors.keys())
            masterIDs.sort()
            for id in masterIDs:
                neighbors = weightObj.neighbors[id]
                outputWriter.write("%s %s\n" % (id, len(neighbors)))
                outputWriter.write("%s\n" % \
                                   (" ".join([str(nbr) for nbr in neighbors])))
            outputWriter.close()
        elif outputExt == EXTENSIONS[1] or outputExt == EXTENSIONS[2]:
            # GWT, KWT
            outputWriter = PYSAL.open(outputFile, 'w')
            outputWriter.varName = uniqueID
            outputWriter.write(weightObj)
            outputWriter.close()
        else:
            # SWM
            swmWriter = WU.SWMWriter(outputFile, uniqueID, \
                                     ssdo.spatialRefName if ssdo else '#', \
                                     weightObj.n, rowStandard)
            masterIDs = list(weightObj.neighbors.keys())
            masterIDs.sort()
            for key in masterIDs:
                swmWriter.swm.writeEntry(key, weightObj.neighbors[key], \
                                         weightObj.weights[key])
            swmWriter.close()
    
if __name__ == '__main__':
    setupParameters()
