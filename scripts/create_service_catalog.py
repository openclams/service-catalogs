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


def make_tree_structure(json_fragments_list: Dict[str,Any]) -> Any:
    tree:List[Any] = []
    root_ids = find_root_nodes(json_fragments_list)
    is_used_list_global:List[str] = []
    for root_node_id in root_ids:
        is_used_list:List[str] = []
        tree.append(get_child_with_children(
                                root_node_id,
                                json_fragments_list,
                                is_used_list,
                                is_used_list_global)
                    )    

    return tree

def find_root_nodes(json_fragments_list):
    list_of_all_children_ids = []
    for node_id in json_fragments_list:
        if json_fragments_list[node_id]["type"] == "Node" and "children" in json_fragments_list[node_id]:
            list_of_all_children_ids.extend(json_fragments_list[node_id]["children"])

    return [node_id for node_id in json_fragments_list if node_id not in list_of_all_children_ids]


def get_child_with_children(node_id:Any, json_fragments_list:Dict[str,Any],is_used_list:List[str],is_used_list_global:List[str]):
    if node_id in is_used_list:
        print("Error: Circualar structure detected around Id:",node_id)
        print("Abort!")
        exit(0)
    else:
        is_used_list.append(node_id)
    
    is_used_list_global.append(node_id)
    node = json_fragments_list[node_id]

    if node["type"] == "Node" and  "children" in node and len(node["children"]):
        #At the begining, the children propertie is a list of ids of type string.
        #We replace piecewise each string with the actual object recursivley.
        for idx in range(len(node["children"])):
            node_obj = node["children"][idx]
           
            if not isinstance(node_obj, str):
                continue

            if node_obj in json_fragments_list:
                child_node = json_fragments_list[node_obj]
                #if child_node['id'] in is_used_list_global:
                #TODO  child_node = branch_node_create_copy(child_node,json_fragments_list,is_used_list_global)
                node["children"][idx] = child_node
                get_child_with_children(child_node["id"], json_fragments_list, is_used_list,is_used_list_global)
            else:
                child_node["children"].remove(node_obj) 
                print("Error: Id of child node no found.")
                print("Node Id:",node_obj,'in parent node',child_node["id"],"not found.")
                print("Node with Id:'"+node_obj+"'is ignored.")

    return  node  

def branch_node_create_copy(node,json_fragments_list,is_used_list_global):
        new_node = node.copy()
        if re.match(r'.*\_\d+$',node['id']):
            new_node['id'] = re.sub(r'(\d+)$', lambda x: str(int(x.group(0)) + 1), node['id'])
        else:
            new_node['id'] = node['id']+"_1"
        print("-> Node ",node['id'],"has mutltiple parents; create new subtree by inserting a copy with Id",new_node['id'])
        json_fragments_list[new_node['id']] = new_node
        return new_node


def inherit_attributes_from_parents(tree):
    for node in tree:
        if node["type"] == "Node":
            inherite_attributes(node,tree)
    
def inherite_attributes(node,tree):
    for child in node["children"]:
        attr = node["attr"].copy()
        attr.update(child["attr"])
        child["attr"] = attr
        inherite_attributes(child,tree)

def generate_json_output(tree,output_file):
    json_obj = {
        "Nodes": [node for node in tree if node["type"] == "Node"],
        "Edges": [node for node in tree if node["type"] == "Edge"],
        "Templates": [node for node in tree if node["type"] == "Template"]
    }
    json_data = json.dumps(json_obj, indent=4)
    with open(output_file, 'w') as f:
        f.write(json_data)
        print("-> Finished Service-Catalog and stored in",output_file)

def print_tree(tree):
    for node in tree:
            print_tree_node(node)

def print_tree_node(node=None,depth=0):
    print("\t"*depth,"("+node["type"]+")",node["id"])
    if "children" in node:
        for child in node["children"]: 
            print_tree_node(child,depth+1)

def main(output_file,path,schema_path):    
    json_fragments_list = read_JSON_from_file(path,schema_path)
    tree = make_tree_structure(json_fragments_list)
    inherit_attributes_from_parents(tree)
    generate_json_output(tree,output_file)
    return tree
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Create Service Catalog',
        description='Compile partial JSON fragments of a service catalog to full service catalog description.')
    parser.add_argument('--verbose', '-v', action='count', default=1)
    parser.add_argument('--version', action='version', version='%(prog) Version 0.1')
    parser.add_argument('--schema','-s', default="../schemas/service-catalog.json", nargs='?')
    parser.add_argument('--partials','-p', default="../test/partials", nargs='?' )
    parser.add_argument('--output','-o', default="../test/service-catalog.json", nargs='?')
    args = parser.parse_args()
    output_file:str = args.output
    path:str = args.partials
    schema_path:str = args.schema
    verbose = args.verbose
    tree = main(output_file,path,schema_path)

    if verbose:
        print_tree(tree)

