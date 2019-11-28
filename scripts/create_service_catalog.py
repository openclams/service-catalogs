import glob
import os
import json
from typing import List, Set, Dict, Tuple, Optional, Any
import jsonschema

output_file:str = "../test/service-catalog.json"
path:str = "../test/partials"
schema_path:str = "../schemas/service-catalog.json"


def read_JSON_from_file() ->  Dict[str,Any]:
    json_fragments_list: Dict[str,Any] = {}
    with open(schema_path, 'r') as schema_file:
        json_schema = json.load(schema_file)


    for json_file_path in glob.glob(path+"/*.json"):
        print("-> Open JSON Fragment: ",json_file_path)
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

# def make_tree_structure(json_fragments_list: Dict[str,Any]) -> Any:
#     tree:List[Any] = []
#     node_ids = list(json_fragments_list.keys())
#     for node_id in node_ids:
#         if node_id in json_fragments_list:
#             tree_node = json_fragments_list[node_id]
#             node_objs = get_child_with_children(tree_node,json_fragments_list,[])
#             tree.append(node_objs)
#     return tree    

def make_tree_structure(json_fragments_list: Dict[str,Any]) -> Any:
    tree:List[Any] = []
    root_ids = find_root_nodes(json_fragments_list)
    is_used_list:List[str] = []
    for root_node_id in root_ids:
        tree.append(get_child_with_children(root_node_id,json_fragments_list,is_used_list))    

    return tree

def find_root_nodes(json_fragments_list):
    list_of_all_children_ids = []
    for node_id in json_fragments_list:
        if json_fragments_list[node_id]["type"] == "Node" and "children" in json_fragments_list[node_id]:
            list_of_all_children_ids.extend(json_fragments_list[node_id]["children"])

    return [node_id for node_id in json_fragments_list if node_id not in list_of_all_children_ids]


def get_child_with_children(node_id:Any, json_fragments_list:Dict[str,Any],is_used_list:List[str]):
    if node_id in is_used_list:
        pass
        # print("Error: Circualar structure detected around Id:",child_node["id"])
        # print("Abort!")
        # exit(0)
    else:
        is_used_list.append(node_id)

    node = json_fragments_list[node_id]

    if node["type"] == "Node" and  "children" in node and len(node["children"]):
        for idx in range(len(node["children"])):
            node_obj = node["children"][idx]
            #Check if this node has all ids replaced yet
            if not isinstance(node_obj, str):
                continue
            
            #We did not iterate over this node
            #Replace all Ids with their corresponding children nodes
            if node_obj in json_fragments_list:
                child_node = json_fragments_list[node_obj]
                node["children"][idx] = child_node
                get_child_with_children(child_node["id"], json_fragments_list, is_used_list)
            else:
                child_node["children"].remove(node_obj) 
                print("Error: Id of child node no found.")
                print("Node Id:",node_obj,'in parent node',child_node["id"],"not found.")
                print("Node with Id:'"+node_obj+"'is ignored.")

    return  node  

# def get_child_with_children(child_node:Any, json_fragments_list:Dict[str,Any],is_used_list:List[str]):
#     if child_node["id"] in is_used_list:
#         print("Error: Circualar structure detected around Id:",child_node["id"])
#         print("Abort!")
#         exit(0)
#     else:
#         is_used_list.append(child_node["id"])

#     if child_node["type"] == "Node" and  "children" in child_node and len(child_node["children"]):
#         children_objs = child_node["children"]
#         child_node_buffer = []
#         for node_obj in children_objs:
            
#             #Check if this node has all ids replaced yet
#             if not isinstance(node_obj, str):
#                 return child_node
            
#             #We did not iterate over this node
#             #Replace all Ids with their corresponding children nodes
#             if node_obj in json_fragments_list:
#                 node = json_fragments_list[node_obj]
#                 child_nodes = get_child_with_children(node, json_fragments_list, is_used_list)
#                 child_node_buffer.append(child_nodes)
#             else:
#                 child_node["children"].remove(node_obj) 
#                 print("Error: Id of child node no found.")
#                 print("Node Id:",node_obj,'in parent node',child_node["id"],"not found.")
#                 print("Node with Id:'"+node_obj+"'is ignored.")
#         child_node["children"] = child_node_buffer.copy()
      
#     del json_fragments_list[child_node["id"]]
#     return  child_node     

#This methode removes subtress that are already existing in bigger trees
# Example: Two entries: 
# 1. database--> key-value-storage--> redis 
# 2. key-value-storage--> redis 
# The 2. entry will be removed, because it already has a parent in entry 1.
def remove_duplicate_sup_trees(tree):
    mark_for_removal = []
    for node_a in tree:
        if not node_a["type"] == "Node":
            continue
        
        for node_b in tree: 
            if not node_a["type"] == "Node" or node_a["id"] == node_b["id"]:
                continue

            if(is_sub_tree(node_a,node_b)):
                print("-> Found sub-tree for id",node_a["id"],"in",node_b["id"])
                mark_for_removal.append(node_a) 

    for node in mark_for_removal:
        tree.remove(node)
    return tree

def is_sub_tree(node_a, node_b):
    if node_a["id"] == node_b["id"]:
        return True

    if "children" in node_b:
        for child in node_b["children"]:
            return is_sub_tree(node_a,child)

    return False

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

def main():    
    json_fragments_list = read_JSON_from_file()
    tree = make_tree_structure(json_fragments_list)
    super_tree = tree #remove_duplicate_sup_trees(tree)
    inherit_attributes_from_parents(super_tree)
    print_tree(tree)
    generate_json_output(super_tree,output_file)
    
if __name__ == '__main__':
    main()

