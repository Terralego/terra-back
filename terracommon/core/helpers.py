import csv
import logging
import os
import zipfile
from copy import deepcopy
from io import BytesIO

logger = logging.getLogger(__name__)


def make_zipfile_bytesio(base_dir):
    zip_file = BytesIO()

    with zipfile.ZipFile(zip_file, "w",
                         compression=zipfile.ZIP_DEFLATED) as zf:
        path = os.path.normpath(base_dir)
        if path != os.curdir and path != base_dir:
            zf.write(path, os.path.relpath(path, base_dir))
            logger.info("adding '%s'", path)
        for dirpath, dirnames, filenames in os.walk(base_dir):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_dir))
                logger.info("adding '%s'", path)
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_dir))
                    logger.info("adding '%s'", path)

    return zip_file


class CustomCsvBuilder:
    """ Build csv file from dict/list data """

    def __init__(self, data):
        self.data = data

    def build_header(self, data, parent_key=None):
        header = []

        if isinstance(data, dict):
            for colname, colvalue in data.items():
                full_colname = colname
                if parent_key:
                    full_colname = (parent_key
                                    if colname in parent_key
                                    else '_'.join((parent_key, colname)))

                partial_header = self.build_header(
                    colvalue,
                    parent_key=full_colname,
                )

                header += partial_header

        elif isinstance(data, list):
            if parent_key:
                header.append(parent_key)
            for val in data:
                header += self.build_header(val, parent_key=parent_key)

        else:
            if parent_key:
                header.append(parent_key)
        return set(header)

    def flatten_datatree(self, tree, parent='', sep='_'):
        flatten_tree = []
        if isinstance(tree, dict):
            self._tree_flattend(flatten_tree, tree, parent, sep)
        elif isinstance(tree, list):
            self._list_flattend(flatten_tree, tree, parent, sep)
        else:
            flatten_tree.append({parent: tree})
        return flatten_tree

    def _list_flattend(self, flatten_tree, tree, parent='', sep='_'):
        for i, sibling in enumerate(tree):
            flatten_sibling = self.flatten_datatree(sibling, parent=parent)
            flatten_tree.extend(flatten_sibling)

    def _tree_flattend(self, flatten_tree, tree, parent='', sep='_'):
        for node, child in tree.items():
            parent_node = node if not parent else sep.join((parent, node))
            flatten_child = self.flatten_datatree(child,
                                                  parent=parent_node)

            if not flatten_tree:
                flatten_tree.extend(flatten_child)
            else:
                for i, sub_child in enumerate(flatten_child):
                    for sub_tree in flatten_tree:
                        if sub_child.keys() <= sub_tree.keys():
                            subtree_copy = deepcopy(sub_tree)
                            subtree_copy.update(sub_child)
                            flatten_tree.append(subtree_copy)
                            break
                    else:
                        try:
                            flatten_tree[i].update(sub_child)
                        except IndexError:
                            flatten_tree.append(sub_child)

    def create_csv(self, output):
        self.csv = output

        header = self.build_header(self.data)
        body = self.flatten_datatree(self.data)

        writer = csv.DictWriter(self.csv, fieldnames=header)

        writer.writeheader()
        for element in body:
            writer.writerow(element)
        output.seek(0)
