from math import log
from csc_utils.ordered_set import OrderedSet
import networkx as nx
log_2 = log(2)

def set_conceptnet_weights(graph):
    """
    Given a ConceptNet-style graph representation, with a 'score' and 'freq'
    on each node, combine these into a single 'weight' value that grows
    linearly with the frequency and logarithmically with the score.
    """
    def conceptnet_weight(score, freq):
        return (freq/10.0) * log(max((score+1, 1)))/log_2
    
    def set_weight(edgedata):
        score = edgedata['score']
        freq = edgedata['freq']
        edgedata['weight'] = conceptnet_weight(score, freq)

    data_foreach(graph, set_weight)

def data_foreach(graph, func):
    """
    Applies a function that mutates the data dictionary of each edge in
    a graph. The return value of the function is not used.
    """
    for source, dest, data in graph.edges_iter(data=True):
        if data and data['score'] > 0:
            func(data)

def _extract_nodes(source, target, data):
    return (source, target)

def _extract_features(source, target, data):
    return (('left', data['rel'], source), ('right', data['rel'], target))

def _extract_pairs(source, target, data):
    return ((source, target), (target, source))

def _extract_relations(source, target, data):
    return (data['rel'], data['rel'])

def _extract_source_only(source, target, data):
    return (source, source)

def _extract_target_only(source, target, data):
    return (target, target)

def prune(graph, cutoff=1):
    '''
    Only keep nodes with a connectivity >= cutoff.
    '''
    # The to_undirected function is tempting, but it copies all the
    # data, which is unnecessary for this algorithm.
    ugraph = nx.Graph()
    ugraph.add_nodes_from(graph)
    ugraph.add_edges_from(graph.edges_iter())
    cores = nx.find_cores(ugraph)
    core_nodes = [n for n in graph.nodes() if cores[n] >= cutoff]
    return graph.subgraph(core_nodes)

def relation_filter(relation):
    if isinstance(relation, basestring): relation = [relation]
    def filter(source, target, data):
        return data['rel'] in relation
    return filter

LABELERS = {
    'nodes': _extract_nodes,
    'concepts': _extract_nodes,       # synonym for 'nodes'
    'features': _extract_features,
    'pairs': _extract_pairs,
    'relations': _extract_relations,
    'source_only': _extract_source_only,
    'target_only': _extract_target_only,
}

def sparse_triples(graph, row_labeler, col_labeler, cutoff=1, filter=None):
    """
    A generator of sparse triples to put into a matrix, given a NetworkX graph.
    It is assumed that each edge of the graph yields two entries of the matrix.
    
    `row_labeler` and `col_labeler` are functions that are given each edge
    as a tuple of (source, target, data), and choose two rows and columns for
    the matrix. The first row is paired with the second column and vice versa.

    In practice, you don't need to worry abaout that, because `row_labeler`
    and `col_labeler` can also be strings choosing a predefined function.
    To get an adjacency matrix that relates nodes to nodes, for example, use::

        divisi2.network.sparse_triples(graph, 'nodes', 'nodes')

    To get an AnalogySpace concept-by-feature matrix:

        divisi2.network.sparse_triples(graph, 'nodes', 'features')

    To get a pair-relation matrix, as in Latent Relational Analysis:

        divisi2.network.sparse_triples(graph, 'pairs', 'relations')
    
    `cutoff` specifies the minimum degree of nodes to include.
    
    The edge weights should be expressed in one of two forms:

    - The standard way for NetworkX, as the entry named 'weight' in the edge
      data dictionaries.
    - As ConceptNet-style 'score' and 'freq' values in the edge data
      dictionaries, which will be transformed into appropriate weights.

    If no edge weights can be found, the edges will be given a default weight
    of 1.
    """
    first_edge = graph.edges_iter(data=True).next()
    first_data = first_edge[2]
    if 'score' in first_data and 'weight' not in first_data:
        set_conceptnet_weights(graph)

    try:
        if isinstance(row_labeler, basestring):
            row_labeler = LABELERS[row_labeler]
        if isinstance(col_labeler, basestring):
            col_labeler = LABELERS[col_labeler]
    except KeyError:
        raise KeyError("Unknown row or column type. The valid types are: %s"
          % sorted(LABELERS.keys()))
    
    row_labels = OrderedSet()
    if row_labeler == col_labeler:
        col_labels = row_labels
    else:
        col_labels = OrderedSet()
    
    subgraph = prune(graph, cutoff=cutoff)
    values = []
    rows = []
    cols = []
    for edge in subgraph.edges_iter(data=True):
        if filter is not None and not filter(*edge): continue
        rownames = row_labeler(*edge)
        colnames = col_labeler(*edge)
        weight = edge[2].get('weight', 1)
        row0 = row_labels.add(rownames[0])
        row1 = row_labels.add(rownames[1])
        col0 = col_labels.add(colnames[0])
        col1 = col_labels.add(colnames[1])
        values.append(weight)
        rows.append(row0)
        cols.append(col1)
        values.append(weight)
        rows.append(row1)
        cols.append(col0)
    return values, rows, cols, row_labels, col_labels

def sparse_matrix(graph, row_labeler, col_labeler, cutoff=1):
    from scipy.sparse import coo_matrix
    """
    Constructs a :class:`SparseMatrix` from a graph. See the documentation
    for :func:`sparse_triples` for how to choose the `row_labeler` and
    `col_labeler` to build different kinds of matrices.
    """
    values, rows, cols, row_labels, col_labels = sparse_triples(
        graph, row_labeler, col_labeler, cutoff
    )
    return coo_matrix((values, (rows, cols))), row_labels, col_labels

def sparse_assoc_matrix(graph, cutoff=1):
    mat, labels, _ = sparse_matrix(graph, 'concepts', 'concepts', cutoff)
    return mat, labels
