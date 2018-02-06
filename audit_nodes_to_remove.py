import xml.etree.cElementTree as ET
import pprint
from collections import Counter

SAMPLE_FILE = 'sample.osm'
REAL_FILE = 'portland_oregon.osm'

def get_id_num(element):
    
    return element.attrib['id']

def get_coord(element):
    
    node_lat = element.attrib['lat']
    node_lon = element.attrib['lon']
    node_coord=node_lat+', '+node_lon
    
    return node_coord    
    
def identify_coord_dups(filename):
    #input: osm file

    #output:

    #1. dups_to_consider - set containing coordinates (lat, lon) that have been found to occur in more than one node.
    
    #   Of these duplicates, only duplicate sets with at least one node with no tags are considered

    #   For example:

    #       <node id="0" lat="0",lon="0">
    #           <tag whatever="whatever"/>
    #       </node>
    
    #       <node id="1" lat="0",lon="0">
    #           <tag whatever="whatever"/>
    #       </node>
    
    #       <node id="2" lat="0",lon="0">
    #           <tag whatever="whatever"/>
    #       </node>

    #This set of duplicates would be ignored and the coordinate (0, 0) would not be in the final dups_to_consider set
    #The reason for this is I decided any element with tags shouldn't be removed

    #2. id_coord_dict - dictionary of the duplicates with node ids as keys and coordinates as values

    #3. with_tags_counter - Counter object that has the number of elements with tags for each duplicate coordinate

    #4. without_tags_counter - Counter object that has the number of elements without tags for each duplicate coordinate
    
    without_tags_counter = Counter()
    with_tags_counter = Counter()
    node_coord_counter=Counter()
    node_coord_dups = set()
    dups_to_consider = set()
    id_coord_dict = {}
    
    for _, element in ET.iterparse(filename):
        if element.tag =="node":
            
            #count number of occurances of each coordinate
            node_coord = get_coord(element)
            node_coord_counter[node_coord]+=1
            
            #create dictionary {id_num, coordinate}
            id_num = get_id_num(element)
            id_coord_dict[id_num] = node_coord
            
            #check if element has any tags
            any_tags = len(element)
            
            #keep track of the number of nodes with tags and without tags for each duplicate coordinate
            if not any_tags:
                without_tags_counter[node_coord]+=1
            else:
                with_tags_counter[node_coord]+=1
                
            #add coord to set of duplicates if it's count is over 1
            if node_coord_counter[node_coord]>1:
                node_coord_dups.add(node_coord)
            else:
                #only keep tag count record if it's of a duplicate coordinate
                if not any_tags:
                    without_tags_counter[node_coord]-=1
                else:
                    with_tags_counter[node_coord]-=1    
            
            #add previous tag stats when dupe count reaches two to make up for when duplicate status was unknown
            if node_coord_counter[node_coord]==2:
                if not any_tags_previously:
                    without_tags_counter[node_coord]+=1
                else:
                    with_tags_counter[node_coord]+=1
            
            #keep track of whether the previous element in the iteration had tags
            any_tags_previously = len(element)
            
        element.clear()
    
    #If all the duplicates for a particular coordinate have tags, then none of them will be considered for removal
    for dup_coord in node_coord_dups:
        if without_tags_counter[dup_coord]>=1:
            dups_to_consider.add(dup_coord)
    
    #make a {id, coord} dict of only duplicates
    dup_id_coord_dict = {k:v for k,v in id_coord_dict.items() if v in dups_to_consider}
    
            
    return dups_to_consider, dup_id_coord_dict, without_tags_counter, with_tags_counter

def find_nodes_to_remove(filename):
    #input: osm file

    #output: set with nodes to remove identified by their node id

    #nodes are removed that satisfy all three conditions:

    #   1. duplicate map coordinates
    #   2. no tags
    #   3. no way references
    
    keep_set = set()
    remove_set = set()
    
    dups_to_consider, dup_id_coord_dict, without_tags_counter, with_tags_counter= identify_coord_dups(filename)
    
    
    #keep nodes that are referenced in way tags
    for _, element in ET.iterparse(filename, events=("start", )):
        if element.tag == "way":
            for nd in element.iter("nd"):
                ref = nd.attrib['ref']
                if ref in dup_id_coord_dict.keys():
                    keep_set.add(ref)
        element.clear()
    
    for _, element in ET.iterparse(filename):
        if element.tag =="node":
            
            id_num = get_id_num(element)
            coord = get_coord(element)
            any_tags = len(element)
            
            #keep any nodes with tags and
            #get rid of duplicates without tags if ones with tags exist
            if coord in dups_to_consider:
                if any_tags:
                    keep_set.add(id_num)
                else:
                    if without_tags_counter[coord]>1 and id_num not in keep_set:
                        remove_set.add(id_num)
                        without_tags_counter[coord]-=1
                    elif without_tags_counter[coord]==1 and id_num not in keep_set:
                        if with_tags_counter[coord]>=1:
                            remove_set.add(id_num)
                            without_tags_counter[coord]-=1
        element.clear()
    return remove_set
    
out_file = open("audit_out.txt","a+")    
nodes_to_remove=find_nodes_to_remove(SAMPLE_FILE)
out_file.write("\n")
out_file.write("Node Ids of nodes with duplicate coordinates, no tags, and no way references:\n")
out_file.write("\n".join(sorted(list(nodes_to_remove))))
out_file.write("\n")
out_file.close()