#! python3

import argparse
import json
import math
import re
from socket import timeout
import sys
from typing import Any
from unicodedata import numeric
import webbrowser
# from matplotlib import table
from quantiphy import Quantity
import logging
from math import inf, nan
import os
import numpy as np
import pandas as pd
from darum.log_readers import Details, readLogs
from quantiphy import Quantity
import holoviews as hv  # type: ignore
# import hvplot           # type: ignore
# from hvplot import hvPlot
from holoviews import opts
from bokeh.models.tickers import FixedTicker, CompositeTicker, BasicTicker
from bokeh.models import NumeralTickFormatter, HoverTool
from bokeh.util.compiler import TypeScript
from bokeh.settings import settings
import os
import glob
import panel as pn
from bokeh.models.widgets.tables import NumberFormatter, BooleanFormatter
from ansi2html import Ansi2HTMLConverter

log = logging.getLogger(__name__)



def smag(i) -> str:
    return f"{Quantity(i):.3}"

def dn_is_excluded(dn, exclude_list):
    for e in exclude_list:
        regex = re.compile(e)
        if regex.search(dn):
            log.debug(f"Excluding {dn}")
            return True
    return False



class NumericalTickFormatterWithLimit(NumeralTickFormatter):
    fail_min = 0

    def __init__(self, fail_min:int, **kwargs):
        super().__init__(**kwargs)
        if __name__ == "__main__":
            print("The generated webpage will only work if this tool is run from its installed script - not the .py file in the package!")
            # This is because of how Bokeh includes these strings in the webpage. There's a "require(custom/XXXnumerical...)" that seems to catch the module name, 
            # and in the "static __name__" definition further down we need to get it the same.
            # This works correctly when using the scripts installed by e.g. poetry or pipx.
        NumericalTickFormatterWithLimit.fail_min = fail_min
        NumericalTickFormatterWithLimit.__implementation__ = TypeScript(
"""
import {NumeralTickFormatter} from 'models/formatters/numeral_tick_formatter'

export class NumericalTickFormatterWithLimit extends NumeralTickFormatter {
    static __name__ = '""" + __name__ + """.NumericalTickFormatterWithLimit'
    FAIL_MIN=""" + str(int(fail_min)) + """

    doFormat(ticks: number[], _opts: {loc: number}): string[] {
        const formatted = []
        const ticks2 = super.doFormat(ticks, _opts)
        for (let i = 0; i < ticks.length; i++) {
            if (ticks[i] < this.FAIL_MIN) {
                formatted.push(ticks2[i])
            } else {
                formatted.push('FAIL/OoR')
            }
        }
        return formatted
    }
}
""")

customJS = r"""
<script type="text/javascript">
/* Plain navigation to anchors doesn't work because the anchors are in a Panel, and each Panel is a shadowDOM. So we need to navigate programmatically. (Panel issue 6156? Closed, but not helping)
This is done by clickInterceptor.
Additionally, Panel doesn't give us Python references to the shadowDOMs that will be created by Bokeh, so to find where is an anchor in container C the best option seems to be to search from JS for known C ids inside the shadowDOMs. (Panel issue 7443) 
This is done with xfind. */

/**
 * @description Locates the first matching elements on the page, even within shadow DOMs, using a complex n-depth selector.
 * Author: Roland Ross L. Hadi
 * GitHub: https://github.com/rolandhadi/shadow-dom-selector
 */
function xfind(e,t=document){const o=performQuery(e,!1,t);return console.log(`Found ${o?1:0} element(s)`),o}function xfindAll(e,t=document){const o=performQuery(e,!0,t);return console.log(`Found ${o.length} element(s)`),o}function performQuery(e,t,o){validateSelector(e);const n=e.split(">>>");let r=o;for(let e=0;e<n.length;e++){if(e===n.length-1&&t)return querySelectorAllXFind(n[e],r);if(r=querySelectorXFind(n[e],r),null===r)return console.error(`Selector ${n[e]} not found`),t?[]:null}return r}function querySelectorAllXFind(e,t=document){return queryInShadowDOM(e,!0,t)}function querySelectorXFind(e,t=document){return queryInShadowDOM(e,!1,t)}function queryInShadowDOM(e,t,o){let n=o.querySelector(e);if(document.head.createShadowRoot||document.head.attachShadow){if(!t&&n)return n;return splitByUnquotedCharacter(e,",").reduce(((e,n)=>{if(!t&&e)return e;const r=splitByUnquotedCharacter(n.trim().replace(/\s*([>+~])\s*/g,"$1")," ").filter(Boolean),l=r.length-1,u=gatherAllElementsXFind(r[l],o),s=matchElements(r,l,o);return t?e.concat(u.filter(s)):u.find(s)||null}),t?[]:null)}return t?o.querySelectorAll(e):n}function matchElements(e,t,o){return n=>{let r=t,l=n;for(;l;){const t=!!l.matches&&l.matches(e[r]);if(t&&0===r)return!0;t&&r--,l=getParentOrHost(l,o)}return!1}}function splitByUnquotedCharacter(e,t){return e.match(/\\?.|^$/g).reduce(((e,o)=>('"'!==o||e.singleQuote?"'"!==o||e.doubleQuote?e.doubleQuote||e.singleQuote||o!==t?e.strings[e.strings.length-1]+=o:e.strings.push(""):(e.singleQuote^=1,e.strings[e.strings.length-1]+=o):(e.doubleQuote^=1,e.strings[e.strings.length-1]+=o),e)),{strings:[""],doubleQuote:0,singleQuote:0}).strings}function getParentOrHost(e,t){const o=e.parentNode;return o&&o.host&&11===o.nodeType?o.host:o===t?null:o}function gatherAllElementsXFind(e=null,t){const o=[],n=e=>{for(const t of e)o.push(t),t.shadowRoot&&n(t.shadowRoot.querySelectorAll("*"))};return t.shadowRoot&&n(t.shadowRoot.querySelectorAll("*")),n(t.querySelectorAll("*")),e?o.filter((t=>t.matches(e))):o}function validateSelector(e){try{document.createElement("div").querySelector(e)}catch{throw new Error(`Invalid selector: ${e}`)}}function highlightElements(e){const t=e=>{const t=e.style.outline;e.style.outline="2px solid red",setTimeout((()=>{e.style.outline=t}),2e3)};Array.isArray(e)?e.forEach(t):e&&t(e)}function showWelcomeMessage(){console.log("%cWelcome to Shadow DOM Selector!","color: green; font-size: 16px;"),console.log("%cAuthor: Roland Ross L. Hadi","color: blue; font-size: 14px;"),console.log("%cGitHub: https://github.com/rolandhadi/shadow-dom-selector","color: blue; font-size: 14px;"),console.log("%cExample usage: xfind('downloads-item:nth-child(4) #remove');","color: orange; font-size: 14px;")}showWelcomeMessage();


function onLoadHandler()  {
    "use strict";
    console.log("In onLoadHandler")
    // Bokeh's DocumentReady event is not working, maybe because we work at the Panel level or because it's a standalone doc
    //setTimeout(delayedAdder, 2000);     
    setInterval(delayedAdder, 1000) // keep looking for links created by Panel's Tabulator when scrolling the tables 
}

let lines 
let codeDOM

function delayedAdder() {
    "use strict";
    codeDOM = xfind('pre>code')
    if (codeDOM == null) {
        return
    }
    lines = Array.from(codeDOM.querySelectorAll('a[id^="L"]'))

    //stdoutDOM = xfindAll('.ansi2html-content')
    const anchorlinks = xfindAll('a[href^="#"]')
    anchorlinks.forEach((d) => {
        d.addEventListener("click", clickInterceptor)
    })

    window.addEventListener("popstate", PopStateHandler)
    console.log("delayAdder finished")
}

function clearSourceHighlight() {
    "use strict";
    const highlighted = Array.from(codeDOM.querySelectorAll('.highlighted'))
    highlighted.forEach( h => {
        h.classList.remove("highlighted")
    })
    console.log("Cleared highlights")
}

function clickInterceptor(e) {
    "use strict";
    const target = e.target;
    console.log("clickInterceptor:"+target)
    debugger
    if (target.matches('a[href^="#"]')) {
        e.preventDefault();

        stateData = {
            scrollTop: document.documentElement.scrollTop
        }
        window.history.pushState(stateData,"title",window.location.href)

        const destURL = target.getAttribute('href').slice(1) //remove #
        console.log(`DestURL = ${destURL}`)
        //is it a line range?
        const re = /L(\d+)-(\d+)/
        let range = re.exec(destURL)
        let destID
        if (range !== null) {
            console.log(`range ${range[1]}-${range[2]}`)
            destID = `L${range[1]}`
        } else {
            destID = destURL
        }
        const anchorSelector = 'a[id^="' + destID + '"]' // shouldn't be id= ??
        const dest = xfind(anchorSelector)
        dest.scrollIntoView() // shouldn't be in the IF?
        if (codeDOM.querySelectorAll(anchorSelector) !== null) {
            clearSourceHighlight() // should probably be outside of IF??
            if (range == null) {
                dest.classList.add("highlighted")
            } else {
                for (let i=range[1]; i<=range[2]; i++){
                    const anchorSelector = `a[id="L${i}"]`
                    const dest = xfind(anchorSelector)
                    dest.classList.add("highlighted")
                    console.log(`Highlighted ${anchorSelector}`)
                }
            }
        } else {
            console.log(`Selector not found: ${anchorSelector}`)
        }
        console.log("clickInterceptor done")
    }
}

function PopStateHandler(e) {
    "use strict";
    debugger
    let stateData = e.state;
    console.log("recovering state:" + JSON.stringify(stateData))
    document.documentElement.scrollTop = stateData.scrollTop
}

stateData = {
    scrollTop: 0
};
history.replaceState(stateData, "", document.location.href);

if (document.readyState !== "complete") {
  // Loading hasn't finished yet
  console.log("Still not complete: prepared onLoadHandler")
  window.addEventListener("load", onLoadHandler);
} else {
  // "load" has already fired
  onLoadHandler();
}

</script>
"""

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*', help="File/s to plot. If absent, tries to plot the latest JSON file in the output dir.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-p", "--recreate-pickle",action="store_true", help=argparse.SUPPRESS) #unmaintained
    parser.add_argument("-n", "--nbins", default=50)
    #parser.add_argument("-d", "--RCspan", type=int, default=10, help="The span maxRC-minRC (as a % of max) over which a plot is considered interesting")
    parser.add_argument("-x", "--exclude", action='append', default=[], help="DisplayNames matched by this regex will be excluded from the plot")
    parser.add_argument("-o", "--output_dir", default="darum", help="Directory to store the results. Default=%(default)s")
    parser.add_argument("-t", "--top", type=int, default=5, help="Plot only the top N most interesting. Default: %(default)s")
    parser.add_argument("--stop", default=False, action='store_true', help="Generate the HTML file but do not open it.")
    parser.add_argument("-s", "--force-standard-mode", default=False, action='store_true', help="Treat Assertion Batches just like members. Default: autodetect")
    parser.add_argument("-i", "--force-IA-mode", default=False, action='store_true', help="Whether to separate Assertion Batches and focus on them, instead of members. Best for Isolated Assertions mode. Default: autodetect")
    parser.add_argument("-l", "--limitRC", type=Quantity, default=None, help=argparse.SUPPRESS) #help="The RC limit that was used during verification. Used only to check consistency of results. Default: %(default)s")
    parser.add_argument("-b", "--bspan", type=int, default=0, help="A function's histogram will only be plotted if it spans => BSPAN bins. Default: %(default)s")

    args = parser.parse_args()
    return plot(args)

def plot(args) -> int:
    logging.basicConfig() #level=numeric_level,format='%(levelname)s:%(message)s')
    numeric_level = max(logging.DEBUG, logging.WARNING - args.verbose * 10)
    log.setLevel(numeric_level)
    logging.getLogger("darum.log_readers").setLevel(numeric_level)


    if not args.paths:
        # Get the path of the latest JSON file in the output directory
        jsons = glob.glob(args.output_dir+"/*.json")
        if jsons != []:
            latest_json = max(jsons, key=os.path.getmtime)
            print(f"Plotting latest JSON file in output dir: {args.output_dir}/{os.path.basename(latest_json)}")
            args.paths.append(latest_json)
        else:
            sys.exit("Error: No file given, and no JSON file in the output dir.")

    results = readLogs(args.paths, args.recreate_pickle)

    assert len(args.paths) == 1, "Multi-file support is not complete. Please specify only 1 file."
    p = args.paths[0]
    with open(p) as jsonfile:
        darum_context = json.load(jsonfile)['darum']
    sourcecode = {}# = list(darum_context['files'].values())[0].splitlines()
    for fname,fdata in darum_context['files'].items():
        sourcecode[fname] = fdata['contents'].splitlines()
        log.debug(f"Found source for '{fname}'")

    dafny_cmdline: list = darum_context["cmd"]
    try:
        lrc_index = dafny_cmdline.index("--resource-limit")
        args.limitRC = Quantity(dafny_cmdline[lrc_index+1])
        log.debug(f"{args.limitRC=} found in logfile ")
    except:
        pass
    IAmode_in_log = "--isolate-assertions" in dafny_cmdline
    if IAmode_in_log:
        log.debug(f"IAmode setting found in logfile")


    # PROCESS THE DATA
    comment_box = ""
    if args.limitRC is not None:
        comment_box += f"* LimitRC = {args.limitRC}\n"

    # Calculate the max-min span for each DisplayName, and the global maxRC, minRC, minFail
    maxRC = -inf
    minRC = inf
    maxRC_ABs = -inf
    minRC_ABs = inf
    minOoR = inf # min RC of the OoR entries
    minFailures = inf # min RC of the failed entries
    maxFailures = -inf # max RC of the failed entries
    df = pd.DataFrame( columns=["minRC", "maxRC", "slowdown", "success", "OoR","fail","fail_extr","AB","loc_html","loc_txt","diag","displayName", "desc", "src"])
    df.index.name="element"


    filenames : set[str]= set()
    for k,v in results.items():
        f = v.filename
        if len(f)>1:
            filenames.add(f)
    filenames_only_one = len(filenames)==1

    # Digest each entry's list of RCs into a dataframe row of the entry's stats
    for k,v in results.items():
        # for ig in args.exclude:
        #     if ig in k:
        #         log.debug(f"Excluding {k}")
        #         continue
        minRC_entry = min(v.RC, default=inf)
        maxRC_entry = max(v.RC, default=-inf)
        minOoR_entry = min(v.OoR, default=inf)
        minOoR = min(minOoR,minOoR_entry)
        minFailures_entry = min(v.failures, default=inf)
        minFailures = min(minFailures,minFailures_entry)
        maxFailures_entry = max(v.failures, default=-inf)
        maxFailures = max(maxFailures,maxFailures_entry)
        if v.AB==0:
            minRC = min(minRC, minRC_entry)
            maxRC = max(maxRC, maxRC_entry)
        else:
            minRC_ABs = min(minRC_ABs, minRC_entry)
            maxRC_ABs = max(maxRC_ABs, maxRC_entry)
    
        diag = ""

        # if a limit was given, we can do some fine-grained sanity checks
        if args.limitRC is not None and v.AB>0:
            # any RC > limitRC should be in the OoRs, not in the RCs
            # but beware, in IAmode, the vRs' RC is the sum of its ABs, so they can legitimately have RCs > limitRC
            if maxRC_entry > args.limitRC:
                log.warning(f"LimitRC={args.limitRC} but {k}({v.AB=}) has maxRC={Quantity(maxRC_entry)}. Should be OoR! ")
            if minOoR_entry < args.limitRC:
                log.warning(f"MinOoR for {k} is {min(v.OoR)}, should be > LimitRC={args.limitRC}")

        # Calculate the span between max and min
        maxCost_entry = maxRC_entry if len(v.OoR)==0 else minOoR_entry
        slowdown = maxCost_entry/minRC_entry # slowdown
        # info = f"{k:40} {len(v.RC):>10} {smag(minRC_entry):>8}    {smag(maxRC_entry):>6} {span:>8.2%}"
        # log.debug(info)
        fail_extremes = "" if minFailures_entry == inf else f"{smag(minFailures_entry)} - {smag(maxFailures_entry)}"
        loc_txt =  v.loc if filenames_only_one else f"{v.filename}:{v.loc}"
        # if we have the source code for the location, turn the location text into an hyperlink
        src = ""
        if sourcecode.get(v.filename) is None:
            loc_html = loc_txt
        else:
            loc_html = "" if filenames_only_one else f"{v.filename}:"
            loc_range = re.match(r'L(\d+)-(\d+)',v.loc) #Lddd-ddd
            if loc_range:
                loc_html += f'<a href="#{v.loc}">{v.loc}</a>'
            else:
                loc_LC = re.match(r'(\d+):(\d+)',v.loc) #ddd:ddd
                if loc_LC:
                    firstline = int(loc_LC.group(1))
                    col = int(loc_LC.group(2))
                    loc_html += f'<a href="#L{firstline}">{firstline}</a>:{col}'
                    srcline = sourcecode[v.filename][firstline-1]
                    src = srcline.lstrip()
                    leading_whitespace = len(srcline)-len(src) # This is correct if tab == 1 char. Dafny 4.8 does this, hence prints error markers out of place in stdout when there's tabs; some changes might come. https://github.com/dafny-lang/dafny/issues/5718
                    adjusted_col = col-leading_whitespace
                    src = src[:adjusted_col] + '🛑' + src[adjusted_col:] 


        df.loc[k] = {
            "success": len(v.RC),
            "minRC" : minRC_entry,
            "maxRC" : maxRC_entry,
            "slowdown" : slowdown,
            "OoR" : len(v.OoR),
            "fail" : len(v.failures),
            "AB" : v.AB,
            "loc_html"   : loc_html,
            "loc_txt" : loc_txt,
            "diag": diag,
            "displayName": v.displayName,
            "desc": v.description,
            "fail_extr": fail_extremes,
            "src": src
        }

    if minFailures == inf:
        df.drop(columns=["fail_extr"], inplace=True)
    minFailures = Quantity(minFailures)
    minOoR = Quantity(minOoR)
    # assert maxRC < minFail

    df_with_sources = df.loc[df.src!='']
    if df_with_sources.empty:
        df.drop(columns=["src"],inplace=True)

    # Make any per-DN adjustments
    members_with_many_ABs = 0
    DNs = set(df["displayName"].values)
    DNs_number = len(DNs)
    for d in DNs:
        # if a DN only has AB0 and AB1, then copy the location from AB1 to AB0 and drop AB1
        # because AB0 is summarized and easier to detect as non-AB in next steps
        dnABs = df[(df.displayName==d) & (df.AB>1)]
        if dnABs.empty:
            df.loc[(df.displayName==d) & (df.AB==0),"loc_html"] = df.loc[(df.displayName==d) & (df.AB==1),"loc_html"].values[0]
            df.drop(df[(df.displayName==d) & (df.AB==1)].index, inplace=True)
            df.loc[(df.displayName==d),"maxAB"] = 0
        else:
            df.loc[(df.displayName==d),"maxAB"] = max(dnABs.AB)
            members_with_many_ABs += 1


    # At this point, we should have no DNs with only AB1: either was absorbed into AB0 or there's AB2, etc
    assert df.loc[df.maxAB==1].empty, f"Unexpected AB1s: {df.loc[df.maxAB==1]}"

    # Add the emojis
    df.loc[(df.fail>0) & (df.success==0) ,"diag"] += "❌"
    if not df.loc[(df.fail>0)].empty :
        line = f"""Some items had verification failures, whose details aren't stored in the log. Please inspect the <a href="#stdout">stored Dafny stdout</a> further down."""
        log.info(line)
        comment_box += f"* {line}\n"    
    df.loc[(df.OoR>0),"diag"] += "⌛️"
    # An AB that flipflops needs highlighting
    df.loc[((df.fail>0) | (df.OoR>0)) & (df.success>0),"diag"] += "❗️"

    items_only_OoR = (df.OoR>0) & (df.success==0) & (df.fail==0)
    if  items_only_OoR.any() :
        line = f"Some items only had OoR results. Consider verifying again with a higher RC limit."
        log.info(line)
        comment_box += f"* {line}\n"

    # Ranking the items by interestingness is done through a score.
    # A good starting point:
    df["score"] = df.maxRC - df.minRC
    # but there's a lot of corner cases to consider.

    # Items without successes would have NaNs or infs, which breaks the rest of their calculations
    df.loc[~np.isfinite(df.score),"score"] = 0

    # ABs usually have smaller slowdowns and smaller RCs than whole members, so boost them
    AB_boost_factor = 5
    df.loc[df["AB"]>0,"score"] *= AB_boost_factor

    # Big RCs in ABs are even more suspicious than in whole members, so boost them
    # we need a big number. We want it around the max plotted to keep some measure of proportion.
    bigRC = minOoR
    if bigRC == inf: # there were no OoRs!
        bigRC = maxRC
    if bigRC == -inf: # there were no successes??
        bigRC == maxFailures

    # items with only 1 success have slowdown 0, yet a single success between many failures needs highlighting. Boost the score, but tag them
    only1success = (df.success==1) & ((df.fail+df.OoR)>1)
    df.loc[only1success,"score"] = bigRC
    df.loc[only1success,"diag"] += "❓"

    df.loc[df["OoR"]>0,"score"] += bigRC
    df.loc[df["fail"]>0,"score"] += bigRC * 2

    df.sort_values(["score"], ascending=False, kind='stable', inplace=True)

    IAmode_recommended = IAmode_in_log or (members_with_many_ABs > (DNs_number / 2))
    if args.force_standard_mode:
        if IAmode_recommended:
            log.info(f"Setting IAmode OFF, even though most members have multiple ABs")
            comment_box += f"* Isolate-assertions mode forced off\n"
        IAmode = False
    elif args.force_IA_mode:
        if not IAmode_recommended:
            log.info(f"Setting IAmode ON, even though most members have a single AB")
            comment_box += f"* Isolate-assertions mode forced on\n"
        IAmode = True
    else:
        IAmode= IAmode_recommended
        if IAmode_recommended and not IAmode_in_log:
            log.info(f"Setting IAmode ON because most members have multiple ABs")
            comment_box += f"* Most members have multiple ABs, so Isolate-assertions mode was enabled\n"

    # In IA mode, the focus in on the ABs. Separate them.
    if IAmode:
        #put the desc column at the end
        col_list = df.columns.tolist()
        col_list.remove("desc")
        col_list.append("desc")
        df = df[col_list]

        df_vrs = df[df["AB"] == 0]
        df = df[df["AB"]>0]
        log.debug(f"shape of vRs table:{df_vrs.shape}, ABs table:{df.shape}")
    else:
        df_vrs = None
        df.drop(columns="desc",inplace=True)

    # Add a new index that reifies the current order
    df.reset_index(inplace=True)
    df.rename_axis(index="idx",inplace=True)
    # And make it available as an alternative name. Useful for the element names in the plot legend and axis
    df['element_ordered'] = [f"{i} {s}" for i,s in zip(df.index,df["element"])]

    
    if args.limitRC is None:
        if minOoR < inf:
            # There are OoRs. No limitRC was given so we couldn't check while digesting the results. But now we can check a bit.
            # We expect actual results and failures to be smaller than the OoRs.
            mRC = max(maxFailures,maxRC_ABs) if maxFailures < inf else maxRC_ABs
            # if still infinite, means that everything we had was OoRs
            if mRC != inf:
                line = f"Logs contain OoR results, but no limitRC was given. Minimum OoR RC found = {minOoR}."
                log.info(line)
                comment_box += f"* {line}\n"
                OoRstr = f"OoR > {minOoR}"
                limitRC_defacto = minOoR
                if minOoR < maxRC_ABs:
                    line=f"LimitRC must have been <= {minOoR}, yet some results are higher: {maxRC_ABs=}"
                    log.warn(line)
                    comment_box += f"* {line}\n"
                if minOoR < maxFailures:
                    # Dafny bug??
                    line=f"LimitRC must have been <= {minOoR}, yet some failures are higher: {maxFailures=}. **Dafny bug?**"
                    log.warn(line)
                    comment_box += f"* {line}\n"

        else:
            OoRstr = ""
    else:
        limitRC_defacto = args.limitRC
        # we did some checking at the single-result-level while digesting the logs; here we can do global checks
        if args.limitRC < maxRC_ABs:
            line = f"LimitRC={args.limitRC}, yet some results are higher: {maxRC_ABs}"
            log.warn(line)
            comment_box += f"* {line}\n"
        if  maxFailures > args.limitRC:
            line = f"LimitRC={args.limitRC}, yet {maxFailures=} is higher"
            log.info(line)
            comment_box += f"* {line}\n"
        assert args.limitRC <= minOoR, f"LimitRC={args.limitRC}, yet some OoR results are lower: {minOoR=}"
        if minOoR < inf and  minOoR > args.limitRC * 1.1:
            # There are OoRs, but they are suspiciously higher than the given limit.
            line = (f"The min OoR found = {minOoR} is larger than {args.limitRC=}. Dafny/Z3 bug?") #Dafny issue 5525
            log.warn(line)
            comment_box += f"* {line}\n"
        OoRstr = f"OoR > {args.limitRC}"

    failstr: str = OoRstr #"FAILED"# + fstr

    # estimate the worst-case slowdown
    # if any entry has 0 successes then can't estimate
    if not IAmode: # because it's hard to see whether this'd be useful there
        if df.loc[df.success==0].empty:
            sumMaxRC = df.loc[(np.isfinite(df.maxRC)) & (df.OoR==0), "maxRC"].sum()
            sumMaxRC += limitRC_defacto * df.loc[df.OoR>0].shape[0]
            sumMinRC = df.loc[np.isfinite(df.minRC), "minRC"].sum()
            slowdown_total = sumMaxRC/sumMinRC
            line = f"Worst-case total slowdown estimated for this verification: {">" if minOoR < inf else ""}{slowdown_total:.1f}x"
            if not df.loc[df.OoR>0].empty :
                timeouts_pc = (df.loc[df.OoR>0, 'OoR']/(df.loc[df.OoR>0, 'OoR']+df.loc[df.OoR>0, 'success'])).max()*100
                line += f" (+ ~{timeouts_pc:.0f}% timeouts)"
            log.info(line)
            comment_box += f"* {line}\n"
        else:
            line = f"Can't estimate a worst-case slowdown because some member/s failed to verify at all."
            log.info(line)
            comment_box += f"* {line}\n"


    # PREPARATORY CALCULATIONS TO PLOT THE RESULTS

    # When plotting all histograms together, the result distribution might cause some DNs' bars
    # to fall too close together; the plot is not helpful then.
    # So let's remove such histograms.
    # For that, first we need to calculate all the histograms.
    # And for that, we need to decide their bins.
    # So get the min([minRCs]) and max([maxRCs]) of the top candidates.
    df["excluded"] = df["element"].map(lambda dn: dn_is_excluded(dn, args.exclude)).astype(bool)

    minRC_plot = min(df[~df["excluded"]].iloc[0:args.top]["minRC"])
    maxRC_plot = max(df[~df["excluded"]].iloc[0:args.top]["maxRC"])

    plotting_fails = (minOoR < inf) or (minFailures <inf) # whether we'll be plotting failures

    # The histograms have the user-given num of bins between minRC_plot and maxRC_plot,
    # + filler to the left until x=0, + 2 bins if there are fails (margin and fails bar)
    with np.errstate(invalid='ignore'): # silence RuntimeWarnings for inf values
        # inf could be in min/maxRC_plot if all plots are for funcs that failed for all random seeds
        if maxRC_plot < 2*minRC_plot: # the plot would be a big empty space with bars at the right end
            low_bin = 0
        else:
            low_bin = minRC_plot
        bins = np.linspace(Quantity(low_bin),Quantity(maxRC_plot), num=args.nbins+1)
        bin_width = bins[1]-bins[0]
            

    log.debug(f"{args.nbins=}, range {smag(minRC_plot)} - {smag(maxRC_plot)}, bin width {smag(bin_width)}")
    bin_fails_margin = 3 * bin_width
    bin_fails_width = 3 * bin_width
    bin_fails_borders = [bins[-1] + bin_fails_margin, bins[-1] + bin_fails_margin + bin_fails_width]
    bins_with_fails = np.append(bins,bin_fails_borders)
    bin_fails_separator = bins[-1] + 0.5 * bin_fails_margin

    labels_plotted = []
    bins_plot = bins_with_fails if plotting_fails else bins
    bin_centers = 0.5 * (bins_plot[:-1] + bins_plot[1:])
    bin_labels = [smag(b) for b in bin_centers]
    if plotting_fails:
        bin_labels = bin_labels[0:-2] + ["",failstr ]
    hist_df = pd.DataFrame(index = bin_centers)
    plotted = 0
    for i in df.index:
        row = df.loc[i]
        if row.excluded:
            df.loc[i,'diag'] = "⛔️" + df.loc[i,'diag']
            continue
        dnab = row.element
        d = results[dnab]
        nfails = len(d.OoR)+len(d.failures)
        counts, _ = np.histogram(d.RC,bins=bins)
        if plotting_fails:
            counts = np.append(counts,[0,nfails])

        # remove uninteresting plots: those without fails that would span less than <bspan> bins
        nonempty_bins = []
        for b,c in enumerate(counts):
            if c != 0:
                nonempty_bins.append(b)
        bin_span = nonempty_bins[-1]-nonempty_bins[0]

        if (nfails > 0) or (bin_span >= args.bspan):
            labels_plotted.append(dnab)
            hist_df[dnab] = counts
            with np.errstate(divide='ignore'): # to silence the errors because of log of 0 values
                hist_df[dnab+"_log"] = np.log10(counts)
            hist_df[dnab+"_log"] = hist_df[dnab+"_log"].apply(
                lambda l: l if l!=0 else 0.2    # log10(1) = 0, so it's barely visible in plot. log10(2)=0.3. So let's plot 1 as 0.2
                )
            hist_df[dnab+"_RCbin"] = bin_labels # for the hover tool
            df.loc[i,'diag'] = "📊" + df.loc[i,'diag'] #f"F={len(d.failures)} O={len(d.OoR)}"
            plotted += 1
        else:
            #row.diag+=f"{bin_span=}"
            pass
        if plotted >= args.top:
            break

    dropped_cols = ["element_ordered","AB","excluded","displayName","maxAB"]

    dropped_cols_text = dropped_cols.copy()
    dropped_cols_text += ["loc_html","src"]
    print(df.drop(columns=dropped_cols_text, errors='ignore')
            # .rename(columns={
            #     "span"          : "RC span %",
            #     "weighted_span" : "minRC * span"
            #     })
            .head(args.top)
            .to_string (formatters={
                    'maxRC':lambda x: smag(x) if abs(x)!=inf else "-" ,
                    'minRC':lambda x: smag(x) if abs(x)!=inf else "-" ,
                    #'OoRs':smag,
                    #'failures':smag,
                    "slowdown":lambda x: f"{x:>4.2}"
                    },
                na_rep='-',
                float_format=smag
                #max_rows=8
                )
            )

    can_plot = not np.isnan(bin_width) and bin_width >0
    if not can_plot:
        comment_box += f"* The top {args.top} results were not plottable. Only tables were generated.\n"

    print(f"Comments:\n{comment_box}")



    # HOLOVIEWS



    hv.extension('bokeh')
    # renderer = hv.renderer('bokeh')
    # settings.log_level('debug')
    # settings.py_log_level('debug')
    # settings.validation_level('all')

    hvplot = None
    if can_plot:
        histplots_dict = {}
        jitter = (bin_width)/len(labels_plotted)/3
        for i,dn in enumerate(labels_plotted):
            eo = df[df["element"]==dn]["element_ordered"].values[0]
            h = hv.Histogram(
                    (bins_plot+i*jitter,
                        hist_df[dn+"_log"],
                        hist_df[dn],
                        hist_df[dn+"_RCbin"]
                        ),
                    kdims=["RC"],
                    vdims=["LogQuantity", "Quantity", "RCbin"]
                )
            histplots_dict[eo] = h

        hover = HoverTool(tooltips=[
            ("Element", "@Element"),
            ("ResCount bin", "@RCbin"),
            ("Quantity", "@Quantity"),
            ("Log(Quantity)", "@LogQuantity"),
            ])

        bticker = BasicTicker(min_interval = 10**math.floor(math.log10(bin_width)), num_minor_ticks=0)

        hists = hv.NdOverlay(histplots_dict)#, kdims='Elements')
        hists.opts(
            opts.Histogram(alpha=0.9,
                            responsive=True,
                            height=500,
                            tools=[hover],
                            show_legend=True,
                            muted=True,
                            backend_opts={
                            "xaxis.bounds" : (0,bins_plot[-1]+bin_width),
                            "xaxis.ticker" : bticker
                                },
                            autorange='y',
                            ylim=(0,None),
                            xlim=(0,bins_plot[-1]+bin_width),
                            xlabel="RC bins",
                            padding=((0.1,0.1), (0, 0.1)),

                            color=hv.Cycle(),
                ),
            #,logy=True # histograms with logY have been broken in bokeh for years: https://github.com/holoviz/holoviews/issues/2591
            opts.NdOverlay(show_legend=True)
            )

        # A vertical separator for the fails bar
        vline = hv.VLine(bin_fails_separator).opts(
            opts.VLine(color='black', line_width=2, autorange='y',ylim=(0,None),apply_ranges=False)
        )
        vspan = hv.VSpan(bin_fails_separator).opts(
            opts.VSpan(color='#00000020', autorange='y',ylim=(0,None),apply_ranges=False)
        )

        hists = hists * vline * vspan

        ####### SPIKES

        # A JavaScript function to customize the hovertool
        from bokeh.models import CustomJSHover

        RCFfunc = CustomJSHover(code='''
                var value;
                var modified;
                if (value > ''' + str(int(maxRC_plot)) + ''') {
                    modified = "''' + failstr + '''";
                } else {
                    modified = value.toString();
                }
                return modified
        ''')

        nlabs = len(labels_plotted)
        spikes_dict = {}
        for i,dn in enumerate(labels_plotted):
            eo = df[df["element"]==dn]["element_ordered"].values[0]
            RC = results[dn].RC
            # Represent the failures / OoRs with a spike in the last bin
            spike_failures_num = len(results[dn].OoR)+len(results[dn].failures)
            if spike_failures_num > 0:
                spike_failures_sep = bin_width / spike_failures_num
                for f in range(spike_failures_num):
                    RC.append(bin_centers[-1] - bin_width/2 + f*spike_failures_sep)
            hover2 = HoverTool(
                        tooltips=[
                            ("Element", dn),
                            ("ResCount", "@RC{custom}"),
                            ],
                        formatters={
                            "@RC" : RCFfunc,
                            "dn"  : 'numeral'
                        }
                    )
            spikes_dict[eo] = hv.Spikes(RC,kdims="RC").opts(position=nlabs-i-1,tools=[hover2],xaxis="bottom")

        yticks = [(nlabs-i-0.5, list(spikes_dict.keys())[i]) for i in range(nlabs)]#-1,-1,-1)]
        spikes = hv.NdOverlay(spikes_dict).opts(
            yticks = yticks
            )

        spikes.opts(
            opts.Spikes(spike_length=1,
                        line_alpha=1,
                        responsive=True,
                        height=50+nlabs*20,
                        color=hv.Cycle(),
                        ylim=(0,nlabs),
                        autorange=None,
                        yaxis='right',
                        backend_opts={
                            "xaxis.bounds" : (0,bins_plot[-1]+bin_width)
                            },
                        show_legend=False,
                        ),
            opts.NdOverlay(show_legend=False,
                            click_policy='mute',
                            autorange=None,
                            ylim=(0,nlabs),
                            xlim=(0,bins_plot[-1]+bin_width),
                            padding=((0.1,0.1), (0, 0.1)),
                        ),
            #opts.NdOverlay(shared_axes=True, shared_datasource=True,show_legend=False)
            )


        spikes = spikes * vline * vspan


        ##### HISTOGRAMS AND SPIKES TOGETHER

        hvplot = hists + spikes #+ table_plot #+ hist #+ violin
        mf = NumericalTickFormatterWithLimit(bin_fails_separator, format="0.0a")

        hvplot.opts(
        #     #opts.Histogram(responsive=True, height=500, width=1000),
            # opts.Layout(sizing_mode="scale_both", shared_axes=True, sync_legends=True, shared_datasource=True)
            opts.NdOverlay(
                click_policy='mute',
                autorange='y',
                xformatter=mf,
                legend_position="right",
                responsive=True
                )
        )
        hvplot.opts(shared_axes=True)
        hvplot.cols(1)

    # TABLE/S
    dropped_cols += ["loc_txt"]
    #df["span"] = df["span"].apply(lambda d: nan if np.isnan(d) else int(d*10000)/100)
    # We can't use magnitudes with the RCs because then the tables can't be sorted correctly.
    df.minRC = df.minRC.apply(lambda x: x if abs(x)<inf else nan)
    df.maxRC = df.maxRC.apply(lambda x: x if abs(x)<inf else nan)
    df.success = df.success.apply(lambda x: x if x!=0 else nan)
    #df.OoR = df.OoR.apply(lambda x: x if x!=0 else "-")
    #df.fail = df.fail.apply(lambda x: x if x!=0 else "-")

    dft1 = df.drop(columns=dropped_cols).rename(
        columns={
            #"span":"slowdown",
            "loc_html":"location"
            }
    )


    bokeh_formatters = {
        'minRC': NumberFormatter(format='0,0', text_align = 'right',nan_format = '-'),
        'maxRC': NumberFormatter(format='0,0', text_align = 'right'),
        'slowdown': NumberFormatter(format='0.00', text_align = 'right'),
        'score': NumberFormatter(format='0,0', text_align = 'right'),
        'success': NumberFormatter(format='0,0', text_align = 'right'),
        'fail': NumberFormatter(format='0,0', text_align = 'right'),
        'OoR': NumberFormatter(format='0,0', text_align = 'right'),
        'location': {'type':'html'}
    }

    table = pn.widgets.Tabulator(dft1, 
        pagination=None,  # no explicit pages, just scrolling
        frozen_columns=['index'], 
        disabled=True, 
        layout='fit_data_table', 
        selectable=False, 
        text_align={"diag":"center"},
        formatters=bokeh_formatters, 
        configuration={
            "initialSort":[{"column":"score","dir":"asc"}], # not working anyway
            #"renderVertical":"basic" # the whole table is rendered at once, instead of when scrolled in
        }, 
        height=300) #give a glimpse of more rows

    table_title = pn.pane.Markdown("## All elements")
    table_vrs = None
    table_vrs_title = None
    if df_vrs is not None:
        df_vrs.reset_index(inplace=True)
        df_vrs.rename_axis(index="idx",inplace=True)
        #df_vrs["span"] = df_vrs["span"].apply(lambda d: nan if np.isnan(d) else int(d*10000)/100)
        #df_vrs.minRC = df_vrs.minRC.apply(lambda x: x if abs(x)<inf else "-")
        #df_vrs.maxRC = df_vrs.maxRC.apply(lambda x: x if abs(x)<inf else "-")
        #df_vrs.success = df_vrs.success.apply(lambda x: x if x!=0 else "-")
        #df_vrs.OoR = df_vrs.OoR.apply(lambda x: x if x!=0 else "-")
        #df_vrs.fail = df_vrs.fail.apply(lambda x: x if x!=0 else "-")
        dropped_cols += ["diag", "src", "desc"]
        dft2 = df_vrs.drop(columns=dropped_cols, errors='ignore').rename(
                            columns={
                                #"span":"RCspan%",
                                "loc_html":"location"   
                                })

        table_vrs = pn.widgets.Tabulator(dft2, 
            pagination=None,  
            frozen_columns=['index'], 
            disabled=True, 
            layout='fit_data_table', 
            selectable=False, 
            text_align={"diag":"center"},
            formatters=bokeh_formatters, 
            configuration={
                "initialSort":[{"column":"score","dir":"asc"}], # not working anyway
                #"renderVertical":"basic" 
            }, 
            height=300) #give a glimpse of more rows

        table_title = pn.pane.Markdown("## AB-level data")
        table_vrs_title = pn.pane.Markdown("## Member-level summary")


    # the legend and other explanations (score?) could be turned into table tooltips, hoped for Panel 1.5
    legend_icons = """
## Legend
### Elements
MemberName [C] = MemberName's Correctness assertions (as opposed to the default Well-Formedness)  
MemberName B2 = MemberName's Assertion Batch 2  


### Diagnostic icons
❌  All iterations failed verification  
⌛️  Some iteration ran Out of Resources  
❗️  Flipflopping result: some successes, some failures  
❓  Notable entry because there was only 1 success  
📊  Item present in the plot  
⛔️  Item excluded from plot  
"""
    legend_pane = pn.pane.Markdown(legend_icons)

    if comment_box!="":
        comment_box = "# Comments:\n" + comment_box
        pane_comment_box = pn.pane.Markdown(comment_box)
        # print(f"\n{comment_box}")
    else:
        pane_comment_box = None
        

    pane_cmds = pn.Column()
    conv = Ansi2HTMLConverter()
    for p in args.paths:
        try:
            with open(p) as jsonfile:
                j = json.load(jsonfile)['darum']
            pane_cmds.append(pn.pane.Markdown("**" + ' '.join(j['cmd']) + "**"))
            pane_cmds.append(pn.pane.HTML(f"""<a id="stdout"></a>""" + 
                    conv.convert("".join(j['output'])),styles={'background-color': '#CCC'}))
            for fname,fdata in j['files'].items():
    #             source = """Here is an example:

    #     :::python
    #     print('hellow world')
    #     """
    #             source = """Here is an example of AppleScript:
    # ``` { .lang linenos=true linenostart=42 hl_lines="43-44 50" title="An Example Code Block" }
    #     :::python
    #     print('hellow world')
    # ```
    # """
                # The markdown rendereres are supposed to highlight source code. But I can't make them work even to just add line numbers.
                # Pygments doesn't highlight Dafny, anyway.
                # So we add our own line numbers.
                numbered = ""
                splitted = fdata['contents'].splitlines(False)
                lines_max = len(splitted)
                num_digits = int(math.log10(lines_max))
                for i,l in enumerate(splitted):
                    numbered += f'<a id="L{i+1}">{i+1:{num_digits}}: {l}</a><br />'
                stylesheet = '''
a[id^="L"] {
  scroll-margin-top: 50vh;
}
.highlighted {
  background-color : yellow
}
'''
                pane_cmds.append(pn.pane.HTML(f'<h2 id="title">{fname}</h2><pre><code>{numbered}</code></pre>', stylesheets=[stylesheet]))#, renderer="markdown",extensions=["fenced_code","codehilite"]))
        except Exception as e:
            log.info(f"Failed to get extra context data from {p}:{e}")
            continue

    title = "-".join([os.path.splitext(os.path.basename(p))[0] for p in args.paths])
    pane_title = pn.pane.Markdown(f"# Log file: {title}")
    pane_customJS = pn.pane.HTML(customJS, visible=False)
    plot = pn.Column(pane_title, hvplot, table_title, table, table_vrs_title, table_vrs,   pane_comment_box, legend_pane, pane_cmds, pane_customJS)


    # fig.xaxis.bounds = (0,bin_fails)

    plotfilepath: str = os.path.join(args.output_dir, title+".html")

    try:
        os.remove(plotfilepath)
    except:
        pass

    #renderer.save(plot, 'plot')
    # from bokeh.resources import INLINE
    # hv.save(plot, plotfilepath, title=title) #resources='inline')
    #hvplot.show(plot)
    plot.save(plotfilepath,title=title)#, resources=INLINE)

    print(f"Created file {plotfilepath}")

    if args.stop:
        log.debug("Stopping as requested.")
        return(0)
    
    webbrowser.open("file://" + os.path.realpath(plotfilepath), new=2, autoraise=False) 
    #os.system(f"open {plotfilepath}")




    #webbrowser.open('plot.html')

    # ls = hv.link_selections.instance()
    # lplot = ls(plot)
    # hv.save(lplot, 'lplot.html')
    # os.system("open lplot.html")

    return 0


# for easier debugging
if __name__ == "__main__":
    main()

