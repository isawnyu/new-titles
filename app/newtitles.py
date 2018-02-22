import glob

import xml.etree.ElementTree as ET
from xml.dom import minidom

def combine_xml(files):
    # See https://stackoverflow.com/q/15921642
    first = None
    xml_files = glob.glob(files +"/*.xml")
    xml_element_tree = None
    for xml_file in xml_files:
        data = ET.parse(xml_file).getroot()
        if first is None:
            first = data
        else:
            first.extend(data)
    if first is not None:
        return ET.tostring(first)

    
def pad_bsn(bsn):
    return '0' * (9-len(bsn)) + bsn


def prettify_xml(xml_string):
    return '\n'.join([line for line in minidom.parseString(xml_string).toprettyxml(indent=' '*2).split('\n') if line.strip()])


