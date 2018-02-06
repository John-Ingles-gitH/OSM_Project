import re
import xml.etree.cElementTree as ET

SAMPLE_FILE = 'sample.osm'
REAL_FILE = 'portland_oregon.osm'

def audit_postcode_trailing_chars(postcode_trailing_chars, postcode):
    postcode_trailing_chars_re = re.compile(r'\-[0-9]+$')
    m = postcode_trailing_chars_re.search(postcode)
    if m:
        postcode_trailing_chars.add(postcode)
        
def audit_postcode_preceding_chars(postcode_preceding_chars, postcode):
    postcode_preceding_chars_re = re.compile(r'^.+(?=([0-9]{5}))')
    m = postcode_preceding_chars_re.search(postcode)
    if m:
        postcode_preceding_chars.add(postcode)
    
def is_postcode(element):
    return (element.attrib["k"] == "addr:postcode")

def postcode_audit(filename):
    postcode_set = set()
    postcode_trailing_chars = set()
    postcode_preceding_chars = set()
    for event, element in ET.iterparse(filename, events=("start", )):
        for tag in element.iter("tag"):
            if is_postcode(tag):
                postcode = tag.attrib['v']
                if postcode not in postcode_set:
                    postcode_set.add(postcode)
                audit_postcode_trailing_chars(postcode_trailing_chars, postcode)
                audit_postcode_preceding_chars(postcode_preceding_chars, postcode)
        element.clear()
    return postcode_preceding_chars, postcode_trailing_chars, postcode_set
    
postcode_preceding_chars, postcode_trailing_chars, postcode_set = postcode_audit(SAMPLE_FILE)
out_file = open("audit_out.txt","a+")
out_file.write("\n")
out_file.write("Extra Postcode Trailing Characters:")
out_file.write("\n")
out_file.write("\n".join(list(postcode_trailing_chars)))
out_file.write("\n")
out_file.write("Extra Postcode Preceding Characters:")
out_file.write("\n")
out_file.write("\n".join(list(postcode_preceding_chars)))
out_file.write("\n")
out_file.write("Unique Postcodes:")
out_file.write("\n")
out_file.write("\n".join(sorted(list(postcode_set))))
out_file.write("\n")
out_file.close()