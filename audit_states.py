import xml.etree.cElementTree as ET

SAMPLE_FILE = 'sample.osm'
REAL_FILE = 'portland_oregon.osm'

def is_state(element):
    return (element.attrib["k"] == "addr:state")

def state_audit(filename):
    state_set = set()
    for event, element in ET.iterparse(filename, events=("start", )):
        for tag in element.iter("tag"):
            if is_state(tag):
                state = tag.attrib['v']
                if state != "OR" and state !="WA":
                    state_set.add(state)
        element.clear()
    return state_set

state_set = state_audit(SAMPLE_FILE)
out_file = open("audit_out.txt","a+")
out_file.write("\n")
out_file.write("Unexpected State Names:")
out_file.write("\n")
out_file.write("\n".join(sorted(list(state_set))))
out_file.write("\n")
out_file.close()