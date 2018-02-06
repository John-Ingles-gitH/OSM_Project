import re
import xml.etree.cElementTree as ET

SAMPLE_FILE = 'sample.osm'
REAL_FILE = 'portland_oregon.osm'

def audit_city_capitalization(improper_city_capitalization, city_name):
    word_list = city_name.split()
    for word in word_list:
        if not word[0].isupper() and word[0].isalpha():
            improper_city_capitalization.add(city_name)

def audit_city_trailing_chars(city_trailing_chars, city_name):
    city_trailing_chars_re = re.compile(r'\s*\,\s*\S*')
    m = city_trailing_chars_re.search(city_name)
    if m:
        city_trailing_chars.add(city_name)
            
def is_city_name(element):
    return (element.attrib["k"] == "addr:city")

def city_audit(filename):
    improper_city_capitalization = set()
    city_trailing_chars = set()
    city_set = set()
    
    for event, element in ET.iterparse(filename, events=("start", )):
        for tag in element.iter("tag"):
            if is_city_name(tag):
                city_name = tag.attrib['v']
                if city_name not in city_set:
                    city_set.add(city_name)
                audit_city_capitalization(improper_city_capitalization, city_name)
                audit_city_trailing_chars(city_trailing_chars, city_name)
        element.clear()
    return improper_city_capitalization, city_trailing_chars, city_set
    
improper_city_capitalization, city_trailing_chars, city_set = city_audit(SAMPLE_FILE)
out_file = open("audit_out.txt","a+")
out_file.write("\n")
out_file.write("Improper Capitalization:")
out_file.write("\n")
out_file.write("\n".join(list(improper_city_capitalization)))
out_file.write("\n")
out_file.write("Extra Trailing Characters:")
out_file.write("\n")
out_file.write("\n".join(list(city_trailing_chars)))
out_file.write("\n")
out_file.write("Unique Cities:")
out_file.write("\n")
out_file.write("\n".join(sorted(list(city_set))))
out_file.write("\n")
out_file.close()