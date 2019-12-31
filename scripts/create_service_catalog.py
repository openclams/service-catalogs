import glob
import os
import json
from typing import List, Set, Dict, Tuple, Optional, Any
import jsonschema
import argparse
import re

def read_JSON_from_file(path:str,schema_path:str) ->  Dict[str,Any]:
    json_fragments_list: Dict[str,Any] = {}
    with open(schema_path, 'r') as schema_file:
        json_schema = json.load(schema_file)


    for json_file_path in glob.glob(path+"/*.json"):
        print("-> Found JSON Files: ",json_file_path)
        with open(json_file_path) as json_file:
            json_data = json.load(json_file)
            try:
                #Validate JSON with Schema
                jsonschema.validate(json_data, json_schema)
                print("-> File fragments are valid")
            except jsonschema.exceptions.ValidationError:
                print("Error: JSON file is not valid. The file is ignored.")

            #Collect all tree nodes as fragments object from one partial
            #ans organize them by id in the fragments list
            for tree_node in json_data:
                node_id:str = str(tree_node["id"])
                if node_id not in json_fragments_list:
                    json_fragments_list[node_id] = tree_node
                else:
                    print("Error: Duplicate Id Found.")
                    print("Node Id:",node_id,'in',json_file_path)
                    print("Node with Id:'"+node_id+"'is ignored.")
    return json_fragments_list

def add_parent_attribute(json_fragments_list):
    root_nodes = find_root_nodes(json_fragments_list)
    for node_id in root_nodes:
        add_parent(node_id,json_fragments_list)

def add_parent(node_id,json_fragments_list):
    if "children" in json_fragments_list[node_id]: 
        for child_id in json_fragments_list[node_id]["children"]:
            if "parents" not in json_fragments_list[child_id]:
                json_fragments_list[child_id]["parents"] = []
            json_fragments_list[child_id]["parents"].append(node_id)
            add_parent(child_id,json_fragments_list)    

def find_root_nodes(json_fragments_list):
    list_of_all_children_ids = []
    for node_id in json_fragments_list:
        if json_fragments_list[node_id]["type"] == "Node" and "children" in json_fragments_list[node_id]:
            list_of_all_children_ids.extend(json_fragments_list[node_id]["children"])

    return [node_id for node_id in json_fragments_list if node_id not in list_of_all_children_ids]

def generate_json_output(structure,output_file):
    json_obj = {
        "Nodes":{},
        "Edges": {},
        "Templates": {}
    }
    for node_id in structure:
        if structure[node_id]["type"] == "Node":
            json_obj["Nodes"][node_id] = structure[node_id]
        elif structure[node_id]["type"] == "Edge":
            json_obj["Edges"][node_id] = structure[node_id]
        elif structure[node_id]["type"] == "Template":
            json_obj["Templates"][node_id] = structure[node_id]
   
    json_data = json.dumps(json_obj, indent=4)
    with open(output_file, 'w') as f:
        f.write(json_data)
        print("-> Finished Service-Catalog and stored in",output_file)

def print_tree(json_data):
    root_nodes = find_root_nodes(json_data)
    for node_id in root_nodes:
            print_tree_node(node_id,json_data)

def print_tree_node(node_id,json_data,depth=0):
    node = json_data[node_id]
    print("\t"*depth,"("+node["type"]+")",node["id"])
    if "children" in node:
        for child_id in node["children"]: 
            print_tree_node(child_id,json_data,depth+1)

def main(output_file,path,schema_path):    
    json_fragments_list = read_JSON_from_file(path,schema_path)
    add_parent_attribute(json_fragments_list)
    generate_json_output(json_fragments_list,output_file)
    return json_fragments_list
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Create Service Catalog',
        description='Compile partial JSON fragments of a service catalog to full service catalog description.')
    parser.add_argument('--verbose', '-v', action='count', default=1)
    parser.add_argument('--version', action='version', version='%(prog) Version 0.1')
    parser.add_argument('--schema','-s', default="schemas/service-catalog.json", nargs='?')
    parser.add_argument('--partials','-p', default="../test/partials", nargs='?' )
    parser.add_argument('--output','-o', default="../test/service-catalog.json", nargs='?')
    args = parser.parse_args()
    output_file:str = args.output
    path:str = args.partials
    schema_path:str = args.schema
    verbose = args.verbose
    structure = main(output_file,path,schema_path)

    if verbose:
        print_tree(structure)

