#!/usr/bin/python3
from argparse import ArgumentParser
from lib.scriptfinder import *
from json import dumps
from datetime import datetime
from tabulate import tabulate

import traceback

MAX_URL_CHARS = 120

parser = ArgumentParser()
parser.add_argument("--target", help="target url")
parser.add_argument("--list", help="a file containing a list of target urls")
parser.add_argument("--outfile", help="a file to write the json data to")
parser.add_argument("--debug", action="store_true", help="enable debug output")
parser.add_argument("--driver", help="path to chromedriver")

args = parser.parse_args()

if __name__ == '__main__':
    outList = []
    urlList = []
    if args.target:
        urlList.append(args.target)
    elif args.list:
        with open(args.list) as listFile:
            for line in listFile.readlines():
                urlList.append(line.strip())
        
    for url in urlList:
        print("[%s][*] Reviewing %s" % (datetime.today(),url))
        finder = ScriptFinder()
        if args.driver:
            finder.setDriverPath(args.driver)
        finder.setUrl(url)
        if args.debug:
            finder.enableDebugging()
        try:
            finder.handlePage()
        except Exception as e:
            print("[-] There was an issue working on %s\n%s\n" % (url, e))
            error_msg = traceback.format_exc()
            print(error_msg)
        outList.append(finder.asDict())

    outData = dumps(outList)

    if args.outfile:
        with open(args.outfile, 'w') as outfile:
            outfile.write(outData)
            print("[*] Data written to file %s" % args.outfile)
    else:
        print("\n\n")
        HEADERS_I_CARE_ABOUT = ["url", "inHtml", "inDom", "inResources"]
        for siteData in outList:
            url = siteData["url"]
            print("%s\n----------------------------------------\n" % url)
            tableData = []
            for resource in siteData["resources"]:
                rowData = []
                for header in HEADERS_I_CARE_ABOUT:
                    if header == "url":
                        rowData.append(resource[header][:MAX_URL_CHARS])
                    else:
                        rowData.append(resource[header])
                tableData.append(rowData)
            print(tabulate(tableData, HEADERS_I_CARE_ABOUT, tablefmt="github"))
            print()
