from gfactoryXmlToDB import *
import yaml
import requests


def run(argv):
    # fetch the content and store in local disk
    URL = "https://my.opensciencegrid.org/rgsummary/xml"
    response = requests.get(URL)
    with open("resource_topology.xml", "wb") as file:
        file.write(response.content)

    # TODO: use normal way to parse topology, the gfactory to DB is not for topology
    # topologyDB = getXML(argv)



if __name__ == "__main__":
    run(sys.argv)