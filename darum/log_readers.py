import csv
import json
import logging as log
import re
from datetime import datetime as dt, timedelta as td
import os
import pickle
import sys
from typing import Tuple

def shortenDisplayName(dn:str) -> str:
    new: str = dn.replace("(well-formedness)","") # WF is almost everywhere, so omit it; better just mention anything non-WF
    new = new.replace("(correctness)","[C]")
    return new.strip()

class Details:
    def __init__(self) -> None:
        self.displayName: str = "" # without AB
        self.RC: list[int] = []
        self.OoR: list[int] = []   #OutOfResources
        self.failures: list[int] = []
        #self.RC_max: int     #useful for the table
        #self.RC_min: int
        self.line: int = 0
        self.col: int = 0
        self.filename: str = ""
        self.description: str = ""
        self.AB: int = 0 # in IA mode, there's ABs with a number (vcRs) and non-ABs with num 0 (the vRs that sum the RCs of the vcRs)

type resultsType = dict[str, Details] # displayName_with_AB:Details

def mergeResults(r:resultsType, rNew:resultsType):
    if len(rNew) == 0:
        log.debug(f"no results in rNew")
        exit(1)
    for k in rNew:
        if k in r:
            r[k].RC.extend(rNew[k].RC)
            r[k].OoR.extend(rNew[k].OoR)
            r[k].failures.extend(rNew[k].failures)
        else:
            r[k] = rNew[k]

def check_locations_ABs(locations) -> None:
    # checks across the whole file
    for loc,RStoABs in locations.items():
        if len(RStoABs) == 1:
            continue # only 1 rseed, so nothing to compare to check
        ABs_first = None
        # Ensure that, for each location, the ABs stay the same in every run
        for r,ABs in RStoABs.items():
            if ABs_first == None:
                ABs_first = ABs
                # some locations can accumulate many ABs
                # if len(ABs) > 1:
                #     log.debug(f"{loc} has {len(ABs)} ABs: {ABs}")
                continue
            assert ABs_first == ABs, f"{loc} has changing ABs. Until now it was {ABs_first}. But for rseed {r}, it's {ABs}"

def readCSV(fullpath) -> resultsType:
    """Reads the CSV file into the global usages map"""
    raise NotImplementedError("CSV reading needs fixing")
    # needs to be changed to return a resultsType like readJSON does
    # only reason to use CSV is for Dafny <4.5
    rows = 0
    global results
    with open(fullpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows += 1
            dn = shortenDisplayName(row['TestResult.DisplayName'])
            rc = row['TestResult.ResourceCount']
            results[dn] = results.get(dn,[]) + [int(rc)]
    log.info(f"{fullpath} :{rows} rows")
    return rows


def readJSON(fullpath: str, paranoid=True) -> resultsType:
    #reads 1 file (possibly containing multiple verification runs)
    results: resultsType = {}

    with open(fullpath) as jsonfile:
        try:
            j = json.load(jsonfile)
            verificationResults = j["verificationResults"]
        except:
            sys.exit("No verificationResults!")
    log.debug(f"{fullpath}: {len(verificationResults)} verificationResults")
    if len(verificationResults) == 0:
        return results
    
    # A JSON verification log contains a list of verificationResults (vR), from all the iterations
    # verification iterations are only distinguishable because the randomseed changes
    # Each vR corresponds to a function or method
    # and contains its Display Name, overall Resource Count, verification outcome and the vcResults (Assertion Batches)
    #   Each AB contains its number (vcNum), outcome, Resource Count, and a list of assertions
    # If "isolating assertions" was NOT used, then the AB list in a vR will contain only 1 AB
    #   1 vR = 1 AB = 1*(multiple assertions); we ignore them for plotting
    #       The AB contains the details we want; we ignore the individual assertions' locations, etc
    # If "isolating assertions" was used, then
    #   1 vR = n AB = n*(1 assertion)
    #       Since each AB contains 1 assertion which contains its location, we can keep that data for reporting convenience later.
    #
    # How this translates to our output:
    # if "isolating assertions" was NOT used, then the AB number is always 1, so no need to add it to our DN
    #   and that AB's entry only contains the list of RCs, not location
    # But if "isolating assertions" was used, then each DN contains an "AB x";
    #   and each such DN+AB's entry contains not only list of RCs, but also location

    try:
        mode_IA = (len(verificationResults[0]['vcResults']) > 1)  # Isolate Assertions. We guess the mode to check if it stays coherent.
    except:
        sys.exit("Empty verificationResults")

    locations: dict[tuple,dict[int,dict[str,str]]] = {} # relate (file,line,col) to {randomseed:{displayname_AB:description}}; allows to compare results per file position
    # the idea is that a given location, across all randomseeds, should have the same ABs and same results (descriptions)

    for vr in verificationResults:
        display_name = shortenDisplayName(vr["name"])        
        vr_RC = vr["resourceCount"]

        # the rseed is only present in the vcrs, so get it from the first one
        # we won't store it, it's only used for sanity checking and error reporting
        try:
            vr_rseed = vr['vcResults'][0]['randomSeed']
        except:
            # logs made by `dafny verify` contain no randomSeed
            vr_rseed = None

        det: Details = results.get(display_name, Details())
        det.AB = 0
        det.displayName = display_name # they only differ when IA is used
        if vr["outcome"] == "Correct":
            det.RC.append(vr_RC)
        elif vr["outcome"] == "OutOfResource":
            det.OoR.append(vr_RC)
            #assert vr["outcome"] != "Errors", f"{vr["name"]}, rseed={vr_rseed} has error outcome!"
        elif vr["outcome"] == "Errors":
                #log.info(f"{vr["name"]}, rseed={vr_rseed} has error outcome")
            det.failures.append(vr_RC)
        else:
            sys.exit(f"{display_name}.outcome == {vr["outcome"]}: unexpected!")
        if mode_IA:
            filename = vr['vcResults'][1]['assertions'][0]["filename"]
        else:
            filename = vr['vcResults'][0]['assertions'][0]["filename"]
        det.filename = filename
        results[display_name] = det

        # Without "isolating assertions", there is only 1 vcr per vr
        # Curiously, with IA, there is always an extra empty vcr in each vr, so with IA the minimum is 2 vcr per vr
        assert mode_IA == (len(vr['vcResults']) != 1), f"It looked like 'isolating-assertions'=={mode_IA}, and yet there's {len(vr['vcResults'])} ABs for {display_name}"

        if mode_IA:
            # We will check that the vr's RC equals the sum of the vcrs' RCs.
            vcrs_RC = []

            for vcr in vr['vcResults']:
                assert vr_rseed == vcr["randomSeed"], f"rseed mismatch: {vr_rseed} vs {vcr["randomSeed"]} in {display_name}"

                # There's multiple ABs. Each AB contains a single assertion
                AB = vcr['vcNum']
                display_name_AB: str = display_name + f" AB{AB}"
                det = results.get(display_name_AB, Details())
                det.AB = AB
                det.displayName = display_name

                # The first vcr is always empty
                if AB == 1:
                    assert len(vcr['assertions']) == 0 
                    # Plus, assertions contain their location and description, so here there should be nothing either
                    if det.line == 0:
                        det.filename = filename
                        det.line = 'not_in_log'
                        det.col = 'not_in_log'
                        det.description = 'not_in_log'
                    else:
                        assert det.line == 'not_in_log'
                else:
                    assert len(vcr['assertions']) <= 1, f"{display_name_AB} contains {len(vcr['assertions'])} assertions, expected 1 or 0 because we're in IA mode!"
                    try:
                        asst = vcr['assertions'][0]
                    except:
                        log.info(f"{display_name_AB} has no assertions")
                        asst = {'filename':filename,'line':'not_in_log','col':'not_in_log', 'description':'not_in_log'}
                    if det.line == 0:
                        det.filename = asst['filename']
                        det.line = asst['line']
                        det.col = asst['col']
                        det.description = asst['description']
                    else:
                        # This is not the first verification run, so
                        # just double-check that previous runs with this display_name + AB are consistent
                        assert det.filename == asst['filename'], f"{display_name_AB}.filename: {det.filename} vs {asst['filename']}"
                        assert det.line == asst['line']
                        assert det.col == asst['col']
                        assert det.description == asst['description']
                location_current = (det.filename, display_name, det.line, det.col)
                l = locations.get(location_current,{})
                l2 = l.get(vr_rseed,{})
                l2[AB]=det.description
                l[vr_rseed]=l2
                locations[location_current] = l


                vcr_RC = vcr['resourceCount']
                vcrs_RC.append(vcr_RC)
                if vcr["outcome"] == "OutOfResource" :
                    assert vr["outcome"] == "OutOfResource", f"{display_name_AB}==OoR, {display_name}=={vr["outcome"]}: unexpected!"
                    det.OoR.append(vcr_RC)
                elif vcr["outcome"] == "Valid":
                    det.RC.append(vcr_RC)
                elif vcr["outcome"] == "Invalid":
                    assert vr["outcome"] == "Errors", f"{display_name_AB}==Invalid, {display_name}=={vr["outcome"]}: unexpected!"
                    det.failures.append(vcr_RC)
                else:
                    sys.exit(f"{display_name_AB}.outcome == {vcr["outcome"]}: unexpected!")
                results[display_name_AB] = det

            # Ensure that the sum of AB's RCs equals the vr's RC, independent of success/failure
            assert sum(vcrs_RC) == vr_RC, f"{display_name}.RC={vr_RC}, but the sum of the vcrs' RCs is {sum(vcrs_RC)} "
        
    if paranoid:
        check_locations_ABs(locations)

    return results



def readLogs(paths, read_pickle = False, write_pickle = False) -> resultsType:

    results: resultsType = {}
    files = 0
    # to be un/pickled: [files, results]

    t0 = dt.now()
    picklefilepath = "".join(paths)+"v2.pickle"
    if os.path.isfile(picklefilepath) and read_pickle:
        with open(picklefilepath, 'rb') as pf:
            [files, results] = pickle.load(pf)
        print(f"Loaded pickle: {files} files {(dt.now()-t0)/td(seconds=1)}")
        return results
    else:

        for p in paths:
            # os.walk doesn't accept files, only dirs; so we need to process single files separately
            log.debug(f"root {p}")
            if os.path.isfile(p):
                ext = os.path.splitext(p)[1]
                if ext == ".json":
                    results_read = readJSON(p)
                elif ext == ".csv":
                    results_read = readCSV(p)
                else:
                    sys.exit(f"Unknown file extension {ext} in {p}")
                mergeResults(results, results_read)
                files += 1
                continue
            files_before_root = files
            for dirpath, dirnames, dirfiles in os.walk(p):
                files_before = files
                for f in dirfiles:
                    if not ".json" in f:
                        continue
                    files +=1
                    fullpath = os.path.join(dirpath, f)
                    log.debug(f"file {files}: {fullpath}")
                    ext = os.path.splitext(fullpath)
                    if ext == ".json":
                        results_read = readJSON(fullpath)
                    elif ext == ".csv":
                        results_read = readCSV(fullpath)
                    else:
                        sys.exit(f"Unknown file format: {fullpath}")
                    mergeResults(results, results_read)

            if files_before_root == files:
                print(f"no files found in {p}")
                exit(1)


        log.debug(f"Processed {files} files in {(dt.now()-t0)/td(seconds=1)}")

        # PRINT OVERLAPPING ABs
        # go through each result, store its location vs what happened in it
        # finally print locations with multiple results
        # loc_ABs: dict[tuple,dict[str,str]] = {}
        # for dn,det in results.items():
        #     loc = (det.filename,det.line,det.col)
        #     if loc == (None, None, None):
        #         continue
        #     ABs = loc_ABs.get(loc,{})
        #     ABs[dn]=det.description
        #     loc_ABs[loc]=ABs
        # for loc,ABs in loc_ABs.items():
        #     if len(ABs)>1:
        #         log.info(f" {loc[0]}:{loc[1]}:{loc[2]} contains {len(ABs)} ABs: {ABs}")

        if write_pickle:
            with open(picklefilepath, "wb") as pf:
                pickle.dump([files, results], pf)
        return results

