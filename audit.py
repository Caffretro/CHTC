from gfactoryXmlToDB import *
from collections import defaultdict
import yaml
import requests

treeDump = False


def getTopologyData(topologyDB):
    # insert Names under a dictionary that stores 4 "groupname"-set pairs
    # Structure of the dictionary:
    # {'resourceGroups': {},
    #  'facilities': {},
    #  'sites': {},
    #  'resources': {}}
    #
    # The XML has the following hierarchy: (only showing info we need)
    # | root
    # | --ResourceGroup
    # | ----Facility
    # | ----Site
    # | ----Resources
    # | --------Resource
    topologyTree = ET.parse("resource_topology.xml")
    topologyRoot = topologyTree.getroot()

    for child in topologyRoot.findall('ResourceGroup'):
        # adding resourceGroup Name attribute to a set
        name = child.find('GroupName')
        if treeDump:
            print("| " + name.text)
        try:
            topologyDB['resourceGroups'].add(name.text)
        except KeyError:
            topologyDB['resourceGroups'] = {name.text}

        for facility in child.findall('Facility'):
            facilityName = facility.find('Name')
            if treeDump:
                print("| ---- " + facilityName.text)
            try:
                topologyDB['facilities'].add(facilityName.text)
            except KeyError:
                topologyDB['facilities'] = {facilityName.text}
        for site in child.findall('Site'):
            siteName = site.find('Name')
            if treeDump:
                print("| ---- " + siteName.text)
            try:
                topologyDB['sites'].add(siteName.text)
            except KeyError:
                topologyDB['sites'] = {siteName.text}
        for resources in child.findall('Resources'):
            for resource in resources.findall('Resource'):
                resourceName = resource.find('Name')
                if treeDump:
                    print("| >>>> " + resourceName.text)
                try:
                    topologyDB['resources'].add(resourceName.text)
                except KeyError:
                    topologyDB['resources'] = {resourceName.text}


def run(argv):
    # fetch the content and store in local disk
    URL = "https://my.opensciencegrid.org/rgsummary/xml"
    response = requests.get(URL)
    with open("resource_topology.xml", "wb") as file:
        file.write(response.content)

    # TODO: use normal way to parse topology, the gfactory to DB is not for topology
    # topologyDB = getXML(argv)
    topologyDB = {}
    getTopologyData(topologyDB)

    print(sorted(topologyDB['resourceGroups']))


if __name__ == "__main__":
    run(sys.argv)
