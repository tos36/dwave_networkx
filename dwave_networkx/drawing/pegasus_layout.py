"""
Tools to visualize Pegasus lattices and weighted graph problems on them.
"""

from __future__ import division

import networkx as nx
from networkx import draw

from dwave_networkx import _PY2
from dwave_networkx.drawing.qubit_layout import draw_qubit_graph, draw_embedding
from dwave_networkx.generators.pegasus import pegasus_coordinates

# compatibility for python 2/3
if _PY2:
    range = xrange

    def itervalues(d): return d.itervalues()

    def iteritems(d): return d.iteritems()
else:
    def itervalues(d): return d.values()

    def iteritems(d): return d.items()

__all__ = ['pegasus_layout', 'draw_pegasus', 'draw_pegasus_embedding']


def pegasus_layout(G, scale=1., center=None, dim=2):
    """Positions the nodes of graph G in a Pegasus topology.

    NumPy (http://scipy.org) is required for this function.

    Parameters
    ----------
    G : NetworkX graph
        Should be a Pegasus graph or a subgraph of a Pegasus graph.
        This should be the product of dwave_networkx.pegasus_graph

    scale : float (default 1.)
        Scale factor. When scale = 1,  all positions fit within [0, 1]
        on the x-axis and [-1, 0] on the y-axis.

    center : None or array (default None)
        Coordinates of the top left corner.

    dim : int (default 2)
        Number of dimensions. When dim > 2, all extra dimensions are
        set to 0.

    Returns
    -------
    pos : dict
        A dictionary of positions keyed by node.

    Examples
    --------
    >>> G = dnx.pegasus_graph(1)
    >>> pos = dnx.pegasus_layout(G)

    """

    if not isinstance(G, nx.Graph) or G.graph.get("family") != "pegasus":
        raise ValueError("G must be generated by dwave_networkx.pegasus_graph")

    xy_coords = pegasus_node_placer_2d(G, scale, center, dim)

    if G.graph.get('labels') == 'coordinate':
        pos = {v: xy_coords(*v) for v in G.nodes()}
    elif G.graph.get('data'):
        pos = {v: xy_coords(*dat['pegasus_index']) for v, dat in G.nodes(data=True)}
    else:
        m = G.graph.get('rows')
        coord = pegasus_coordinates(m)
        pos = {v: xy_coords(*coord.tuple(v)) for v in G.nodes()}

    return pos


def pegasus_node_placer_2d(G, scale=1., center=None, dim=2):
    """Generates a function that converts Pegasus indices to x, y
    coordinates for a plot.

    Parameters
    ----------
    G : NetworkX graph
        Should be a Pegasus graph or a subgraph of a Pegasus graph.
        This should be the product of dwave_networkx.pegasus_graph

    scale : float (default 1.)
        Scale factor. When scale = 1,  all positions fit within [0, 1]
        on the x-axis and [-1, 0] on the y-axis.

    center : None or array (default None)
        Coordinates of the top left corner.

    dim : int (default 2)
        Number of dimensions. When dim > 2, all extra dimensions are
        set to 0.

    Returns
    -------
    xy_coords : function
        A function that maps a Pegasus index (u, w, k, z) in a
        Pegasus lattice to x,y coordinates such as used by a plot.

    """
    import numpy as np

    m = G.graph.get('rows')
    h_offsets = G.graph.get("horizontal_offsets")
    v_offsets = G.graph.get("vertical_offsets")
    tile_width = G.graph.get("tile")
    tile_center = tile_width / 2 - .5

    # want the enter plot to fill in [0, 1] when scale=1
    scale /= m * tile_width

    if center is None:
        center = np.zeros(dim)
    else:
        center = np.asarray(center)

    paddims = dim - 2
    if paddims < 0:
        raise ValueError("layout must have at least two dimensions")

    if len(center) != dim:
        raise ValueError("length of center coordinates must match dimension of layout")

    def _xy_coords(u, w, k, z):
        # orientation, major perpendicular offset, minor perpendicular offset, parallel offset

        if k % 2:
            p = -.1
        else:
            p = .1

        if u:
            xy = np.array([z*tile_width+h_offsets[k] + tile_center, -tile_width*w-k-p])
        else:
            xy = np.array([tile_width*w+k+p, -z*tile_width-v_offsets[k]-tile_center])

        # convention for Pegasus-lattice pictures is to invert the y-axis
        return np.hstack((xy * scale, np.zeros(paddims))) + center

    return _xy_coords


def draw_pegasus(G, **kwargs):
    """Draws graph G in a Pegasus topology.

    If `linear_biases` and/or `quadratic_biases` are provided, these
    are visualized on the plot.

    Parameters
    ----------
    G : NetworkX graph
        Should be a Pegasus graph or a subgraph of a Pegasus graph,
        a product of dwave_networkx.pegasus_graph.

    linear_biases : dict (optional, default {})
        A dict of biases associated with each node in G. Should be of
        form {node: bias, ...}. Each bias should be numeric.

    quadratic_biases : dict (optional, default {})
        A dict of biases associated with each edge in G. Should be of
        form {edge: bias, ...}. Each bias should be numeric. Self-loop
        edges (i.e., :math:`i=j`) are treated as linear biases.

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the `pos` parameter which is not used by this
       function. If `linear_biases` or `quadratic_biases` are provided,
       any provided `node_color` or `edge_color` arguments are ignored.

    Examples
    --------
    >>> # Plot a Pegasus graph with size parameter 2
    >>> import networkx as nx
    >>> import dwave_networkx as dnx
    >>> import matplotlib.pyplot as plt
    >>> G = dnx.pegasus_graph(2)
    >>> dnx.draw_pegasus(G)
    >>> plt.show()

    """

    draw_qubit_graph(G, pegasus_layout(G), **kwargs)


def draw_pegasus_embedding(G, *args, **kwargs):
    """Draws an embedding onto the pegasus graph G, according to layout.

    If interaction_edges is not None, then only display the couplers in that
    list.  If embedded_graph is not None, the only display the couplers between
    chains with intended couplings according to embedded_graph.

    Parameters
    ----------
    G : NetworkX graph
        Should be a Pegasus graph or a subgraph of a Pegasus graph.
        This should be the product of dwave_networkx.pegasus_graph

    emb : dict
        A dict of chains associated with each node in G.  Should be
        of the form {node: chain, ...}.  Chains should be iterables
        of qubit labels (qubits are nodes in G).

    embedded_graph : NetworkX graph (optional, default None)
        A graph which contains all keys of emb as nodes.  If specified,
        edges of G will be considered interactions if and only if they
        exist between two chains of emb if their keys are connected by
        an edge in embedded_graph

    interaction_edges : list (optional, default None)
        A list of edges which will be used as interactions.

    show_labels: boolean (optional, default False)
        If show_labels is True, then each chain in emb is labelled with its key.

    chain_color : dict (optional, default None)
        A dict of colors associated with each key in emb.  Should be
        of the form {node: rgba_color, ...}.  Colors should be length-4
        tuples of floats between 0 and 1 inclusive. If chain_color is None,
        each chain will be assigned a different color.

    unused_color : tuple (optional, default (0.9,0.9,0.9,1.0))
        The color to use for nodes and edges of G which are not involved
        in chains, and edges which are neither chain edges nor interactions.
        If unused_color is None, these nodes and edges will not be shown at all.

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the `pos` parameter which is not used by this
       function. If `linear_biases` or `quadratic_biases` are provided,
       any provided `node_color` or `edge_color` arguments are ignored.
    """
    draw_embedding(G, pegasus_layout(G), *args, **kwargs)
