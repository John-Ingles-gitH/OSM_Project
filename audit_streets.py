import re
import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict

SAMPLE_FILE = 'sample.osm'
REAL_FILE = 'portland_oregon.osm'

def audit_bad_endings(bad_endings, street_name):
    street_endings = ["Street", "Avenue", "Boulevard", "Drive", "Court",
                      "Place", "Circle", "Lane", "Road", "Way", "Terrace",
                      "Trail", "Highway", "Loop", "Parkway", "Greenway", 
                      "Broadway", "Byway", "Circus", "East", "Heights", "Landing"]
    
    street_ending_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    m = street_ending_re.search(street_name)
    
    if m:
        street_ending = m.group()
        if street_ending not in street_endings:
            bad_endings[street_ending].add(street_name)
            
def audit_street_capitalization(improper_street_capitalization, street_name):
    word_list = street_name.split()
    for word in word_list:
        if not word[0].isupper() and word[0].isalpha():
            improper_street_capitalization.add(street_name)
            
def audit_abbreviated_directions(bad_directions, street_name):
    directions = ["N", "NW","NE","S","SW","SE","E","W", "N.", "S.", "W.", "E.", "NW.", "NE.", "SW.", "SE."]
    
    first_word_re = re.compile(r'^\S+')
    m = first_word_re.search(street_name)
    
    if m:
        direction = m.group()
        if direction in directions:
            bad_directions[direction].add(street_name)
            
def is_street_name(elem):
    return (elem.attrib["k"] == "addr:street")

def street_audit(filename):
    bad_endings = defaultdict(set)
    bad_directions = defaultdict(set)
    improper_street_capitalization = set()
    for event, elem in ET.iterparse(filename, events=("start", )):
        for tag in elem.iter("tag"):
            if is_street_name(tag):
                street_name = tag.attrib['v']
                audit_bad_endings(bad_endings, street_name)
                audit_abbreviated_directions(bad_directions, street_name)
                audit_street_capitalization(improper_street_capitalization, street_name)
        elem.clear()
    return bad_endings, bad_directions, improper_street_capitalization
    
out_file = open("audit_out.txt","a+")

bad_endings, bad_directions, improper_street_capitalization = street_audit(SAMPLE_FILE)

out_file.write("\n")
out_file.write("Unexpected Street Endings:")
out_file.write("\n")
pprint.pprint(dict(bad_endings),out_file)
out_file.write("\n")
out_file.write("Abbreviated Cardinal Directions:")
out_file.write("\n")
pprint.pprint(dict(bad_directions),out_file)
out_file.write("\n")
out_file.write("Improperly Capitalized Street Names:")
out_file.write("\n")
out_file.write("\n".join(sorted(list(improper_street_capitalization))))
out_file.write("\n")
out_file.close()