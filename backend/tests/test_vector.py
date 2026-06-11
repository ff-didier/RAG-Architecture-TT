from app.retrieval.vector import _vector_literal


def test_vector_literal_format():
    assert _vector_literal([1.0, 2.5, 3.0]) == "[1.0,2.5,3.0]"
