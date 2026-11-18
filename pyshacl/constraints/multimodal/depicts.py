from decimal import Decimal
from math import isfinite

from rdflib import Literal, URIRef
from rdflib.namespace import XSD

from pyshacl.consts import (
    MM_DepictsConstraintComponent,
    MM_depicts,
    MM_score,
    MM_threshold,
)
from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.errors import ConstraintLoadError


def score_image(image_iri: str, expected_description: str) -> float:
    """Temporary stub: does not retrieve or inspect images."""
    return 0.0


class DepictsConstraintComponent(ConstraintComponent):
    shacl_constraint_component = MM_DepictsConstraintComponent

    def __init__(self, shape):
        super().__init__(shape)

        # Only property shapes are supported initially.
        if not self.shape.is_property_shape:
            raise ConstraintLoadError(
                "mm:depicts requires a property shape.",
                str(MM_depicts),
            )

        # Read and validate the expected description.
        descriptions = list(self.shape.objects(MM_depicts))

        if (
            len(descriptions) != 1
            or not isinstance(descriptions[0], Literal)
            or descriptions[0].datatype not in (None, XSD.string)
        ):
            raise ConstraintLoadError(
                "mm:depicts requires exactly one plain or xsd:string literal.",
                str(MM_depicts),
            )

        self.description = str(descriptions[0])

        # Read and validate the threshold.
        thresholds = list(self.shape.objects(MM_threshold))

        if len(thresholds) != 1 or not isinstance(thresholds[0], Literal):
            raise ConstraintLoadError(
                "mm:threshold requires exactly one numeric literal.",
                str(MM_threshold),
            )

        threshold = thresholds[0].value

        # bool must be rejected explicitly because it subclasses int.
        if isinstance(threshold, bool) or not isinstance(
            threshold, (int, float, Decimal)
        ):
            raise ConstraintLoadError(
                "mm:threshold must be a number.",
                str(MM_threshold),
            )

        try:
            self.threshold = float(threshold)
        except (TypeError, ValueError, OverflowError):
            raise ConstraintLoadError(
                "mm:threshold cannot be converted to a valid float.",
                str(MM_threshold),
            ) from None

        # Our scorer's contract uses cosine similarity.
        if not isfinite(self.threshold) or not -1 <= self.threshold <= 1:
            raise ConstraintLoadError(
                "mm:threshold must be finite and between -1 and 1.",
                str(MM_threshold),
            )

    @classmethod
    def constraint_parameters(cls):
        return [MM_depicts]

    @classmethod
    def constraint_name(cls):
        return "DepictsConstraintComponent"

    def evaluate(self, executor, target_graph, focus_value_nodes, _evaluation_path):
        reports = []

        for focus_node, value_nodes in focus_value_nodes.items():
            for value_node in value_nodes:
                # sh:nodeKind reports values that are not IRIs.
                if not isinstance(value_node, URIRef):
                    continue

                score = score_image(str(value_node), self.description)

                if score >= self.threshold:
                    continue

                message = Literal(
                    f"Placeholder score {score} is below threshold {self.threshold} "
                    f"for '{self.description}'."
                )
                description, result_node, result_triples = self.make_v_result(
                    target_graph,
                    focus_node,
                    value_node=value_node,
                    extra_messages=[message],
                )
                result_triples.append((result_node, MM_score, Literal(score)))
                result_triples.append((result_node, MM_threshold, Literal(self.threshold)))
                reports.append((description, result_node, result_triples))

        return len(reports) == 0, reports
