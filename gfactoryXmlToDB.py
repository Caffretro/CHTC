#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gets the entries from gfactory XML files and converts them to a sqlite DB"""

import glob
import os
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple
from distutils.util import strtobool


US_TLDS = {"net", "gov", "edu", "org", "com"}


Attribs = namedtuple("Attribs", "fqdn us gridtype gatekeeper name enabled hosted vos")


def entries_from_tree(tree):
    return tree.findall("./entries/entry[@name][@enabled][@gatekeeper][@gridtype]")


def vos_from_entry(entry):
    vos = set()
    for elem in entry.findall("./attrs/attr[@name='GLIDEIN_Supported_VOs'][@value]"):
        vos = vos.union(elem.attrib["value"].strip().split(","))
    return vos


def get_attribs(entry):
    gk = entry.get("gatekeeper").strip()
    gridtype = entry.get("gridtype").strip()
    fqdn = fqdn_from_gatekeeper_and_gridtype(gk, gridtype)
    us = is_us_fqdn(fqdn)
    hosted = is_hosted_fqdn(fqdn)
    vos = vos_from_entry(entry)
    vos = ",".join("'%s'" % vo.strip() for vo in sorted(vos))
    return Attribs(
        fqdn.lower(),
        us,
        gridtype,
        gk,
        entry.get("name"),
        strtobool(entry.get("enabled")),
        hosted,
        vos,
    )


def is_hosted_fqdn(fqdn):
    return (
        fqdn.startswith("hosted-ce") or fqdn.startswith("pearc-ce")
    ) and fqdn.endswith(".grid.uchicago.edu")


def fqdn_from_gatekeeper_and_gridtype(gatekeeper, gridtype):
    if gridtype.startswith("batch"):  # BOSCO: "login@hostname"
        if "@" in gatekeeper:
            return gatekeeper.split("@")[1]
    elif gridtype == "condor":  # Condor-C: "<schedd host[:port]> <cm host[:port]>"
        match = re.match(r"[^: ]+(?:[:]\d+)?\s+([^: ]+)", gatekeeper)
        if match:
            return match.group(1)
    elif gridtype in ["cream", "gt2", "gt5"]:  # CREAM, GRAM: "hostname[:port]/endpoint"
        match = re.match(r"([^:/]+)", gatekeeper)
        if match:
            return match.group(1)
    elif gridtype == "ec2":  # EC2: "SCHEME://HOST[:PORT][/...]"
        match = re.match(r"\w+://([^:/]+)", gatekeeper)
        if match:
            return match.group(1)
    elif gridtype == "nordugrid":  # this one's prety easy :)
        return gatekeeper


def is_us_fqdn(fqdn):
    # special cases
    if fqdn.endswith(".cancercomputer.com"):
        return False
    if fqdn.endswith(".slateci.io"):
        return True

    tld = fqdn.split(".")[-1]
    return tld in US_TLDS


def xml_to_table(db, fname, prod):
    with open(fname, "r") as fh:
        tree = ET.fromstring(fh.read())

    cur = db.cursor()

    for ent in entries_from_tree(tree):
        attribs = get_attribs(ent)
        cur.execute(
            "INSERT INTO entry (name, enabled, gatekeeper, gridtype, fqdn, prod, us, hosted, vos) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                attribs.name,
                attribs.enabled,
                attribs.gatekeeper,
                attribs.gridtype,
                attribs.fqdn,
                prod,
                attribs.us,
                attribs.hosted,
                attribs.vos,
            ),
        )

    db.commit()


def main(argv):
    try:
        dbname = argv[2]
    except IndexError:
        dbname = "gfactory.sqlite"

    db = sqlite3.connect(dbname)

    db.executescript(
        """
        DROP TABLE IF EXISTS entry;

        CREATE TABLE entry(
            name TEXT,
            enabled INTEGER,
            gatekeeper TEXT,
            gridtype TEXT,
            fqdn TEXT,
            prod INTEGER,
            us INTEGER,
            hosted INTEGER,
            vos TEXT
        );
"""
        # note: I can't use name as a PRIMARY KEY because a name might have multiple entries (some enabled, some disabled)
    )

    try:
        datadir = sys.argv[1]
    except IndexError:
        datadir = "."

    fnames = glob.glob(datadir + "/*.xml")
    if not fnames:
        sys.exit("No xml files found")

    for fname in fnames:
        xml_to_table(
            db, fname, prod=not bool(re.search(r"\bitb\b", os.path.basename(fname)))
        )


main(sys.argv)