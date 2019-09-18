from flask import render_template
from app import app

###
#Move this elsewhere
###
import pathlib
from shutil import copyfile

import csv
import pickle
import urllib.request

import xml.etree.ElementTree as ET

import xmltodict
import callnumber as callnumber

import os
from pyzotero import zotero

from datetime import datetime, date
from calendar import monthrange

from pprint import pprint

from app.newtitles import combine_xml, pad_bsn, prettify_xml
from app.title import NewTitle, NewTitleXML

### Load/convert infile

with open('app/data/in/ISAW_NEW_650_all.xml') as f:
    doc = xmltodict.parse(f.read())

######################################################
### Extract date info
def get_sample_date(aleph_xml_dict):
    sample_row = doc['printout']['ROW'][0]['DATE_ADDED']
    sample_date = datetime.strptime(sample_row, '%Y%m%d')
    return sample_date

def get_date_info(sample_date):
    d = sample_date
    year = d.strftime('%Y')
    month = d.strftime('%m')
    month_name = d.strftime('%B')
    return year, month, month_name

sample_date = get_sample_date(doc)
year, month, month_name = get_date_info(sample_date)
print(year, month, month_name)
if int(month) == 1:
    last_month_name = "December"
else:
    last_month_name = date(1900, int(month)-1, 1).strftime('%B')
_, max_day = monthrange(int(year), int(month))
max_day = '{:02}'.format(max_day)

range_low_str = f'{year}{month}01'
range_high_str = f'{year}{month}{max_day}'
range_low = datetime.strptime(range_low_str, '%Y%m%d')
range_high = datetime.strptime(range_high_str, '%Y%m%d')
range_low_format = range_low.strftime('%B %-d, %Y')
range_high_format = range_high.strftime('%B %-d, %Y')

zotero_match = f'{int(month):02d}: {month_name} {year}'

if int(month) == 1:
    zotero_match_last = f'12: December {int(year)-1}'
else:
    zotero_match_last = f'{int(month)-1:02d}: {last_month_name} {year}'

######################################################

######################################################

# Get BSN Addons

from app.addons import get_addons

# def get_addons(sample_date):
#     append_infile = 'app/data/in/append_bsns.txt'
#     append_exists = pathlib.Path(append_infile).exists()
#
#     if append_exists:
#         with open(append_infile, "r") as f:
#             addons = [pad_bsn(bsn) for bsn in f.read().splitlines()]
#
#     return addons



######################################################


######################################################
### Check Zotero for new collection

library_id = os.getenv('LIBRARY_ID')
library_type = os.getenv('LIBRARY_TYPE')
api_key = os.getenv('API_KEY')

z = zotero.Zotero(library_id, library_type, api_key)

collection_data = [(item['data']['name'],
                    item['data']['key'],
                    item['data']['parentCollection']) for item in z.collections()]

collection_names, collection_keys, collection_parents = zip(*collection_data)

if zotero_match not in collection_names:
    print('No match!')

    collection_parent = collection_parents[collection_names.index(zotero_match_last)]

    print('Adding new collection...')

    new_collection = z.create_collections([{'name': zotero_match, 'parentCollection': collection_parent}])
    collection_key = new_collection['success']['0']
else:
    print('Already there!')
    collection_key = collection_parents[collection_names.index(zotero_match)]
######################################################

######################################################
# Read a txt file of isbns
# File should be named append-bsns.txt
# Make an argument?
def process(addons=None):

    if addons:
        # Transform list into XML file
        root = ET.Element('printout')

        for i, item in enumerate(addons):
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
            with open('app/data/tmp/append_bsns.xml', 'w') as f:
                f.write(xmlstr)

            # Delete infile?

    # Combine xml NT report with append
    # File should be named report.xml
    # Make an argument?
    process_infile = 'app/data/in/ISAW_NEW_650_all.xml'
    process_tmp = 'app/data/tmp/report.xml'
    copyfile(process_infile, process_tmp)

    combined_xml = combine_xml('app/data/tmp/')
    xmlstr = prettify_xml(combined_xml)

    process_outfile = 'app/data/out/full_report.xml'

    with open(process_outfile, "w") as f:
        f.write(xmlstr)

    with open(process_outfile) as f:
        doc = xmltodict.parse(f.read())

    # Logging?
    print('There are {} records in this month\'s report.'.format(len(doc['printout']['ROW'])))

    report = []

    for row in doc['printout']['ROW']:
        item = {}
        item['barcode'] = row['BARCODE']
        item['bsn'] = row['BSN']
        if 'VOLUME_INFO' in row.keys():
            item['volume'] = row['VOLUME_INFO']
            if '(' in item['volume']:
                item['volume'] = item['volume'].replace('(',' (')

        if 'Z13_IMPRINT' in row.keys():
            item['imprint'] = row['Z13_IMPRINT']

        report.append(item)

    barcodes = [item['barcode'] for item in report]
    bsns = [item['bsn'] for item in report]
    # pprint(list(zip(barcodes, bsns)))

    # Move to newtitles.py
    # http://stackoverflow.com/a/3308844

    import unicodedata as ud

    latin_letters= {}

    def is_latin(uchr):
        try: return latin_letters[uchr]
        except KeyError:
             return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))

    def only_roman_chars(unistr):
        return all(is_latin(uchr)
               for uchr in unistr
               if uchr.isalpha()) # isalpha suggested by John Machin

    def check_bsn(bsn):
        urlstring = 'http://aleph.library.nyu.edu/X?op=publish_avail&library=nyu01&doc_num=%s' % bsn
        url = urllib.request.urlopen(urlstring)
        tree = ET.parse(url)
        root = tree.getroot()
        check = root.findall(".//{http://www.openarchives.org/OAI/2.0/}metadata")
        return True if check else False

    records = []
    processed = 0
    successes = 0

    for i, barcode in enumerate(barcodes):
        bc_index = barcodes.index(barcode)

        bsn = report[bc_index]['bsn']
        processed += 1


        if check_bsn(bsn):
            successes += 1

            new_title = NewTitle(bsn) # API call already made in check--capture that information so there is no need to make second call?

            #print("Processing record %d: %s" % (i+1, bsn))

            record = {}
            record['bsn'] = bsn
            record['title'] = new_title.format_title()
            record['char'] = only_roman_chars(record['title'])
            record['contributor'] = new_title.format_contributor()
            record['edition'] = new_title.format_edition()

            if 'imprint' in report[bc_index].keys():
                record['imprint'] = report[bc_index]['imprint'].strip()
                record['imprint'] = record['imprint'][:-1] if record['imprint'][-1] == '.' else record['imprint']
            else:
                record['imprint'] = new_title.format_imprint()

            record['imprint'] = new_title.format_imprint()
            record['collection'] = new_title.format_collection()
            record['series'] = new_title.format_series()

            if 'volume' in report[bc_index].keys():
                record['volume'] = report[bc_index]['volume'].replace('.', '. ')
            else:
                record['volume'] = ""

            # FIX!
            record['callnumber'] = new_title.format_callnumber()
            if record['callnumber']:
                record['lccn'] = callnumber.LC(record['callnumber']).normalized
            else:
                record['lccn'] = "Call number missing"

            if record['lccn'] == None:
                record['lccn'] = record['callnumber'].strip().title()

            if record['volume']:
                if record['callnumber']:
                    record['callnumber'] += " " + record['volume']

            record['gift'] = new_title.format_gift()
            record['handle'] = new_title.format_handle()

            records.append(record)
        else:
            print(f'{bsn} is an invalid BSN. Skipping record...')

    print('\nFinished processing %d records with %d successes.' % (processed, successes))


    ## Choose category using call number map

    with open('app/data/ref/lc_classes.csv', 'r') as f:
      reader = csv.reader(f)
      lc_classes = list(reader)

    for i, record in enumerate(records):
        #print(i, record['title'], record['callnumber'])
        record['category'] = 'other'
        if record['callnumber']:
            cn = callnumber.LC(record['callnumber'])
            cn_split = cn.components()
            #print(cn_split)
            if cn_split:
                if len(cn_split) > 1:
                    if cn_split[0] in [item[0] for item in lc_classes]:
                        #print('Yes')
                        rows = [item for item in lc_classes if cn_split[0]==item[0]]
                        for row in rows:
                            #print(row)
                            if float(row[1]) <= float(cn_split[1]) <= float(row[2]):
                                #print(float(row[1]) <= float(cn_split[1]) <= float(row[2]))
                                record['category'] = row[3]
                                #print('Updated!')
                                break
            else:
                print(record['title'], record['lccn'])

    ## Guess category

    from app.categorize_nt import predict_categories
    # ^^^ Can put any categorization algorithm into this module

    titles = [record['title'] for record in records]

    predicted_categories = predict_categories(titles)
    for i, category in enumerate(predicted_categories):
        if records[i]['category'] == 'other':
            records[i]['title'] = "*"+records[i]['title']
            records[i]['category'] = category

    records = sorted(records, key=lambda k: (k['lccn'], int(''.join(list(filter(str.isdigit, "0"+ k['volume']))))))

    with open('app/data/ref/newtitles.p', 'wb') as f:
        pickle.dump(records, f)

######################################################
# *****
# WRITE SCRIPT TO ADD NEW TITLES TO ZOTERO
# *****
######################################################

import pickle

nts = pickle.load(open("app/data/ref/newtitles.p", "rb" ))

cats = ['Classical Antiquity & Western Europe',
        'Egypt & North Africa',
        'The Ancient Near East & Asia Minor',
        'The Caucasus & The Western Steppe',
        'Central Asia & Siberia',
        'China, South Asia, & East Asia',
        'Cross-Cultural Studies & Other']

@app.route('/')
def index():
    zotero_link = f'https://www.zotero.org/groups/290269/isaw_library_new_titles/items/collectionKey/{collection_key}'

    # Break process() up into smaller functions
    addons = get_addons(sample_date)
    process(addons=addons)
    return render_template("index.html",
                           title='Home',
                           range_low_format=range_low_format,
                           range_high_format=range_high_format,
                           zotero_link=zotero_link,
                           nts=nts,
                           cats=cats #cats=set([nt['category'].title() for nt in nts])
                          )



@app.route('/test')
def xml_test():
    #XML = NewTitleXML('002061459')
    #info = XML.root
    import requests
    from pprint import pprint
    r = requests.get("http://aleph.library.nyu.edu/X?op=publish_avail&library=nyu01&doc_num=002061459")
    info = xmltodict.parse(r.content)['publish-avail']['OAI-PMH']['ListRecords']['record']['metadata']['record']
    pprint(dict(info))
    info = dict(info)
    return render_template('test.html', info=info)



# Fix insertion of date range
