### Imports

import re
import roman

from datetime import datetime

from urllib.request import urlopen

import lxml.etree as ET
import xmltodict

### Load/convert infile

with open('data/in/ISAW_NEW_650_all.xml') as f:
    doc = xmltodict.parse(f.read())

### Extract date info

def get_month_year(aleph_xml_dict):
    date_sample = doc['printout']['ROW'][0]['DATE_ADDED']
    d = datetime.strptime(date_sample, '%Y%m%d')
    year = d.strftime('%Y')
    month = d.strftime('%m')
    return year, month

year, month = get_month_year(doc)

### Build list of bsns

bsns = []

for row in doc['printout']['ROW']:
    bsns.append(row['BSN'])

### Create xml object

urlbase = 'http://aleph.library.nyu.edu/X?op=publish_avail&library=nyu01&doc_num='
nss = {'marc': 'http://www.loc.gov/MARC21/slim',}

records = []

for bsn in bsns:
    url = f'{urlbase}{bsn}'
    response = urlopen(url)
    tree = ET.parse(response)
    root = tree.getroot()
    record = root.find('.//marc:record', nss)
    records.append(record)

xml = ET.fromstring("<collection>\n</collection>")
for record in records:
    record.tail = None
    xml.append(record)

### ISAW specific edits
##
## Todo
## Collapse multivols by BSN? (Recommendation of GM 7.12.18)

## Edit pagination
##
## Recommendation of GM 7.12.18
## e.g. change...
## <datafield tag="300" ind1=" " ind2=" ">
## <subfield code="a">3, 2, 2, 378 pages ;</subfield>
## ...to...
## <datafield tag="300" ind1=" " ind2=" ">
## <subfield code="a">378</subfield>
##
## If a comma (',') appears in this subfield...
## 1. the string is split by commas
## 2. regex matches on integer or roman number and p(ages|.)
## 3. the highest value is kept; in this case 378

def validate_pages_simple(pages_string):
    m = re.search(r'\[?(\d+?)\]? p(ages|\.)', pages_string)
    if m:
        return int(m[1])
    m = re.search(r'\b(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))\b p(ages|\.)', pages_string, re.IGNORECASE)
    if m:
        if m[0] == ' pages': # trap for problems with regex matching
            return 0
        else:
            return roman.fromRoman(m[1].upper())
    return 0

dfs_300 = xml.findall(".//marc:datafield[@tag='300']", nss)
for df in dfs_300:
    sfs = df.findall("marc:subfield[@code='a']", nss)
    for sf in sfs:
        if ',' in sf.text:
            temp = max([validate_pages_simple(item) for item in sf.text.split(',')])
            sf.text = str(temp)

## Remove subfield 9

# for bad in tree.xpath("//fruit[@state='rotten']"):
#     bad.getparent().remove(bad)

sfs_9 = xml.findall(".//marc:subfield[@code='9']", nss)

for sf in sfs_9:
    sf.getparent().remove(sf)

### Create marcxml output file

outfilepath = 'data/result/'
outfilename = f'newtitles-{year}-{month}-marc.xml'

with open(outfilepath+outfilename, 'wb+') as doc:
    doc.write(ET.tostring(xml, pretty_print = True))
