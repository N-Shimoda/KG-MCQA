from typing import Literal


class KB:

    def __init__(self, relations=None):
        if relations is None:
            self.relations: list[dict[Literal["head", "type", "tail"], str]] = []
        else:
            self.relations = relations

    def __str__(self) -> str:
        str_list = [str(r) for r in self.relations]
        return ",\n".join(str_list)

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
            self.relations = [
                r for r in self.relations if (r["head"] in nodes and r["tail"] in nodes)
            ]
        else:
            self.relations = [
                r for r in self.relations if (r["head"] in nodes or r["tail"] in nodes)
            ]

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
        degrees = {
            n: d for n, d in sorted(degrees.items(), key=lambda item: item[1], reverse=True)
        }
        return degrees

    def get_max_degree(self) -> int:
        """Get max degree of KB"""
        return max(self.get_degree().values())

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
        result: list[dict[str,str]]
            Relations between `hd` and `tl`.
        """
        return [r for r in self.relations if (r["head"] == hd and r["tail"] == tl)]

    def write_dot(self, output_file: str):
        """
        Save KB as DOT file in the current directory with name.

        Parameters
        ----------
        output_file: str
            Path of output dot file.
        """
        dot_content = "digraph RDFGraph {\n"

        for r in self.relations:
            dot_content += f'\t"{r["head"]}" -> "{r["tail"]}" [label="{r["type"]}"];\n'

        dot_content += "}\n"

        with open(output_file, "w") as dot_file:
            dot_file.write(dot_content)


if __name__ == "__main__":

    from kgraph.utils import colorize

    color_code = 32  # green

    # Constructor and print
    print(colorize("Constructor and printing", color_code))
    kb = KB(
        [
            {"head": "Napoleon Bonaparte", "type": "date of birth", "tail": "15 August 1769"},
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

    # Relations between
    print(colorize("\nRelation search", color_code))
    hd = "Napoleon Bonaparte"
    tl = "15 August 1769"
    print("Relations from '{}': {}".format(hd, kb.get_relations_from(hd)))
    print("Relations to '{}': {}".format(tl, kb.get_relations_to(tl)))
    print(
        "Relations between: {}".format(
            kb.get_relations_between("Napoleon Bonaparte", "15 August 1769")
        )
    )
    # print(kb.get_relations_between('15 August 1769', 'Napoleon Bonaparte'))

    # Extract subgraph with node limitation
    nodes = ["French Revolution", "5 May 1821"]
    kb.select_where(nodes)
    print("\nSubgraph with nodes: {}\n{}".format(nodes, kb))
