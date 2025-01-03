#!/usr/local/cs/bin/python3
import os, sys, zlib
import copy

class commit_node:
    def __init__(self, commit_hash):
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()

def find_git_dir():
    cwd = os.getcwd()
    while True:
        if os.path.isdir(".git"):
            return cwd
        else:
            parent = os.path.dirname(cwd)
            if cwd == parent:
                print("Not inside a Git repository")
                sys.exit(1)
            else:
                cwd = parent

def get_branch_list(directory):
    branch_list = []
    branch_dir = os.path.join(directory, '.git', 'refs', 'heads')
    check_for_slash_case(branch_dir, '', branch_list)
    return branch_list

def check_for_slash_case(cur_path, relative_path, branch_list):
    ref_list = os.listdir(cur_path)
    for ref in ref_list:
        path_check = os.path.join(cur_path, ref)
        cur_branch = relative_path + ref
        if os.path.isdir(path_check):
            check_for_slash_case(path_check, cur_branch + '/', branch_list)
        elif os.path.isfile(path_check):
            with open(path_check, 'r') as f:
                commit_hash = f.read().strip()
                branch_list.append((cur_branch, commit_hash))
            
def get_commit_graph(hashes):
    node_graph = {}
    visited = set()
    branch_list = hashes
    while branch_list:
        current_hash = branch_list.pop()
        if current_hash in visited:
            continue
        else:
            visited.add(current_hash)
            if current_hash not in node_graph:
                node_graph[current_hash] = commit_node(current_hash)
            parents = get_parents(current_hash)
            cur_node = node_graph[current_hash]
            for parent_hash in parents:
                if parent_hash not in visited:
                    branch_list.append(parent_hash)
                if parent_hash not in node_graph:
                    node_graph[parent_hash] = commit_node(parent_hash)
                node_graph[parent_hash].children.add(current_hash)
                cur_node.parents.add(parent_hash)
    return node_graph

def get_parents(hash):
    parents = []
    git_dir = find_git_dir()
    parent_path = os.path.join(git_dir, '.git', 'objects', hash[:2], hash[2:])
    if os.path.exists(parent_path):
        with open(parent_path, 'rb') as f:
            compress_data = f.read()
            uncompress_data = zlib.decompress(compress_data)
            string_data = uncompress_data.decode('utf_8')
        data_lines = string_data.split()
        for i in range(len(data_lines)):
            if data_lines[i] == "parent":
                parents.append(data_lines[i+1])
    return parents

def get_topo_ordering(commits):
    sorted_list = []
    commit_list = copy.deepcopy(commits)
    no_kids_list = []
    for commit in commit_list:
        if not commit_list[commit].children:
            no_kids_list.append(commit_list[commit])
    while len(no_kids_list) > 0:
        curr = no_kids_list.pop()
        sorted_list.append(curr)
        for parent in list(curr.parents):
            parent_node = commit_list[parent]
            parent_node.children.discard(curr.commit_hash)
            if not any(parent_node.children):
                no_kids_list.append(parent_node)
    if len(sorted_list) != len(commits):
        print("Cycle Detected")
        sys.exit(1)
    else:
        return sorted_list

def print_hashes(topo_ordered_commits, branch_list, commit_graph):
    jumped = False
    for i in range(len(topo_ordered_commits)):
        node = topo_ordered_commits[i]
        print_string = node.commit_hash

        #check for branch(it's branch name to hash)
        for branch in branch_list:
            if(branch[1] == node.commit_hash):
                print_string += ' ' + branch[0]

        #check if need to output sticky end
        if i + 1 < len(topo_ordered_commits):
            next_node = topo_ordered_commits[i+1]
            if next_node.commit_hash not in node.parents:
                print_string += '\n'
                isFirst = True
                sorted_parents = sorted(node.parents)
                for parent in sorted_parents:
                    if(isFirst):
                        print_string += parent
                        isFirst = False
                    else:
                        print_string += ' ' + parent
                print_string += '=' + '\n'
                jumped = True
                    
        #output
        print(print_string)

        #output a stick front if you outputted a sticky end
        if(jumped):
            next_node = topo_ordered_commits[i+1]
            front_out = '='
            isFirst = True
            sorted_children = sorted(commit_graph[next_node.commit_hash].children)
            for child in sorted_children:
                if isFirst:
                    front_out += child
                    isFirst = False
                else:
                    front_out += ' ' + child
            print(front_out)
            jumped = False

def topo_order_commits():
    path = find_git_dir()
    branch_list = get_branch_list(path)
    branch_hash_list = []
    for branch in branch_list:
        branch_hash_list.append(branch[1])
    commit_graph = get_commit_graph(branch_hash_list)
    topo_list = get_topo_ordering(commit_graph)
    print_hashes(topo_list, branch_list, commit_graph)

if __name__ == '__main__':
    topo_order_commits()
