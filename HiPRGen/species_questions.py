from HiPRGen.mol_entry import *
import networkx as nx
from networkx.algorithms.graph_hashing import weisfeiler_lehman_graph_hash
import copy
from functools import partial
from HiPRGen.constants import *


"""
species decision tree:

A question is a function q(mol_entry) -> Bool

Unlike for reaction filtering, these questions should not modify the mol_entry in any way.

A node is either a Terminal or a non empty list [(question, node)]

class Terminal(Enum):
    KEEP = 1
    DISCARD = -1

For the return value of a question, True means travel to this node and False means try next question in the list.

for non terminal nodes, it is an error if every question returns False. i.e getting stuck at a non terminal node is an error.

Once a Terminal node is reached, it tells us whether to keep or discard the species.
"""

def run_decision_tree(mol_entry,
                      decision_tree,
                      decision_pathway=None):

    node = decision_tree

    while type(node) == list:
        next_node = None
        for (question, new_node) in node:
            if question(mol_entry):

                # if decision_pathway is a list,
                # append the question which
                # answered true i.e the edge we follow
                if decision_pathway is not None:
                    decision_pathway.append(question)


                next_node = new_node
                break

        node = next_node


    if type(node) == Terminal:
        if decision_pathway is not None:
            decision_pathway.append(node)


        if node == Terminal.KEEP:
            return True
        else:
            return False
    else:
        print(node)
        raise Exception("unexpected node type reached")



def metal_ion_filter(mol_entry):
    "only allow positively charged metal ions"
    if mol_entry.formula in m_formulas and mol_entry.charge <= 0:
        return True
    else:
        return False


def mol_not_connected(mol):
    return not nx.is_connected(mol.graph)


def add_star_hashes(mol):

    for i in range(mol.num_atoms):
        if i not in mol.m_inds:
            neighborhood = nx.generators.ego.ego_graph(
                mol.covalent_graph,
                i,
                1,
                undirected=True)

            mol.star_hashes[i] = weisfeiler_lehman_graph_hash(
                neighborhood,
                node_attr='specie')

    return False


def add_fragment_hashes(mol):
    if mol.formula in m_formulas:
        return False


    for edge in mol.covalent_graph.edges:
        h = copy.deepcopy(mol.covalent_graph)
        h.remove_edge(*edge)
        connected_components = nx.algorithms.components.connected_components(h)
        fragment_hashes = [
            weisfeiler_lehman_graph_hash(
                h.subgraph(c),
                node_attr='specie')

            for c in connected_components
            ]

        mol.fragment_hashes.append(fragment_hashes)

    return False



def metal_complex(mol):
    # if mol is a metal, it isn't a metal complex
    if mol.formula in m_formulas:
        return False

    return not nx.is_connected(mol.covalent_graph)


def carbon_metal_bond(mol):
    # TODO: make this more general for metals
    for bond in mol.bonds:
        if set([mol.species[i] for i in bond]) == set(['Li', 'C']):
            return True

    return False

def bad_hydrogen_bonding(mol):

    for i in range(mol.num_atoms):


        if mol.species[i] == 'H':

            num_bonds = 0
            for bond in mol.bonds:
                if i in bond:
                    num_bonds += 1

            if num_bonds > 1:
                return True

            else:
                return False

    return False

def bad_lithium_coordination(mol):

    if mol.formula != 'Li1':

        if 'Li' in mol.species and mol.number_of_coordination_bonds == 0:
            return True

    return False

def bad_lithium_partial_charge(mol):
    for i in range(mol.num_atoms):
        if (mol.species[i] == "Li" and
            mol.partial_charges[i] < 0.0):
            return True

    return False


def default_true(mol):
    return True


standard_species_decision_tree = [
    (mol_not_connected, Terminal.DISCARD),
    (metal_ion_filter, Terminal.DISCARD),
    (metal_complex, Terminal.DISCARD),
#    (carbon_metal_bond, Terminal.DISCARD),
#    (bad_hydrogen_bonding, Terminal.DISCARD),
    (bad_lithium_coordination, Terminal.DISCARD),
#    (bad_lithium_partial_charge, Terminal.DISCARD),
    (add_star_hashes, Terminal.KEEP),
    (add_fragment_hashes, Terminal.KEEP),
    (default_true, Terminal.KEEP)
    ]
