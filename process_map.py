import unicodecsv as csv
import codecs
import cerberus
import schema
import re
import xml.etree.cElementTree as ET
import pprint

OSM_PATH = "sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

nodes_to_remove = {1586441156,3101351150,3739845881,3745936974,3791964448,
                   4062672405,4062672406,4062672407,4062672408,4062672410,
                   4356679463,4880947375,4880947376,4880947379,4880947380,
                   4880947381,4880947382,4880947383,4880947384,4880947387,
                   4880947388,4880947389}

def is_street_name(elem):
    return (elem.attrib["k"] == "addr:street")
    
def is_city_name(element):
    return (element.attrib["k"] == "addr:city")
    
def is_postcode(element):
    return (element.attrib["k"] == "addr:postcode")
    
def is_state(element):
    return (element.attrib["k"] == "addr:state")
                   
def update_street(tag):
    street_ending_map = { "ave":"Avenue",'ave.':'Avenue','blvd.':'Boulevard', "blvd":"Boulevard",
                         "cir":"Circle",  "ct":"Court",'ct.':'Court',  "dr":"Drive",'dr.':'Drive',
                         "hwy":"Highway",'hwy.':'Highway',  "ln":"Lane",'ln.':'Lane',  "pkwy":"Parkway",
                         "pky":"Parkway",  "rd":"Road",'rd.':'Road',  "srive":"Drive",
                         "st":"Street", "st.":"Street",  "trl":"Trail",'trl.':'Trail'}
    street_direction_map = {"n":"North",'n.':'North', "nw":"Northwest",'nw.':'Northwest',"ne":"Northeast",
                            'ne.':'Northeast',"s":"South",'s.':'South',"sw":"Southwest",'sw.':'Southwest',
                            "se":"Southeast",'se.':'Southeast',"e":"East","w":"West",'e.':'East'}
    
    minor_changes_map = {"Main street":"Main Street","northeast 4th Avenue":"Northeast 4th Avenue"}
    change_flag = False
    street_ending_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    first_word_re = re.compile(r'^\S+')
    
    street_name = tag.attrib['v']
    
    m = street_ending_re.search(street_name)
    n = first_word_re.search(street_name)
    if m:
        street_ending = m.group()
        if street_ending.lower() in street_ending_map.keys():
            street_name = re.sub(r'\b\S+\.?$', street_ending_map[street_ending.lower()], street_name)
            change_flag = True
    if n:
        first_word = n.group()
        if first_word.lower() in street_direction_map.keys():
            street_name = re.sub(r'^\S+', street_direction_map[first_word.lower()], street_name)
            change_flag = True
    if street_name in minor_changes_map.keys():
        street_name = minor_changes_map[street_name]
        change_flag = True
    
    if change_flag:
        tag.set('v',street_name)
    return tag

def update_city(tag):
    city_map = {"molalla":"Molalla","vancouver":"Vancouver",
                "portland":"Portland","vernonia":"Vernonia", 
                "Portland, OR":"Portland", "Beaverton, OR":"Beaverton", 
                "St Helens":"St. Helens", "Portland, Oregon":"Portland", 
                ", Gales Creek":"Gales Creek", "La center":"La Center",
                "Vancoucer":"Vancouver","Newburg":"Newberg"}
    change_flag = False
    city_name = tag.attrib['v']
    if city_name in city_map.keys():
        city_name = city_map[city_name]
        change_flag=True
        
    if change_flag:
        tag.set('v', city_name)
    return tag

def update_state(tag):
    state_map = {'wa':'WA', 'Washington':'WA', 'or':'OR', 'ORs':'OR',
                 'Or':'OR', 'Oregon':'OR', '1401 N.E. 68th Avenue  Portland, OR 97213':'OR'}
    change_flag = False
    state_name = tag.attrib['v']
    if state_name in state_map.keys():
        state_name = state_map[state_name]
        change_flag = True
    if change_flag:
        tag.set('v', state_name)
    return tag

def update_postcode(tag):
    postcode_map = {'Portland, OR 97209':'97209'}
    postcode_trailing_chars_re = re.compile(r'\-[0-9]+$')
    change_flag = False
    postcode = tag.attrib['v']
    p = postcode_trailing_chars_re.search(postcode)
    if postcode in postcode_map.keys():
        postcode = postcode_map[postcode]
        change_flag = True        
    if p:
        postcode = postcode[:5]
        change_flag = True
    if change_flag:
        tag.set('v',postcode)
    return tag

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    
    
    # shape NODES and NODES_TAGS python dictionarys to schema for conversion to csv and eventual migration to a database
    if element.tag == 'node':
        node_tag_dict = {}
        for attribute in element.attrib:
            if attribute in node_attr_fields:
                node_attribs[attribute]=element.get(attribute)
        for child in element.iter('tag'):
            node_tag_dict['id'] = element.attrib['id']
            for tag_attrib in child.attrib:
                if tag_attrib == 'k':
                    if LOWER_COLON.search(child.get(tag_attrib)):
                        node_tag_dict['key']= ":".join(child.get(tag_attrib).split(':')[1:])
                        node_tag_dict['type']=child.get(tag_attrib).split(':')[0]
                    else:
                        node_tag_dict['type']=default_tag_type
                        node_tag_dict['key'] = child.get(tag_attrib)
                if tag_attrib == 'v':
                    node_tag_dict['value'] = child.get(tag_attrib)
            tags.append(node_tag_dict)
            node_tag_dict = {}
        node_shaped_dict = {'node': node_attribs, 'node_tags': tags}
        return node_shaped_dict
    elif element.tag == 'way':
        node_dict={}
        tag_dict={}
        for attribute in element.attrib:
            if attribute in way_attr_fields:
                way_attribs[attribute]=element.get(attribute)
        for child in element.iter('tag'):
            tag_dict['id'] = element.attrib['id']
            for tag_attrib in child.attrib:
                if tag_attrib == 'k':
                    if LOWER_COLON.search(child.get(tag_attrib)):
                        tag_dict['key']= ":".join(child.get(tag_attrib).split(':')[1:])
                        tag_dict['type']=child.get(tag_attrib).split(':')[0]
                    else:
                        tag_dict['type']=default_tag_type
                        tag_dict['key'] = child.get(tag_attrib)
                if tag_attrib == 'v':
                    tag_dict['value'] = child.get(tag_attrib)
            tags.append(tag_dict)
            tag_dict = {}
        n=0
        for child in element.iter('nd'):
            node_dict['id'] = element.attrib['id']
            for tag_attrib in child.attrib:
                node_dict['node_id']=child.get(tag_attrib)
                node_dict['position']=n
                n+=1
            way_nodes.append(node_dict) 
            node_dict={}
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        
        for field,errors in validator.errors.items():
            
            message_string = "\nElement of type '{0}' has the following errors:\n{1}"
            error_string = pprint.pformat(errors)
        
            raise Exception(message_string.format(field, error_string))


class DictWriter(csv.DictWriter, object):

    def writerow(self, row):
        super(DictWriter, self).writerow({
            k:v for k, v in row.items()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'wb') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'wb') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = DictWriter(nodes_file, NODE_FIELDS, lineterminator = '\n')
        node_tags_writer = DictWriter(nodes_tags_file, NODE_TAGS_FIELDS, lineterminator = '\n')
        ways_writer = DictWriter(ways_file, WAY_FIELDS, lineterminator = '\n')
        way_nodes_writer = DictWriter(way_nodes_file, WAY_NODES_FIELDS, lineterminator = '\n')
        way_tags_writer = DictWriter(way_tags_file, WAY_TAGS_FIELDS, lineterminator = '\n')

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()
        
        for _, element in ET.iterparse(file_in, events=("start", )):
            if element.tag=="node" or element.tag=="way":
                for tag in element.iter("tag"):
                    if is_street_name(tag):
                        tag = update_street(tag)
                    elif is_city_name(tag):
                        tag = update_city(tag)
                    elif is_state(tag):
                        tag = update_state(tag)
                    elif is_postcode(tag):
                        tag = update_postcode(tag)       
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    if element.attrib['id'] not in nodes_to_remove:
                        nodes_writer.writerow(el['node'])
                        node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags']) 
            element.clear()


process_map(OSM_PATH, validate=False)