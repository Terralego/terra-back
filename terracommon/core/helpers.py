import csv
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


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


class Choices:
    """
    Class under GPL Licence from:
    https://github.com/liberation/django-extended-choices/
    Helper class for choices fields in Django.
    A choice value has three representation (constant name, value and
    string). So Choices takes list of such tuples.
    Here is an example of Choices use:
    >>> CHOICES_ALIGNEMENT = Choices(
    ...     ('BAD', 10, u'bad'),
    ...     ('NEUTRAL', 20, u'neutral'),
    ...     ('CHAOTIC_GOOD', 30, u'chaotic good'),
    ...     ('GOOD', 40, u'good'),
    ... )
    >>> CHOICES_ALIGNEMENT.BAD
    10
    >>> CHOICES_ALIGNEMENT.CHOICES_DICT[30]
    u'chaotic good'
    >>> CHOICES_ALIGNEMENT.REVERTED_CHOICES_DICT[u'good']
    40
    As you can see in the above example usage, Choices objects gets three
    attributes:
    - one attribute built after constant names provided in the tuple (like BAD,
      NEUTRAL etc...)
    - a CHOICES_DICT that match value to string
    - a REVERTED_CHOICES_DICT that match string to value
    If you want to create subset of choices, you can
    use the add_subset method
    This method take a name, and then the constants you want to
    have in this subset:
    >>> CHOICES_ALIGNEMENT.add_subset('WESTERN',('BAD', 'GOOD'))
    >>> CHOICES_ALIGNEMENT.WESTERN
    ((10, u'bad'), (40, u'good'))
    """

    def __init__(self, *raw_choices, **kwargs):
        self._CHOICES = None
        self._CHOICES_DICT = None
        self._REVERTED_CHOICES_DICT = None
        self._VALUE_TO_CONST = None
        self._RAW_CHOICES = None
        self._CONSTS = []
        self._CONST_CHOICES = None
        self.parent = None
        if "parent" in kwargs:  # 'subchoice' mode
            self.parent = kwargs["parent"]
            self._CONSTS = kwargs["CONSTS"]
        else:
            name = kwargs.get('name', 'CHOICES')  # retrocompatibility
            if name != "CHOICES":  # retrocompatibility
                self._RAW_CHOICES = tuple()
                self.add_choices(name, *raw_choices)
            else:
                self._RAW_CHOICES = raw_choices  # default behaviour
                self._make_consts(*raw_choices)

    def _make_consts(self, *raw_choices):
        for choice in raw_choices:
            const, value, string = choice
            if hasattr(self, const):
                raise ValueError("You cannot declare two constants "
                                 "with the same name! %s " % str(choice))
            if value in [getattr(self, c) for c in self._CONSTS]:
                raise ValueError("You cannot declare two constants "
                                 "with the same value! %s " % str(choice))
            setattr(self, const, value)
            self._CONSTS.append(const)

            # retrocompatibilty
            self._CHOICES = None
            self._CHOICES_DICT = None
            self._REVERTED_CHOICES_DICT = None

    def add_choices(self, name="CHOICES", *raw_choices):
        # for retrocompatibility
        # we may have to call _build_choices
        # more than one time and so append the
        # new choices to the already existing ones
        RAW_CHOICES = list(self._RAW_CHOICES)
        self._RAW_CHOICES = tuple(RAW_CHOICES + list(raw_choices))
        self._make_consts(*raw_choices)
        if name != "CHOICES":
            # for retrocompatibility
            # we make a subset with new choices
            constants_for_subset = []
            for choice in raw_choices:
                const, value, string = choice
                constants_for_subset.append(const)
            self.add_subset(name, constants_for_subset)

    def add_subset(self, name, constants):
        if hasattr(self, name):
            raise ValueError("Cannot use %s as a subset name."
                             "It's already an attribute." % name)

        subset = Choices(parent=self, CONSTS=constants)
        setattr(self, name, subset)

        # For retrocompatibility
        setattr(self, '%s_DICT' % name, getattr(subset, "CHOICES_DICT"))
        setattr(self, 'REVERTED_%s_DICT' % name,
                getattr(subset, "REVERTED_CHOICES_DICT"))

    @property
    def RAW_CHOICES(self):
        if self._RAW_CHOICES is None:
            if self.parent:
                self._RAW_CHOICES = tuple((c, k, v) for c, k, v
                                          in self.parent.RAW_CHOICES
                                          if c in self._CONSTS)
            else:
                raise ValueError("Implementation problem : first "
                                 "ancestor should have a _RAW_CHOICES")
        return self._RAW_CHOICES

    @property
    def CHOICES(self):
        """
        Tuple of tuples (value, display_value).
        """
        if self._CHOICES is None:
            self._CHOICES = tuple((k, v) for c, k, v in self.RAW_CHOICES
                                  if c in self._CONSTS)
        return self._CHOICES

    @property
    def CHOICES_DICT(self):
        if self._CHOICES_DICT is None:
            self._CHOICES_DICT = {}
            for c, k, v in self.RAW_CHOICES:
                if c in self._CONSTS:
                    self._CHOICES_DICT[k] = v
        return self._CHOICES_DICT

    @property
    def REVERTED_CHOICES_DICT(self):
        """
        Dict {"display_value": "value"}
        """
        # FIXME: rename in a more friendly name, like STRING_TO_VALUE?
        if self._REVERTED_CHOICES_DICT is None:
            self._REVERTED_CHOICES_DICT = {}
            for c, k, v in self.RAW_CHOICES:
                if c in self._CONSTS:
                    self._REVERTED_CHOICES_DICT[v] = k
        return self._REVERTED_CHOICES_DICT

    @property
    def VALUE_TO_CONST(self):
        """
        Dict {"value": "const"}
        """
        if self._VALUE_TO_CONST is None:
            self._VALUE_TO_CONST = {}
            for c, k, v in self.RAW_CHOICES:
                if c in self._CONSTS:
                    self._VALUE_TO_CONST[k] = c
        return self._VALUE_TO_CONST

    @property
    def CONST_CHOICES(self):
        """
        Tuple of tuples (constant, display_value).
        """
        if self._CONST_CHOICES is None:
            self._CONST_CHOICES = tuple((c, v) for c, k, v in self.RAW_CHOICES
                                        if c in self._CONSTS)
        return self._CONST_CHOICES

    def __contains__(self, item):
        """
        Make smarter to check if a value is valid for a Choices.
        """
        return item in self.CHOICES_DICT

    def __iter__(self):
        return self.CHOICES.__iter__()

    def __eq__(self, other):
        return other == self.CHOICES

    def __ne__(self, other):
        return other != self.CHOICES

    def __len__(self):
        return self.CHOICES.__len__()

    def __add__(self, item):
        """
        Needed to make MY_CHOICES + OTHER_CHOICE
        """
        if not isinstance(item, (Choices, tuple)):
            raise ValueError("This operand could only by evaluated "
                             "with Choices or tuple instances. "
                             "Got %s instead." % type(item))
        return self.CHOICES + tuple(item)

    def __repr__(self):
        return self.CHOICES.__repr__()
