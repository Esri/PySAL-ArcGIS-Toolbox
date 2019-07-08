"""
Author(s): Luc Anselin, Sergio Rey, Xun Li
"""
import os as OS
import numpy as NUM
import ErrorUtils as ERROR
import arcpy as ARCPY
import SSDataObject as SSDO
import SSUtilities as UTILS
import WeightsUtilities as WU
import locale as LOCALE
import pysal as PYSAL
from pysal.lib.weights import W

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

def setUniqueIDField(ssdo, weightsFile):
    """Replace SSUTILITIES.setUniqueIDField to support flexible weights file 
    headers."""
    if weightsFile == None:
        return ssdo.oidName
    
    weightsSuffix = weightsFile.split(".")[-1].lower()
    swmFileBool = (weightsSuffix == "swm")
    
    if swmFileBool:
        return UTILS.setUniqueIDField(ssdo, weightsFile)
    
    fo = UTILS.openFile(weightsFile, "r")
    header = fo.readline().strip()
    headerItems = header.split(" ") 
    
    if len(headerItems) == 1 and weightsSuffix == "gal":
        return ssdo.oidName
    
    elif len(headerItems) > 1:
        for item in headerItems:
            if not item.isdigit() and item.lower() != "unknown" \
               and len(item) > 0:
                masterField = item
                # check to see if in ssdo
                for fieldName, fieldObj in ssdo.allFields.items():
                    if fieldObj.baseName.upper() == masterField.upper():
                        return masterField
                    
    msg = "Header is not valid in Weights file (%s)." % weightsFile
    ARCPY.AddWarning(msg)
             
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
            return False
    return True

def getIDFieldFromWeights(weightsFile):
    weightType = returnWeightFileType(weightsFile)
    if weightType == 'SWM':
        swm = WU.SWMReader(weightsFile)
        if not swm.masterField or swm.masterField == 'UNKNOWN':
            return None
        return swm.masterField
    else:
        weightFile = open(weightsFile, 'r')
        info = weightFile.readline().strip().split()
        weightFile.close()
        for item in info:
            if not item.isdigit() and item.lower() != "unknown" \
               and len(item) > 0:
                return item
        return None

def getFeatNumFromWeights(weightsFile):
    weightType = returnWeightFileType(weightsFile)
    if weightType in ['GAL', 'GWT', 'KWT']:
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


def swm2Weights(swmFile, master2Order=None):
    swm = WU.SWMReader(swmFile)
    numObs = swm.numObs
    adjust = False
    
    if master2Order and len(master2Order) < numObs: 
        msg = ("The spatial attributes have fewer entries than spatial" 
               "weights! Weights will be adjusted dynamically...")
        ARCPY.AddWarning(msg)
        adjust = True

    neighs = {}
    w = {}
    rowStandard = swm.rowStandard
    for i in range(numObs):
        masterID, nn, nhsTemp, weightsTemp, sumUnstandard = swm.swm.readEntry()
        if master2Order == None:
            # no need adjust when convert directly from weights content
            orderID = masterID
            nhIDs = nhsTemp
            weights = weightsTemp
            
        elif masterID in master2Order:
            orderID = master2Order[masterID]         
            if not adjust:
                nhIDs = [ master2Order[nh] for nh in nhsTemp ]
                weights = weightsTemp
            else:
                # Restandardize Due to Subset/Select
                nhIDs = []
                weights = []            
                if nn:
                    for i in range(nn):
                        nh = nhsTemp[i]
                        if nh in master2Order:
                            nhOrder = master2Order[nh]
                            nhIDs.append(nhOrder)
                            nhWeight = weightsTemp[i]
                            if rowStandard:
                                # Unstandardize if Necessary
                                nhWeight = nhWeight * sumUnstandard[0]
                            weights.append(nhWeight)            
    
                # Re-Standardize
                if nhIDs:
                    weights = NUM.array(weights)
                    if rowStandard:
                        weights = (1.0 / weights.sum()) * weights
    
        # Add To Dict Structures
        neighs[orderID] = nhIDs
        w[orderID] = weights

    swm.close()
    wobj = W(neighs, w)
    wobj._varName = swm.masterField
    return wojb

def text2Weights(weightsFile, master2Order = None):

    adjust = False
    numObs = getFeatNumFromWeights(weightsFile)
    if master2Order:
        if len(master2Order) < numObs: 
            msg = ("The spatial attributes have fewer entries than spatial "
                   "weights! Weights will be adjusted dynamically...")
            ARCPY.AddWarning(msg)
            adjust = True

    uid = None
    neighDict = {}
    weightDict = {}
    orderID = None
    inType = OS.path.splitext(weightsFile)[-1].upper()
    
    fi = open(weightsFile, "r")
    info = fi.readline().strip()
    for item in info.split(" "):
        if not item.isdigit() and item.lower() != "unknown" \
           and len(item) > 0:
            uid = item
            break
    if uid == None:
        msg = ("A unique ID entry was not found in the weights file. Please "
               "check the weights file.")
        ARCPY.AddError(msg)
        raise SystemExit()
        
    if inType == ".GAL":
        # read 2 lines at a time
        line = fi.readline()
        while line:
            # read line for id and #neighbors
            masterID, nn = [int(i) for i in line.strip().split()]
            orderID = None
            if not adjust:
                try:
                    if master2Order:
                        orderID = master2Order[masterID]
                    else:
                        orderID = masterID
                except:
                    msg = ("A unique Master ID entry was not found in the "
                           "spatial dataset! Invaid GAL File...")
                    ARCPY.AddError(msg)
                    raise SystemExit()
            else:
                if masterID in master2Order:
                    orderID = int(master2Order[masterID])
                #### Check Unique ID ####
                if orderID in neighDict:
                    ARCPY.AddIDMessage("Error", 644, "UNIQUE_ID")
                    ARCPY.AddIDMessage("Error", 643)
                    raise SystemExit()
            
            # read next line for neighbor ids
            line = fi.readline()
            if orderID is not None:
                neighIDs = [int(i) for i in line.strip().split()]
                if not adjust:
                    try:
                        if master2Order:
                            neighs = [master2Order[i] for i in neighIDs]
                        else:
                            neighs = neighIDs
                        neighDict[orderID] = neighs
                        weightDict[orderID] = [1. for i in neighs] 
                    except:
                        msg = ("A unique ID entry" + uid + " was not found in the "
                               "spatial dataset! Invalid GAL file...")
                        ARCPY.AddError(msg)
                        raise SystemExit()
                else:
                    neighDict[orderID] = []
                    weightDict[orderID] = []
                           
                    for curMasterID in neighIDs:
                        if curMasterID in master2Order:
                            neighDict[orderID].append(master2Order[curMasterID])
                            weightDict[orderID].append(1.)
                           
                    weightArray = NUM.array(weightDict[orderID]) 
                    if len(weightArray) > 0:
                        weightArray = 1.0 * weightArray / len(weightArray)
                        weightDict[orderID] = weightArray.tolist()
                    
            line = fi.readline()
            
    # inType not GAL
    else:
        for line in fi:
            masterID, nid, weight = line.strip().split()
            masterID = int(masterID)
            nid = int(nid)
            
            if not adjust:
                try:
                    if master2Order:
                        orderID = master2Order[masterID] 
                        neighID = master2Order[nid] 
                    else:
                        orderID = masterID 
                        neighID = nid
                except:
                    msg = ("A unique Master ID entry was not found in the "
                           "spatial dataset! Invalid GWT File...")
                    ARCPY.AddError(msg)
                    raise SystemExit()

                #### Process Intersection in Weights Matrix ####
                if orderID not in neighDict:
                    neighDict[orderID] = []
                    weightDict[orderID] = []
                try:
                    neighDict[orderID].append( neighID )
                    weightDict[orderID].append( LOCALE.atof(weight) )
                except:
                    msg = ("Parsing error encountered while creating spatial "
                           "weights object...")
                    ARCPY.AddError(msg)
                    raise SystemExit()
            else:
                if masterID in master2Order:
                    orderID = master2Order[masterID]
                    if orderID not in neighDict:
                        neighDict[orderID] = []
                        weightDict[orderID] = []
                    if nid in master2Order:
                        orderNID = master2Order[nid]
                        neighDict[orderID].append(orderNID)
                        weightDict[orderID].append(LOCALE.atof(weight))
        # restandardization
        if adjust:
            for orderID in weightDict.keys():
                if len(weightDict[orderID]) > 0:
                    sumWeight = 0.0
                    for item in weightDict[orderID]:
                        sumWeight += item
                    weightArray = 1.0 * NUM.array(weightDict[orderID])/sumWeight
                    weightDict[orderID] = weightArray.tolist()
    fi.close()
    if returnWeightFileType(weightsFile) == 'GWT' and master2Order:
        for neighKey in master2Order.keys():
            orderID = int(master2Order[int(neighKey)])
            if orderID not in neighDict:
                neighDict[orderID] = []
                weightDict[orderID] = []

    w = W(neighDict, weightDict)
    if inType == ".GAL":
        w.transform = 'r'

    w._varName = uid
    return w

def lmChoice(result, criticalValue):
    """Makes choice of aspatial/spatial model based on LeGrange Multiplier
    stats from an OLS result.

    INPUTS:
    result (object): instance of PySAL OLS Model with spatial weights given.
    criticalValue (float): significance value

    RETURN:
    category (str): ['MIXED', 'LAG', 'ERROR', 'OLS']
    """

    sigError = result.lm_error[1] < criticalValue
    sigLag = result.lm_lag[1] < criticalValue
    sigBoth = sigError and sigLag
    if sigLag or sigError:
        sigErrorRob = result.rlm_error[1] < criticalValue
        sigLagRob = result.rlm_lag[1] < criticalValue
        sigBothRob = sigErrorRob and sigLagRob
        if sigBothRob:
            return "MIXED"
        else:
            if sigLagRob:
                return "LAG"
            if sigErrorRob:
                return "ERROR"
            if sigBoth:
                return "MIXED"
            else:
                if sigLag:
                    return "LAG"
                return "ERROR"
    else:
        return "OLS"

def autospace(y,x,w,gwk,opvalue=0.01,combo=False,name_y=None,name_x=None,
              name_w=None,name_gwk=None,name_ds=None):
    """
    Runs automatic spatial regression using decision tree
    
    Accounts for both heteroskedasticity and spatial autocorrelation
    
    No endogenous variables
    
    Parameters
    ----------
    y            : array
                   nx1 array for dependent variable
    x            : array
                   Two dimensional array with n rows and one column for each
                   independent (exogenous) variable, excluding the constant
    w            : pysal W object
                   Spatial weights object 
    gwk          : pysal W object
                   Kernel spatial weights needed for HAC estimation. Note:
                   matrix must have ones along the main diagonal.
    opvalue      : real
                   p-value to be used in tests; default: opvalue = 0.01
    combo        : boolean
                   flag for use of combo model rather than HAC for lag-error
                   model; default: combo = False
                   
    Returns
    -------
    results      : a dictionary with
                   results['final model']: one of
                        No Space - Homoskedastic
                        No Space - Heteroskedastic
                        Spatial Lag - Homoskedastic
                        Spatial Lag - Heteroskedastic
                        Spatial Error - Homoskedastic
                        Spatial Error - Heteroskedastic
                        Spatial Lag with Spatial Error - HAC
                        Spatial Lag with Spatial Error - Homoskedastic
                        Spatial Lag with Spatial Error - Heteroskedastic
                        Robust Tests not Significant - Check Model
                   results['heteroskedasticity']: True or False
                   results['spatial lag']: True or False
                   results['spatial error']: True or False
                   results['regression1']: regression object with base model (OLS)
                   results['regression2']: regression object with final model
    """
    results = {}
    results['spatial error']=False
    results['spatial lag']=False
    r1 = PYSAL.model.spreg.OLS(y,x,w=w,gwk=gwk,spat_diag=True,
                               name_y=name_y,name_x=name_x,
                               name_w=name_w,name_gwk=name_gwk,
                               name_ds=name_ds)
    results['regression1'] = r1
    Het = r1.koenker_bassett['pvalue']
    if Het < opvalue:
        Hetflag = True
    else:
        Hetflag = False
    results['heteroskedasticity'] = Hetflag
    model = lmChoice(r1, opvalue)
    if model == "MIXED":
        if not combo:
            r2 = PYSAL.model.spreg.GM_Lag(y,x,w=w,gwk=gwk,robust='hac',spat_diag = True,
                                          name_y=name_y, name_x=name_x,
                                          name_w=name_w,name_gwk=name_gwk,
                                          name_ds=name_ds)
            results['final model']="Spatial Lag with Spatial Error - HAC"
        elif Hetflag:
            r2 = PYSAL.model.spreg.GM_Combo_Het(y,x,w=w,name_y=name_y,name_x=name_x,
                                                name_w=name_w,name_ds=name_ds)
            results['final model']="Spatial Lag with Spatial Error - Heteroskedastic"
        else:
            r2 = PYSAL.model.spreg.GM_Combo_Hom(y,x,w=w,name_y=name_y,name_x=name_x,
                                                name_w=name_w,name_ds=name_ds)
            results['final model']="Spatial Lag with Spatial Error - Homoskedastic"
    elif model == "ERROR":
        results['spatial error']=True
        if Hetflag:
            r2 = PYSAL.model.spreg.GM_Error_Het(y,x,w,name_y=name_y,name_x=name_x,
                                                name_w=name_w,name_ds=name_ds)
            results['final model']="Spatial Error - Heteroskedastic"
        else:
            r2 = PYSAL.model.spreg.GM_Error_Hom(y,x,w,name_y=name_y,name_x=name_x,
                                                name_w=name_w,name_ds=name_ds)
            results['final model']="Spatial Error - Homoskedastic"
    elif model == "LAG":
        results['spatial lag']=True
        if Hetflag:
            r2 = PYSAL.model.spreg.GM_Lag(y,x,w=w,robust='white',
                                          name_y=name_y,name_x=name_x,
                                          name_w=name_w,name_ds=name_ds)
            results['final model']="Spatial Lag - Heteroskedastic"
        else:
            r2 = PYSAL.model.spreg.GM_Lag(y,x,w=w,name_y=name_y,name_x=name_x,
                                          name_w=name_w,name_ds=name_ds)
            results['final model']="Spatial Lag - Homoskedastic"
    else:
        if Hetflag:
            r2 = PYSAL.model.spreg.OLS(y,x,robust='white',name_y=name_y,name_x=name_x,
                                       name_ds=name_ds)
            results['final model']="No Space - Heteroskedastic"
        else:
            r2 = r1
            results['final model']="No Space - Homoskedastic"
    results['regression2'] = r2
    return results
