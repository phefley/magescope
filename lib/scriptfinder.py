import hashlib
import traceback

from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options 

from requests import get

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from time import sleep

from json import dumps


DOM_LOAD_DELAY = 20
VALID_ALGORITHMS = hashlib.algorithms_guaranteed
DEFAULT_CHROME_DRIVER_PATH = "/usr/bin/chromedriver"
DEFAULT_PAGE_TIMEOUT = 90 #seconds

def normalizeUrl(inUrl, baseUrl):
    return urljoin(baseUrl, inUrl)

class JavaScriptResource():
    def __init__(self, url=None, integrity=None, tagString=None):
        self.__url = url
        self.__hashes = {}
        self.__strTag = tagString
        self.__parsedTag = None
        self.__inDom = False
        self.__inHtml = False
        self.__inResources = False
        self.__integrity = integrity
        self.__data = None

    def asDict(self):
        outDict = {}
        outDict['url'] = self.__url
        outDict['hashes'] = self.__hashes
        outDict['tag'] = self.__strTag
        outDict['inHtml'] = self.__inHtml
        outDict['inDom'] = self.__inDom
        outDict['inResources'] = self.__inResources
        return outDict

    def asJson(self):
        return dumps(self.asDict())

    def setIntegrity(self, v):
        self.__integrity = v
    
    def getIntegrity(self):
        return self.__integrity

    def setData(self, v):
        self.__data = v
    
    def getData(self):
        return self.__data

    def setInHtml(self, v=True):
        self.__inHtml = v

    def isInHtml(self):
        return self.__inHtml

    def setInDom(self, v=True):
        self.__inDom = v

    def isInDom(self):
        return self.__inDom

    def setInResources(self, v=True):
        self.__inResources = v

    def isInResources(self):
        return self.__inResources

    def setUrl(self, url):
        self.__url = url

    def getUrl(self):
        return self.__url

    def getHashes(self):
        return self.__hashes

    def getAvailableHashes(self):
        return self.__hashes.keys()

    def addHash(self, algo, value):
        if algo in VALID_ALGORITHMS:
            self.__hashes[algo] = value

    def removeHash(self, algo):
        if algo in self.__hashes.keys():
            self.__hashes.pop(algo)

    def getHashFor(self, algo):
        return self.__hashes.get(algo, None)

    def grindHashes(self, data):
        for algo in VALID_ALGORITHMS:
            hasher = hashlib.new(algo)
            hasher.update(data)
            self.addHash(algo, hasher.hexdigest())
    
    def getTagString(self):
        return self.__strTag
    
    def setTagString(self, ts):
        self.__strTag = ts

    def __eq__(self, other):
        if not other == None:
            if self.getUrl() == other.getUrl():
                if self.getTagString() == other.getTagString():
                    for algo in self.getAvailableHashes():
                        if self.getHashFor(algo) == other.getHashFor(algo):
                            return True
        return False


class ScriptFinder():
    def __init__(self):
        self.__url = None
        self.__driver = None
        self.__pageTimeout = DEFAULT_PAGE_TIMEOUT
        self.__jsResources = []
        self.__pageData = None
        self.__debug = False
        self.__driverPath = DEFAULT_CHROME_DRIVER_PATH

    def asDict(self):
        outDict = {}
        outDict['url'] = self.__url
        outDict['resources'] = []
        outDict['resourceCount'] = self.countResources()
        outDict['htmlResourceCount'] = self.countHtmlResources()
        outDict['domResourceCount'] = self.countDomResources()
        outDict['resourceResourceCount'] = self.countResourceResources()
        for r in self.getJsResources():
            outDict['resources'].append(r.asDict())
        return outDict

    def asJson(self):
        return dumps(self.asDict())

    def setUrl(self, url):
        self.__url = url

    def getUrl(self):
        return self.__url

    def setPageTimeout(self, t):
        self.__pageTimeout = t

    def getPageTimeout(self):
        return self.__pageTimeout

    def setPageData(self, pd):
        self.__pageData = pd

    def getPageData(self):
        return self.__pageData

    def getDebugFlag(self):
        return self.__debug
    
    def setDebugFlag(self, f):
        self.__debug = f

    def enableDebugging(self):
        self.setDebugFlag(True)

    def disableDebugging(self):
        self.setDebugFlag(False)

    def getDriverPath(self):
        return self.__driverPath
    
    def setDriverPath(self, dp):
        self.__driverPath = dp

    def getResourceFor(self, url):
        for rsc in self.__jsResources:
            if rsc.getUrl() == url:
                return rsc
        return None
    
    def addResource(self, r):
        self.__jsResources.append(r)

    def hasResourceFor(self, url):
        return not self.getResourceFor(url) == None

    def countResources(self):
        return len(self.getJsResources())
    
    def countHtmlResources(self):
        out = 0
        for res in self.getJsResources():
            if res.isInHtml():
                out+=1
        return out

    def countDomResources(self):
        out = 0
        for res in self.getJsResources():
            if res.isInDom():
                out+=1
        return out

    def countResourceResources(self):
        out = 0
        for res in self.getJsResources():
            if res.isInResources():
                out+=1
        return out

    def getPageData(self):
        if self.__url:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'}
            response = get(url=self.__url, headers=headers, allow_redirects=True)
            if response.status_code == 200:
                self.setPageData(response.content)
                soup = BeautifulSoup(response.content, 'html.parser')
                scriptSoups = soup.find_all('script')
                for scriptSoup in scriptSoups:
                    src = scriptSoup.get("src")
                    sri = scriptSoup.get("integrity")
                    if src:
                        url = normalizeUrl(src, self.getUrl())
                        newResource = JavaScriptResource(url, sri, str(scriptSoup))
                        newResource.setInHtml()
                        self.__jsResources.append(newResource)
                        if self.__debug:
                            print("[*] HTML Script at {url} with integrity {sri} and tag {tag}".format(url=url, sri=sri, tag=str(scriptSoup)))
            else:
                print("[-] Non 200 status code received in getting %s. Received code %s" % (self.__url, response.status_code))

    def startDriver(self):
        if not self.__driver:
            chrome_options = webdriver.ChromeOptions()  
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--load-images=no")
            # Check for your other options and bring them over here
            self.__driver = webdriver.Chrome(options=chrome_options)
            self.__driver.set_page_load_timeout(self.getPageTimeout())

    def stopDriver(self):
        if self.__driver:
            self.__driver.quit()

    def getJsResources(self):
        return self.__jsResources

    def handlePage(self):
        self.getPageData()
        self.startDriver()
        if self.__driver and self.__url:
            try:
                self.__driver.get(self.__url)
            except Exception as e:
                print("[-] Issue while getting {url}\n\n{exception}\n\n".format(url=self.__url, exception=e))
                error_msg = traceback.format_exc()
                print(error_msg)
                self.stopDriver()
                return None

            # Wait for the DOM
            sleep(DOM_LOAD_DELAY)

            # Start by getting the page HTML and looking for those resources
            html = self.__driver.page_source

            # Now go through the DOM and find all of the JS
            scriptElements = self.__driver.find_elements_by_tag_name("script")
            for scriptElement in scriptElements:
                src = scriptElement.get_attribute("src")
                sri = scriptElement.get_attribute("integrity")
                tag = scriptElement.get_attribute("outerHTML")
                if not src=='':
                    url = normalizeUrl(src, self.getUrl())
                    if self.hasResourceFor(url):
                        self.getResourceFor(url).setInDom()
                    else:
                        newResource = JavaScriptResource(url=src, integrity=sri, tagString=tag)
                        newResource.setInDom()
                        self.addResource(newResource)
                    if self.__debug:
                        print("[*] DOM Script at {url} with integrity {sri} and tag {tag}".format(url=url, sri=sri, tag=tag))
            
            """ CDP Resources are experimental and I removed them... for now.
            # Okay, now go through the page resources and find all of the scripts
            # https://chromedevtools.github.io/devtools-protocol/tot/Page
            resourceTree = self.__driver.execute_cdp_cmd('Page.getResourceTree',{})
            # Get the resources for the frame
            frameId = resourceTree['frameTree']['frame']['id']
            for rsc in resourceTree['frameTree']['resources']:
                if rsc["type"].lower() == "script":
                    try:
                        rscContent = self.__driver.execute_cdp_cmd("Page.getResourceContent",{"frameId":frameId,"url":rsc["url"]})
                        rawContent = rscContent.get("content",None)
                        if rawContent:
                            hasher = hashlib.md5()
                            hasher.update(rawContent.encode('utf-8'))
                            if self.__debug:
                                print("Resource script from CDP at {url} - {hash} of type {type}".format(url=rsc["url"], hash=hasher.hexdigest(), type=rsc['type']))
                            if self.hasResourceFor(rsc["url"]):
                                self.getResourceFor(rsc["url"]).setInResources()
                                self.getResourceFor(rsc["url"]).setData(rawContent)
                                self.getResourceFor(rsc["url"]).addHash("md5", hasher.hexdigest())
                            else:
                                if self.__debug:
                                    print("[-] What kind of weird trickery is this?? This was a resource but had no TAG?!?")
                    except Exception as e:
                        print("[-] Error getting {url}\n\t{error}".format(url=rsc["url"],error=e))
            # Get the resources for the child frames
            if 'childFrames' in resourceTree['frameTree'].keys():
                for frame in resourceTree['frameTree']['childFrames']:
                    for rsc in frame['resources']:
                        if rsc['type'].lower()=="script":
                            try:
                                rscContent = self.__driver.execute_cdp_cmd("Page.getResourceContent",{"frameId":frame["frame"]["id"],"url":rsc["url"]})
                                rawContent = rscContent.get("content",None)
                                if rawContent:
                                    hasher = hashlib.md5()
                                    hasher.update(rawContent.encode('utf-8'))
                                    if self.__debug:
                                        print("Resource script from CDP at {url} - {hash} of type {type}".format(url=rsc["url"], hash=hasher.hexdigest(), type=rsc['type']))
                                    if self.hasResourceFor(rsc["url"]):
                                        self.getResourceFor(rsc["url"]).setInResources()
                                        self.getResourceFor(rsc["url"]).setData(rawContent)
                                        self.getResourceFor(rsc["url"]).addHash("md5", hasher.hexdigest())
                                    else:
                                        if self.__debug:
                                            print("[-] What kind of weird trickery is this?? This was a resource but had no TAG?!?")
                            except Exception as e:
                                print("[-] Error getting {url}\n\t{error}".format(url=rsc["url"],error=e))
            """
        self.stopDriver()

