import os

from pyvis.network import Network

from kgraph.kgraph import KB


def draw_graph(kb: KB, title: str, outdir=None) -> None:
    """
    This functiion takes RDF relations and creates an HTML file for graph visualization.

    Parameters
    ----------
    realations: list[dict]
    title: str
    outdir: str (optional)

    Return
    ------
    None. However, this function generates an HTML file during execution.
    """
    # setting
    nt = Network(directed=True, height="720px")
    nt.show_buttons(True)

    # add realtions to graph
    for link in kb.relations:
        head = link["head"]
        tail = link["tail"]
        label = link["type"]

        nt.add_node(head, size=10)
        nt.add_node(tail, size=10)
        nt.add_edge(head, tail, label=label)

    # save html
    if outdir:
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        path = os.path.join(outdir, f"{title}.html")
        nt.save_graph(path)
    else:
        nt.save_graph("{}.html".format(title))


def show_graph(kb: KB, filename="network.html"):
    """
    Function to visualize Knolege Graph in jupyter notebook.

    Parameters
    ----------
    kb: KB
        KB which stores knowledge graph.
    """
    # create network
    net = Network(directed=True, width="700px", height="700px", bgcolor="#eeeeee")

    # nodes
    color_entity = "#00FF00"
    for e in kb.get_nodes():
        net.add_node(e, shape="circle", color=color_entity)

    # edges
    for r in kb.relations:
        net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"])

    # save network
    net.repulsion(
        node_distance=200,
        central_gravity=0.2,
        spring_length=200,
        spring_strength=0.05,
        damping=0.09,
    )
    net.set_edge_smooth("dynamic")
    net.show(filename)


def colorize(text: str, color_code: int) -> str:
    """
    Function for printing coloured text to standard output.

    Parameters
    ----------
    text: str
        Output text.
    color_code: int
        See following link for color samples:
        https://www.python.ambitious-engineer.com/wp-content/uploads/2021/11/print_color_samples.png.

    Return
    ------
    str
        `text` with color information
    """
    return f"\033[{color_code}m{text}\033[0m"
