import json
import uuid
import time

class LoomTree:
    def __init__(self, id, text, children=None):
        self.id = id
        self.text = text
        self.children = children if children is not None else []

    def add_child(self, child):
        self.children.append(child)


def to_pyloom_format(tree):
    def build_node(node):
        node_data = {
            "id": node.id,
            "text": node.text,
            "children": [build_node(child) for child in node.children]
        }
        return node_data

    # root_id = tree.id
    root_node = build_node(tree)
    pyloom_data = {"root": root_node}

    return pyloom_data


def from_pyloom_format(pyloom_data):
    pyloom_data = json.loads(pyloom_data)  # Parse the string into a dictionary

    def build_tree(node_data):
        children = [build_tree(child_data) for child_data in node_data["children"]]
        return LoomTree(id=node_data.get("id"), text=node_data["text"], children=children)

    root_node = pyloom_data["root"]
    loom_tree = build_tree(root_node)

    return loom_tree

def to_loomsidian_format(loom_tree):
    def build_node(node):
        node_id = str(uuid.uuid4())
        children_ids = [build_node(child) for child in node.children]

        return {
            "text": node.text,
            "parentId": None,  # We'll populate this later
            "unread": False,
            "collapsed": False,
            "bookmarked": False,
            "color": None,
            "lastVisited": int(time.time() * 1000),  # Convert current timestamp to milliseconds
            "children": children_ids
        }

    root_node = build_node(loom_tree)
    parent_child_relationship = {}

    def update_parent_id(node):
        node_id = str(uuid.uuid4())  # Use UUID as the node ID
        parent_child_relationship[node_id] = node

        for child in node["children"]:
            child["parentId"] = node_id
            update_parent_id(child)

    update_parent_id(root_node)

    # Extract the ID of the root node
    root_id = next(iter(parent_child_relationship))

    # Update the parent ID of the root node
    root_node["parentId"] = None

    return {
        "hoisted": [],
        "nodes": parent_child_relationship,
        "current": root_id,
        "generating": None
    }



def from_loomsidian_format(json_str):
    data = json.loads(json_str)

    def build_tree(node_id):
        node_data = data["nodes"][node_id]
        children = [build_tree(child_id) for child_id in data["nodes"] if data["nodes"][child_id]["parentId"] == node_id]
        return LoomTree(id=node_id, text=node_data["text"], children=children)

    root_ids = [node_id for node_id in data["nodes"] if data["nodes"][node_id]["parentId"] is None]
    trees = [build_tree(root_id) for root_id in root_ids]
    
    if len(trees) == 1:
        return trees[0]
    else:
        # If there are multiple root nodes, create a new root node and make the existing trees its children
        return LoomTree(id=uuid.uuid4(), text="", children=trees)



# if __name__ == '__main__':
#     with open("G:/Loom/newsun.json", "r") as f:
#         treedata = f.read()

#     loom_tree = from_loomsidian_format(treedata)
#     pyloom_data = to_pyloom_format(loom_tree)
#     print(pyloom_data)
#     pyloom_data = json.dumps(pyloom_data)
#     loom_tree = from_pyloom_format(pyloom_data)
#     loomsidian_data = to_loomsidian_format(loom_tree)
#     print(loomsidian_data)