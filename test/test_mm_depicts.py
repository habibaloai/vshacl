from rdflib import Graph, Namespace
from pyshacl import validate
from pyshacl.consts import MM, SH

EX = Namespace("https://example.org/")


def test_depicts_stub_reports_one_image():
    data = Graph().parse(
        data="""
        @prefix ex: <https://example.org/> .

        ex:A a ex:Bridge ;
            ex:image <https://example.org/banana.jpg> .
        """,
        format="turtle",
    )

    shapes = Graph().parse(
        data="""
        @prefix ex: <https://example.org/> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix mm: <https://example.org/vshacl#> .

        ex:BridgeShape a sh:NodeShape ;
            sh:targetClass ex:Bridge ;
            sh:property ex:BridgeImageShape .

        ex:BridgeImageShape a sh:PropertyShape ;
            sh:path ex:image ;
            sh:minCount 1 ;
            sh:nodeKind sh:IRI ;
            mm:depicts "a photo of a bridge" .
        """,
        format="turtle",
    )

    conforms, report, report_text = validate(
        data_graph=data,
        shacl_graph=shapes,
    )

    assert conforms is False

    results = list(
        report.subjects(
            SH.sourceConstraintComponent,
            MM.DepictsConstraintComponent,
        )
    )
    assert len(results) == 1

    result = results[0]
    assert report.value(result, SH.focusNode) == EX.A
    assert report.value(result, SH.value) == EX["banana.jpg"]
    assert report.value(result, SH.resultPath) == EX.image
    assert report.value(result, SH.sourceShape) == EX.BridgeImageShape
    assert report.value(result, SH.resultSeverity) == SH.Violation
    assert report.value(result, SH.resultMessage) is not None