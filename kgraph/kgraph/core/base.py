# import re
import copy
import re
from typing import Literal


class KB:

    def __init__(self, relations: list[dict[str, str]] = None):
        if relations is None:
            self.relations: list[dict[Literal["head", "type", "tail"], str]] = []
        else:
            self.relations = relations

        # instance variables
        self.nodes = {node: {"wiki_title": None} for node in self.get_nodes()}

    def __repr__(self) -> str:
        """
        Representation of KB for lists or debugging.
        """
        str_list = [str(r) for r in self.relations]
        return "kgraph.KB([{}])".format(",\n".join(str_list))

    def are_relations_equal(self, r1, r2):
        return all(r1[attr] == r2[attr] for attr in ["head", "type", "tail"])

    def exists_relation(self, r1):
        return any(self.are_relations_equal(r1, r2) for r2 in self.relations)

    def add_relation(self, r: dict[str, str]):
        """
        Add a single triplet relation `r` to KB.

        Parameters
        ----------
        r: dict[str, str]
            Triplet relation for adding.

        Notes
        -----
        If `r` already exists in KB, this method only update `meta` information of existing triplet.
        """
        if not self.exists_relation(r):
            self.relations.append(r)

    def add_node_attr(self, node_label: str, attr: str, value: str):
        """
        Add attribute `attr` to node `node_label` with value `value`.

        Parameters
        ----------
        node_label: str
            Label of node to add attribute.
        attr: str
            Name of attribute.
        value: str
            Value of attribute.
        """
        if node_label not in self.nodes.keys():
            raise ValueError(f"Node {node_label} does not exist in KB.")
        self.nodes[node_label][attr] = value

    def add_edge_attr(self, hd: str, r: str, tl: str, attr: str, value: str):
        """
        Add attribute `attr` to edge (hd, r, tl) with value `value`.

        Parameters
        ----------
        hd: str
            Head node label.
        r: str
            Relation type.
        tl: str
            Tail node label.
        attr: str
            Name of attribute.
        value: str
            Value of attribute.
        """
        for relation in self.relations:
            if relation["head"] == hd and relation["type"] == r and relation["tail"] == tl:
                relation[attr] = value
                return
        raise ValueError(f"Relation ({hd}, {r}, {tl}) does not exist in KB.")

    def get_nodes(self) -> list[str]:
        """
        Return a list of node labels.

        Returns
        -------
        node_list: list[str]
            List of node labels.

        Notes
        -----
        Even if a node appears in multiple relations, its label appears only once in output list.
        """
        head_list = list(set([relation["head"] for relation in self.relations]))
        tail_list = list(set([relation["tail"] for relation in self.relations]))
        node_list = head_list + [tail for tail in tail_list if tail not in head_list]

        return node_list

    def get_relations_from(self, node_label: str) -> list[dict[str, str]]:
        """Return all relations whose HEAD is `node_label`"""
        return [r for r in self.relations if r["head"] == node_label]

    def get_relations_to(self, node_label: str) -> list[dict[str, str]]:
        """Return all relations whose TAIL is `node_label`"""
        return [r for r in self.relations if r["tail"] == node_label]

    def get_relations_between(self, hd: str, tl: str) -> list[dict[str, str]]:
        """
        Acquire realtions which has `hd` as head and `tl` as tail.

        Parameters
        ----------
        hd: str
            Node label of head.
        tl: str
            Node label of tail.

        Returns
        -------
        list[dict[str,str]]
            Relations between `hd` and `tl`.
        """
        return [r for r in self.relations if (r["head"] == hd and r["tail"] == tl)]

    def select_where(self, nodes: list[str], strict=False):
        """
        Extract a subgraph of KB whose node labels are in `nodes`.

        Parameters
        ----------
        nodes: list[dict[str, str]]
            List of nodes to remain.
        strict: bool
            If `strict` were true, this method returns relationship whose "head" and "tail" are
            BOTH included in `nodes`.

        Notes
        -----
        This method DELTES the remaining part of `KB` whose node labels are not in `nodes`.
        """
        if strict:
            self.relations = [r for r in self.relations if (r["head"] in nodes and r["tail"] in nodes)]
        else:
            self.relations = [r for r in self.relations if (r["head"] in nodes or r["tail"] in nodes)]

    def get_degree(self, direction: Literal["both", "in", "out"] = "both") -> dict[str, int]:
        """
        Method to get degrees of all nodes in KB.
        In order to limit edge direction, set `direction` as `in` or `out`.

        Parameters
        ----------
        direction: Literal["both","in","out"]
            Option for edge direction. ("both" | "in" | "out")

        Returns
        -------
        degrees: dict[str, int]
            Dictionary of node degrees in KB.
            Nodes are reversely sorted by their degrees.
        """
        degrees = dict()
        nodes = self.get_nodes()

        for n in nodes:
            match direction:
                case "both":
                    degrees[n] = len(self.get_relations_from(n) + self.get_relations_to(n))
                case "in":
                    degrees[n] = len(self.get_relations_to(n))
                case "out":
                    degrees[n] = len(self.get_relations_from(n))
                case _:
                    raise ValueError('direction should be specified from "both", "in" or "out".')

        # sort results by degree
        degrees = {n: d for n, d in sorted(degrees.items(), key=lambda item: item[1], reverse=True)}
        return degrees

    def get_max_degree(self) -> int:
        """Get max degree of KB"""
        return max(self.get_degree().values())

    def apply_entity_linking(self, mapping: dict[str, str]):
        """
        Apply entity linking to the KB.

        Parameters
        ----------
        mapping: dict[str, str]
            Mapping of node labels to their linked entities.
        """
        rels = [
            (
                {"head": mapping[r["head"]], "type": r["type"], "tail": mapping[r["tail"]]}
                if r["head"] in mapping and r["tail"] in mapping
                else (
                    {"head": mapping[r["head"]], "type": r["type"], "tail": r["tail"]}
                    if r["head"] in mapping
                    else (
                        {"head": r["head"], "type": r["type"], "tail": mapping[r["tail"]]}
                        if r["tail"] in mapping
                        else r
                    )
                )
            )
            for r in self.relations
        ]
        unique_rels = [dict(t) for t in set(tuple(r.items()) for r in rels)]  # remove duplicates
        self.relations = unique_rels

    def copy(self) -> "KB":
        """
        Create a deep copy of the KB instance.

        Returns
        -------
        KB
            A new KB instance with the same data as the original.
        """
        new_kb = KB(relations=copy.deepcopy(self.relations))
        new_kb.nodes = copy.deepcopy(self.nodes)
        return new_kb

    @classmethod
    def from_dot_file(cls, dot_file_path: str) -> "KB":
        """
        Construct a KB object from a DOT file.

        Parameters
        ----------
        dot_file_path: str
            Path to the DOT file.

        Returns
        -------
        KB
            An instance of the KB class.
        """
        relations = []
        node_atts = dict()

        with open(dot_file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            # Match node lines: "node_label" [wiki_title="title"];
            node_match = re.match(
                r'\s*"([^"]+)"(?:\s*\[\s*(?:wiki_title="([^"]+)")?(?:,\s*)?(?:color="([^"]+)")?\s*\])?;', line
            )
            if node_match:
                # NOTE: `wiki_title` is None if not found.
                node_label, wiki_title, color = node_match.groups()
                node_atts[node_label] = (
                    {"wiki_title": wiki_title, "color": color} if color else {"wiki_title": wiki_title}
                )
                continue

            # Match edge lines: "head" -> "tail" [label="type", verified=true, color="..."];
            edge_match = re.match(
                r'\s*"(.+)" -> "(.+)" \[label="([^"]+)"(?:, color="([^"]+)")?(?:, verified=(true|false))?.*];', line
            )
            if edge_match:
                head, tail, relation_type, color, verified = edge_match.groups()
                relation = {"head": head, "type": relation_type, "tail": tail}
                if color:
                    relation["color"] = color
                if verified:
                    relation["verified"] = True if verified == "true" else False
                relations.append(relation)

        # Create KB instance
        kb = cls(relations)
        for node_label, attributes in node_atts.items():
            kb.nodes[node_label] = attributes

        return kb

    def write_dot(self, output_file: str):
        """
        Save KB as DOT file without using pydot.
        If each node has the `wiki_title` attribute, it will be included in the output.
        For nodes without a `wiki_title`, the attribute will not be given.

        Parameters
        ----------
        output_file: str
            Path of output dot file.
        """
        # Start building the DOT content
        dot_content = ["digraph RDFGraph {"]

        # Add nodes
        dot_content.append("\t// Nodes")
        for node_label, attributes in self.nodes.items():
            # TODO: This IF statement should be removed.
            assert node_label != "", "Node label should not be empty. Current knowledge graph: {}".format(self)
            # node label
            node_line = f'\t"{node_label}"'
            # node attributes
            wiki_title = attributes.get("wiki_title", "")
            color = attributes.get("color", "")
            if wiki_title and color:
                node_line += f' [wiki_title="{wiki_title}", color="{color}"]'
            elif wiki_title:
                node_line += f' [wiki_title="{wiki_title}"]'
            elif color:
                node_line += f' [color="{color}"]'
            node_line += ";"
            dot_content.append(node_line)

        # Add edges
        dot_content.append("\n\t// Edges")
        for r in self.relations:
            label = r["type"]
            ver_info = ', color="orange", verified=true' if "verified" in r and r["verified"] else ""
            edge_line = f'\t"{r["head"]}" -> "{r["tail"]}" [label="{label}"{ver_info}];'
            dot_content.append(edge_line)

        # Close the DOT content
        dot_content.append("}")

        # Write to the output file
        with open(output_file, "w") as f:
            f.write("\n".join(dot_content))


if __name__ == "__main__":
    import os

    # Constructor and print
    print("Constructor and printing")
    kb = KB(
        [
            {"head": "Napoleon Bonaparte", "type": "date of birth", "tail": "15 'August 1769"},
            {"head": "Napoleon Bonaparte", "type": "date of death", "tail": "5 May 1821"},
            {"head": "Napoleon Bonaparte", "type": "participant in", "tail": "French Revolution"},
            {"head": "Napoleon Bonaparte", "type": "conflict", "tail": "Revolutionary Wars"},
            {"head": "Revolutionary Wars", "type": "part of", "tail": "French Revolution"},
            {"head": "French Revolution", "type": "participant", "tail": "Napoleon Bonaparte"},
            {"head": "Revolutionary Wars", "type": "participant", "tail": "Napoleon Bonaparte"},
        ]
    )
    print("Relations:\n{}".format(kb))
    print("Nodes:\n{}".format(kb.get_nodes()))

    kb.add_node_attr("Napoleon Bonaparte", "wiki_title", "Napoleon_Bonaparte")
    kb.add_node_attr("Napoleon Bonaparte", "color", "orange")
    kb.add_node_attr("French Revolution", "wiki_title", "French_Revolution")
    kb.add_node_attr("Revolutionary Wars", "color", "orange")

    print("Before:\n{}".format(kb))
    kb.write_dot("output.dot")
    kb = KB.from_dot_file("output.dot")
    print("After:\n{}".format(kb))
    print(kb.nodes)
    os.remove("output.dot")

    # Relations between
    print("\nRelation search")
    hd = "Napoleon Bonaparte"
    tl = "15 'August 1769"
    print("Relations from '{}': {}".format(hd, kb.get_relations_from(hd)))
    print("Relations to '{}': {}".format(tl, kb.get_relations_to(tl)))
    print("Relations between: {}".format(kb.get_relations_between("Napoleon Bonaparte", "15 'August 1769")))
    # print(kb.get_relations_between('15 'August 1769', 'Napoleon Bonaparte'))

    # Extract subgraph with node limitation
    nodes = ["French Revolution", "5 May 1821"]
    kb.select_where(nodes)
    print("\nSubgraph with nodes: {}\n{}".format(nodes, kb))
