import os as OS
import numpy as NUM
import ErrorUtils as ERROR
import arcpy as ARCPY
import SSDataObject as SSDO
import SSUtilities as UTILS
import WeightsUtilities as WU
import locale as LOCALE
from pysal.weights import W

class PAT_W(object):
    """Wrapper Class for adding attributes to PySAL W for toolkit"""

    def __init__(self, ssdo, weightsFile):
        #### Set Initial Attributes ####
        UTILS.assignClassAttr(self, locals())
        self.wPath, self.wName = OS.path.split(weightsFile)
        name, ext = OS.path.splitext(weightsFile.upper())
        self.wExt = ext.strip(".")
        self.setWeights()
        
    def setWeights(self):

        if self.wExt == "SWM":
            self.w = swm2Weights(self.weightsFile, self.ssdo.master2Order)
        else:
            self.w = text2Weights(self.weightsFile, 
                                 master2Order = self.ssdo.master2Order)

def returnWeightFileType(weightsFile):
    name, ext = OS.path.splitext(weightsFile.upper())
    if not ext:
        return None
    return ext.strip(".")

def isNewGalFormat(weightsFile):
    ext = returnWeightFileType(weightsFile)
    if ext == "GAL":
        weightFile = open(weightsFile, 'r')
        info = weightFile.readline().strip().split()
        if len(info) > 1:
            return True
    return False

def getIDFieldFromWeights(weightsFile):
    weightType = returnWeightFileType(weightsFile)
    if weightType == 'GAL':
        weightFile = open(weightsFile, 'r')
        info = weightFile.readline().strip().split()
        if len(info) > 1:
            # new format gal, read associated field name
            if info[2] != 'UNKNOWN':
                return info[2]
        return None
    elif weightType == 'SWM':
        swm = WU.SWMReader(weightsFile)
        if not swm.masterField or swm.masterField == 'UNKNOWN':
            return None
        return swm.masterField
    else:
        gwtFile = open(weightsFile, 'r')
        info = gwtFile.readline().strip().split()
        if info[-1] == 'UNKNOWN':
            return None
        return info[-1]

def getFeatNumFromWeights(weightsFile):
    weightType = returnWeightFileType(weightsFile)
    if weightType in ['GAL', 'GWT']:
        weightFile = open(weightsFile, 'r')
        info = weightFile.readline().strip().split()
        if weightType == 'GAL':
            if len(info) == 1:
                return LOCALE.atoi(info[0])
            elif len(info) > 1:
                return LOCALE.atoi(info[1])
        else:
            return LOCALE.atoi(info[1])
    elif weightType == 'SWM':
        swm = WU.SWMReader(weightsFile)
        return swm.numObs


def swm2Weights(swmFile, master2Order):
    swm = WU.SWMReader(swmFile)
    numObs = swm.numObs
    if len(master2Order) < numObs: 
        msg = "The spatial attributes have fewer entries than spatial weights! Weights will be adjusted dynamically..."
        ARCPY.AddWarning(msg)
        adjust = True
    else:
        adjust = False

    neighs = {}
    w = {}
    rowStandard = swm.rowStandard
    for i in xrange(numObs):
        info = swm.swm.readEntry()
        masterID, nn, nhsTemp, weightsTemp, sumUnstandard = info
        
        if master2Order.has_key(masterID):
            orderID = master2Order[masterID]
            if not adjust:
                if nn:
                    nhIDs = [ master2Order[nh] for nh in nhsTemp ]
                weights = weightsTemp
            else:
                #### Empty Result Structures ####
                nhIDs = []
                weights = []

                #### Restandardize Due to Subset/Select ####
                if nn:
                    for i in xrange(nn):
                        nh = nhsTemp[i]
                        if master2Order.has_key(nh):
                            nhOrder = master2Order[nh]
                            nhIDs.append(nhOrder)
                            nhWeight = weightsTemp[i]
                            if rowStandard:
                                #### Unstandardize if Necessary ####
                                nhWeight = nhWeight * sumUnstandard[0]
                            weights.append(nhWeight)

                #### Re-Standardize ####
                nn = len(nhIDs)
                if nn:
                    weights = NUM.array(weights)
                    if rowStandard:
                        weights = (1.0 / weights.sum()) * weights

            #### Add To Dict Structures ####
            neighs[orderID] = nhIDs
            w[orderID] = weights

    swm.close()
    return W(neighs, w)

def text2Weights(weightsFile, master2Order = None):

    numObs = getFeatNumFromWeights(weightsFile)
    if len(master2Order) < numObs: 
        msg = "The spatial attributes have fewer entries than spatial weights! Weights will be adjusted dynamically..."
        ARCPY.AddWarning(msg)
        adjust = True
    else:
        adjust = False

    fi = open(weightsFile, "r")
    info = fi.readline()
    neighDict = {}
    weightDict = {}
    orderID = None
    inType = OS.path.splitext(weightsFile)[-1].upper()
    if inType == ".GAL":
        inRecord = False
        for line in fi:
            if inRecord:
                if orderID != None:
                    if not adjust:
                        try:
                            if master2Order:
                                neighs = [ int(master2Order[int(i)]) for i in line.strip().split() ]
                            else:
                                neighs = [ int(i) for i in line.strip().split() ]
                            neighDict[orderID] = neighs
                            weightDict[orderID] = [1. for i in neighs]
                        except:
                            msg = "A unique ID entry was not found in the spatial dataset! Invalid GAL file..."
                            ARCPY.AddError(msg)
                            raise SystemExit()
                    else:
                        neighDict[orderID] = []
                        weightDict[orderID] = []
                        neighMasterIDs = [int(i) for i in line.strip().split()]
                        for seqID in xrange(len(neighMasterIDs)):
                            curMasterID = neighMasterIDs[seqID]
                            if master2Order.has_key(curMasterID):
                                neighDict[orderID].append(master2Order[curMasterID])
                                weightDict[orderID].append(1.)
                        if len(weightDict[orderID]) > 0:
                            weightArray = 1.0 * NUM.array(weightDict[orderID]) / len(weightDict[orderID])
                            weightDict[orderID] = weightArray.tolist()
                inRecord = False
            else:
                masterID, nn = [ int(i) for i in line.strip().split() ]
                orderID = None
                if not adjust:
                    #### Unpack and Check Format ####
                    try:
                        if master2Order:
                            orderID = int(master2Order[masterID])
                        else:
                            orderID = masterID
                    except:
                        msg = "A unique Master ID entry was not found in the spatial dataset! Invaid GAL File..."
                        ARCPY.AddError(msg)
                        raise SystemExit()
                else:
                    if master2Order.has_key(masterID):
                        orderID = int(master2Order[masterID])
                    #### Check Unique ID ####
                    if orderID and neighDict.has_key(orderID):
                        ARCPY.AddIDMessage("Error", 644, "UNIQUE_ID")
                        ARCPY.AddIDMessage("Error", 643)
                        raise SystemExit()
                inRecord = True
    else:
        for line in fi:
            masterID, nid, weight = line.strip().split()
            if not adjust:
                #### Unpack and Check Format ####
                try:
                    if master2Order:
                        orderID = int(master2Order[int(masterID)])
                        neighID = int(master2Order[int(nid)])
                    else:
                        orderID = int(masterID)
                        neighID = int(nid)
                except:
                    msg = "A unique Master ID entry was not found in the spatial dataset! Invalid GWT File..."
                    ARCPY.AddError(msg)
                    raise SystemExit()

                #### Process Intersection in Weights Matrix ####
                if not neighDict.has_key(orderID):
                    neighDict[orderID] = []
                    weightDict[orderID] = []
                try:
                    neighDict[orderID].append( neighID )
                    weightDict[orderID].append( LOCALE.atof(weight) )
                except:
                    msg = "Parsing error encountered while creating spatial weights object..."
                    ARCPY.AddError(msg)
                    raise SystemExit()
            else:
                if master2Order.has_key(int(masterID)):
                    orderID = int(master2Order[int(masterID)])
                    if not neighDict.has_key(orderID):
                        neighDict[orderID] = []
                        weightDict[orderID] = []
                    if master2Order.has_key(int(nid)):
                        orderNID = int(master2Order[int(nid)])
                        neighDict[orderID].append(orderNID)
                        weightDict[orderID].append(LOCALE.atof(weight))
        # restandardization
        if adjust:
            for orderID in weightDict.keys():
                if len(weightDict[orderID]) > 0:
                    sumWeight = 0.0
                    for item in weightDict[orderID]:
                        sumWeight += item
                    weightArray = 1.0 * NUM.array(weightDict[orderID]) / sumWeight
                    weightDict[orderID] = weightArray.tolist()
    fi.close()
    if returnWeightFileType(weightsFile) == 'GWT' and master2Order:
        for neighKey in master2Order.keys():
            orderID = int(master2Order[int(neighKey)])
            if not neighDict.has_key(orderID):
                neighDict[orderID] = []
                weightDict[orderID] = []

    return W(neighDict, weightDict)
