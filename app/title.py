import urllib.request
import xml.etree.ElementTree as ET
from itertools import groupby

class NewTitle(object):
    def __init__(self, bsn):
        self.bsn = bsn
        urlstring = 'http://aleph.library.nyu.edu/X?op=publish_avail&library=nyu01&doc_num=%s' % self.bsn
        url = urllib.request.urlopen(urlstring)
        tree = ET.parse(url)
        self.root = tree.getroot()
        
        # Get NewTitle info
        self.title_info = self.get_title_info()
        self.contributor_info = self.get_contributor_info()
        self.edition_info = self.get_edition_info()
        self.imprint_info = self.get_imprint_info()
        self.collection_info = self.get_collection_info()
        self.series_info = self.get_series_info()
        self.gift_info = self.get_gift_info()
        self.handle_info = self.get_handle_info()
                
        
    def get_element(self, tag, code, nr=True):
        datastring = ".//{http://www.loc.gov/MARC21/slim}datafield[@tag='%s']/{http://www.loc.gov/MARC21/slim}subfield" % tag
        datafield = self.root.findall(datastring)
        if nr:
            element = next((item.text for item in datafield if item.attrib['code'] == code), None)
        else:
            element = [item.text for item in datafield if item.attrib['code'] == code]
        return element

    
    # Should abstract this to be useful for getting other XML nodes
    def get_alts(self, tag):
        
        datastring = ".//{http://www.loc.gov/MARC21/slim}datafield[@tag='%s']/" % tag
        nodes = self.root.findall(datastring)
        
        alts = []
        
        for node in nodes:
            alts.append((node.attrib['code'], node.text))

        a = [list(g) for k, g in groupby(alts, lambda x: x[0] != '6') if k]
        b = [list(g)[0][1][:3] for k, g in groupby(alts, lambda x: x[0] == '6') if k]  
        c = dict(zip(b, a))
        
        return c
    
    
    def strip_char_(self, s, char):
        if s.endswith(char):
            return s[:-1]
        else:
            return s    

        
    def fix_punctuation_(self, string):
        string = string.replace(' ;', ';')
        string = string.replace(' :', ':')
        return string
    
    
    def alt_exists_(self):
        return any(self.get_element('880','6', False))

    
    def get_title_info(self):
        self.title = self.get_element('245','a')
        self.remainder_of_title = self.get_element('245','b')
        
        self.section_number = " ".join([self.strip_char_(item, '/').strip() for item in self.get_element('245','n', False)])
        self.section_name = " ".join([self.strip_char_(item, '/').strip() for item in self.get_element('245','p', False)])
        self.alt_section_number = None
        self.alt_section_name = None
        
        
        if self.alt_exists_():
            alt = self.get_alts('880')
            if '245' in alt.keys():
                alt_block = dict(alt['245'])

                self.title = alt_block['a']
                if 'b' in alt_block.keys():
                    self.remainder_of_title = alt_block['b']
                if 'n' in alt_block.keys():
                    self.alt_section_number = alt_block['n']
                if 'p' in alt_block.keys():
                    self.alt_section_name = alt_block['p']

            
    def get_contributor_info(self):
        self.contributor = self.get_element('245', 'c')
        
        if self.alt_exists_():
            alt = self.get_alts('880')
            if '245' in alt.keys():
                alt_block = dict(alt['245'])
                if 'c' in alt_block.keys():
                    self.contributor = alt_block['c']

                    
    def get_edition_info(self):
        self.edition = self.get_element('250', 'a')
        self.remainder = self.get_element('250', 'b')

        
    def get_imprint_info(self):
        self.places = self.get_element('264', 'a', False)
        self.publishers = self.get_element('264', 'b', False)
        self.dates = self.get_element('264', 'c', False)
        self.places_alt = self.get_element('260', 'a', False)
        self.publishers_alt = self.get_element('260', 'b', False)
        self.dates_alt = self.get_element('260', 'c', False)

        
    def get_collection_info(self):
        self.library = self.get_element('AVA', 'b', False)
        self.collection = self.get_element('AVA', 'c', False)
        self.callnumber = self.get_element('AVA', 'd', False)
        if self.callnumber == []:
            self.callnumber == ["Not found"]
        

        # Fix this hack; a node-based solution like the get_alts might be better for collections
        #print(self.callnumber)
        #while len(self.callnumber) < len(self.library):
        #    self.callnumber += self.callnumber[0]

        collection_ = list(zip(self.library, self.collection, self.callnumber))
        collection = []
        
        for item in collection_:
            if item[0] == 'NISAW':
                collection.append(item)
                break
            elif item[0] == 'WEB':
                collection.append(item)
                break
        
        #collection = [item for item in collection if item[0] == 'NISAW']
        if collection == []:
            self.library, self.collection, self.callnumber = None, None, None
        else:
            self.library, self.collection, self.callnumber = zip(*collection)

        
    def get_series_info(self):
        self.series = self.get_element('490', 'a', False)
        self.version = self.get_element('490', 'v', False)

        
    def get_gift_info(self):
        self.gift = self.get_element('500', 'a', False)
        self.gift = [item for item in self.gift if item.startswith('ISAW copy')]

    def get_handle_info(self):
        handle_loc = self.get_element('856', '3', False)
        handle = self.get_element('856', 'u', False)
        handles = list(zip(handle_loc, handle))
        handles = [item[1] for item in handles if item[0].startswith('Ancient World Digital Library')]
        if handles:
            self.handle = handles[0]
        else:
            self.handle = None
        
    def format_title(self):
        title = self.fix_punctuation_(self.title)
        if self.remainder_of_title:
            title += ' ' + self.remainder_of_title
        title = self.strip_char_(title, '/')
        title += ' ' + self.section_number + self.section_name
        if self.alt_section_number:
            title += ' = ' + self.alt_section_number
        if self.alt_section_name:
            title += '' + self.alt_section_name       
    
        title = title.strip()
        title = self.strip_char_(title, '.')
        
        return title

    def format_contributor(self):
        contributor = self.contributor
        if contributor:
            contributor = contributor[0].capitalize() + contributor[1:] # Capitalize first letter
            contributor = contributor.strip()
            contributor = self.strip_char_(contributor, '.')
        return contributor
    
    def format_edition(self):
        edition = self.edition
        remainder = self.remainder

        if remainder:
            edition += remainder
        
        if edition:
            return self.strip_char_(edition.strip(), '.')

    
    def format_imprint(self):
        
        self.places = self.get_element('264', 'a', False)
        self.publishers = self.get_element('264', 'b', False)
        self.dates = self.get_element('264', 'c', False)
        
        if self.places:
            places = self.places
        else:
            places = self.places_alt

        if self.publishers:
            publishers = self.publishers
        else:
            publishers = self.publishers_alt

        if self.dates:
            dates = self.dates
        else:
            dates = self.dates_alt

        places = [self.fix_punctuation_(place) for place in places]
        place = " ".join(places)

        publishers = [self.fix_punctuation_(publisher) for publisher in publishers]
        publisher = " ".join(publishers)

        if len(dates) == 2:
            date = dates[1]
        else:
            date = " ".join(dates)
        
        #print(date)
    
        imprint = " ".join([place, publisher, date]).strip()
        imprint = self.strip_char_(imprint, '.')
        
        return imprint
    
    def format_collection(self):
        collection = self.collection
        if collection:
            collection = collection[0].strip()
        return collection
    
    
    def format_callnumber(self):
        callnumber = self.callnumber
        if callnumber:
            callnumber = callnumber[0].strip()
            if callnumber.endswith(' Non-circulating'):
                callnumber = callnumber.replace(' Non-circulating','')
        return callnumber
    
    
    def format_series(self):
        series = self.series
        version = self.version
        version = [item.replace('no. ','') for item in version]
        
        series = [self.fix_punctuation_(s) for s in series]
        series = list(zip(series, version))
        series = " ".join([" ".join(item) for item in series])
        return series
    
    
    def format_gift(self):
        if self.gift:
            gift = self.gift[0]
            index = gift.find('from')
            gift = gift[index].upper() + gift[index+1:]
            gift = self.strip_char_(gift, '.')
            return gift
                       
    def format_handle(self):
        if self.handle:
            handle = self.handle
            return handle


class NewTitleXML(object):
    def __init__(self, bsn):
        self.bsn = bsn
        urlstring = 'http://aleph.library.nyu.edu/X?op=publish_avail&library=nyu01&doc_num=%s' % self.bsn
        url = urllib.request.urlopen(urlstring)
        tree = ET.parse(url)
        self.root = tree.getroot()