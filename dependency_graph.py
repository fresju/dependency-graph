import os
import re
import argparse
import codecs
from collections import defaultdict
from graphviz import Digraph

include_regex = re.compile(r'#include\s+["<](.*)[">]')
valid_headers = [['.h', '.hpp'], 'red']
valid_sources = [['.c', '.cc', '.cpp'], 'blue']
valid_extensions = valid_headers[0] + valid_sources[0]


def normalize(path):
    """ Return the name of the node that will represent the file at path. """
    filename = os.path.basename(path)
    end = filename.rfind('.')
    end = end if end != -1 else len(filename)
    return filename[:end]


def get_extension(path):
    """ Return the extension of the file targeted by path. """
    return path[path.rfind('.'):]


def find_all_files(path, ignore, recursive=True):
    """
    Return a list of all the files in the folder.
    If recursive is True, the function will search recursively.
    """
    files = []
    for entry in os.scandir(path):
        if entry.is_dir() and recursive:
            if entry.name not in ignore:
                files += find_all_files(entry.path, ignore)
        elif get_extension(entry.path) in valid_extensions:
            files.append(entry.path)
    return files


def find_neighbors(path):
    """ Find all the other nodes included by the file targeted by path. """
    f = codecs.open(path, 'r', "utf-8", "ignore")
    code = f.read()
    f.close()
    return [normalize(include) for include in include_regex.findall(code)]


def create_graph(folder, create_cluster, label_cluster, strict, recursive, ignore):
    """ Create a graph from a folder. """
    # Find nodes and clusters
    files = find_all_files(folder, ignore, recursive=recursive)
    folder_to_files = defaultdict(list)
    for path in files:
        dir_name = os.path.dirname(path)
        if dir_name not in ignore:
            folder_to_files[dir_name].append(path)
    nodes = []
    for path in files:
        normalized_path = normalize(path)
        if normalized_path not in ignore:
            nodes.append(normalized_path)
    # Create graph
    graph = Digraph(strict=strict)
    # Find edges and create clusters
    for folder in folder_to_files:
        with graph.subgraph(name='cluster_{}'.format(folder)) as cluster:
            for path in folder_to_files[folder]:
                color = 'black'
                node = normalize(path)
                if node not in nodes:
                    continue
                ext = get_extension(path)
                if ext in valid_headers[0]:
                    color = valid_headers[1]
                if ext in valid_sources[0]:
                    color = valid_sources[1]
                if create_cluster:
                    cluster.node(node)
                else:
                    graph.node(node)
                neighbors = find_neighbors(path)
                for neighbor in neighbors:
                    if neighbor != node and neighbor in nodes:
                        graph.edge(node, neighbor, color=color)
            if create_cluster and label_cluster:
                cluster.attr(label=folder)
    return graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help='Path to the folder to scan')
    parser.add_argument('output', help='Path of the output file without the extension')
    parser.add_argument('-f', '--format', help='Format of the output', default='pdf',
                        choices=['bmp', 'gif', 'jpg', 'png', 'pdf', 'svg'])
    parser.add_argument('-v', '--view', action='store_true', help='View the graph')
    parser.add_argument('-c', '--cluster', action='store_true', help='Create a cluster for each subfolder')
    parser.add_argument('--cluster-labels', dest='cluster_labels', action='store_true', help='Label subfolder clusters')
    parser.add_argument('-s', '--strict', action='store_true', help='Rendering should merge multi-edges', default=False)
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively parse sub-folders', default=False)
    parser.add_argument('-i', '--ignore', action='append', help='Ignore file or folder', default=[])
    args = parser.parse_args()
    normalized_ignore = [normalize(path) for path in args.ignore]
    graph = create_graph(args.folder, args.cluster, args.cluster_labels, args.strict, args.recursive, normalized_ignore)
    graph.format = args.format
    graph.render(args.output, cleanup=True, view=args.view)


if __name__ == '__main__':
    main()
