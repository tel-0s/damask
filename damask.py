import json
import uuid
import time

class LoomTree:
    def __init__(self, node_id, text, children=None):
        self.node_id = node_id
        self.text = text
        self.children = children if children is not None else []

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        return f"LoomTree(node_id={self.node_id}, text={self.text}, children={[str(child) for child in self.children]})"

def to_pyloom_format(tree):
    def build_node(node):
        node_data = {
            "id": node.node_id,
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
        return LoomTree(node_id=node_data.get("id"), text=node_data["text"], children=children)

    root_node = pyloom_data["root"]
    loom_tree = build_tree(root_node)

    return loom_tree

def to_loomsidian_format(loom_tree):
    def build_node(node):
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
        return LoomTree(node_id=node_id, text=node_data["text"], children=children)

    root_ids = [node_id for node_id in data["nodes"] if data["nodes"][node_id]["parentId"] is None]
    trees = [build_tree(root_id) for root_id in root_ids]
    
    if len(trees) == 1:
        return trees[0]
    else:
        # If there are multiple root nodes, create a new root node and make the existing trees its children
        return LoomTree(node_id=uuid.uuid4(), text="", children=trees)

def from_bonsai_format(bonsai_data):
    bonsai_data = json.loads(bonsai_data)

    # Create a dictionary to store the parent-child relationships
    parent_child_relationship = {}

    # Build the LoomTree nodes
    def build_node(node_data):
        children = []
        for child_id in node_data["childrenIds"]:
            child_node = next((child for child in bonsai_data["nodes"] if child["id"] == child_id), None)
            if child_node:
                children.append(build_node(child_node))
        return LoomTree(node_id=node_data["id"], text=node_data["text"], children=children)

    # Create the root node
    root_node_data = bonsai_data["nodes"][0]
    root_node = build_node(root_node_data)
    parent_child_relationship[root_node_data["id"]] = root_node

    # Build the parent-child relationships
    for edge in bonsai_data["edges"]:
        parent_id = edge["from"]
        child_id = edge["to"]
        parent_node = parent_child_relationship.get(parent_id)
        child_node = parent_child_relationship.get(child_id)
        if parent_node and child_node:
            parent_node.add_child(child_node)

    return root_node

def to_bonsai_format(loom_tree):
    def build_node(node):
        children_ids = [child.node_id for child in node.children]

        node_data = {
            "id": node.node_id,
            "text": node.text,
            "childrenIds": children_ids,
            "parentIds": [],  # We'll populate this later
            "group": "normal",
            "visible": True,
            "tags": [],
            "createdAt": int(time.time() * 1000),  # Convert current timestamp to milliseconds
            "lastVisited": int(time.time() * 1000),  # Convert current timestamp to milliseconds
            "lastUpdated": int(time.time() * 1000),  # Convert current timestamp to milliseconds
            "logprobs": None,
            "generationSettings": None,
            "label": ""
        }

        return node_data

    root_node = build_node(loom_tree)
    nodes = [root_node]
    edges = []

    def traverse_tree(node):
        nonlocal nodes, edges

        for child in node.children:
            child_data = build_node(child)
            nodes.append(child_data)
            edges.append({"from": node.node_id, "to": child.node_id, "relation": "parentId"})

            # Populate parentIds of the child
            child_data["parentIds"] = [node.node_id]

            traverse_tree(child)

    traverse_tree(loom_tree)

    bonsai_data = {
        "nodes": nodes,
        "edges": edges,
        "name": "graph_1",
        "pathNodes": [root_node["id"]],
        "focusedId": root_node["id"]
    }

    return json.dumps(bonsai_data)


# if __name__ == '__main__':
#     with open("G:/Loom/newsun.json", "r") as f:
#         treedata = f.read()

#     loom_tree = from_loomsidian_format(treedata)
#     pyloom_data = to_pyloom_format(loom_tree)
#     print("\n\nPYLOOMDATA\n"+str(pyloom_data))
#     pyloom_data = json.dumps(pyloom_data)
#     loom_tree = from_pyloom_format(pyloom_data)
#     print("\n\nLOOMDATA\n"+str(loom_tree))
#     bonsai_data = to_bonsai_format(loom_tree)
#     print("\n\nBONSAIDATA\n"+str(bonsai_data))
#     bonsai_data = json.dumps(bonsai_data)
#     loom_tree = from_bonsai_format(json.loads(bonsai_data))
#     loomsidian_data = to_loomsidian_format(loom_tree)
#     print("\n\nLOOMSIDIANDATA\n"+str(loomsidian_data))