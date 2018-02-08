import pathlib
from shutil import copyfile

import xml.etree.ElementTree as ET

import xmltodict
from newtitles import combine_xml, pad_bsn, prettify_xml

# Read a txt file of isbns
# File should be named append-bsns.txt
# Make an argument?
append_infile = 'data/in/append-bsns.txt'

append_exists = pathlib.Path(append_infile).exists()

if append_exists:
    with open(append_infile, "r") as f:
        append_bsns = f.read().splitlines()
        append_bsns = [pad_bsn(bsn) for bsn in append_bsns]

    #Transform list into XML file
    root = ET.Element('printout')
    
    for i, item in enumerate(append_bsns):
        temp = ET.Element('ROW')
        child = ET.Element('BSN')
        child.text = item
        temp.append(child)
        child = ET.Element('BARCODE')
        child.text = str(i)
        temp.append(child)
        root.append(temp)
    
        # pretty string
        xmlstr = prettify_xml(ET.tostring(root))
        
        # Write append record to xml file
        with open("data/tmp/append_bsns.xml", "w") as f:
            f.write(xmlstr)

        # Delete infile?

# Combine xml NT report with append
# File should be named report.xml
# Make an argument?
process_infile = 'data/in/report.xml'
process_tmp = 'data/tmp/report.xml'
copyfile(process_infile, process_tmp)

combined_xml = combine_xml('data/tmp/')
xmlstr = prettify_xml(combined_xml)

process_outfile = 'data/out/full_report.xml'

with open(process_outfile, "w") as f:
    f.write(xmlstr)

with open(process_outfile) as f:
    doc = xmltodict.parse(f.read())
    
print(doc[:100])

    
#if __name__ == '__main__':
#   check for append
#   check for report
        