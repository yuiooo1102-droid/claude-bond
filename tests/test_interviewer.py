from unittest.mock import patch

from claude_bond.extractor.interviewer import identify_gaps, build_bond_from_classified


def test_identify_gaps_finds_empty_dimensions():
    classified = {
        "identity": ["data scientist"],
        "rules": ["no emoji"],
        "style": [],
        "memory": ["works on NLP"],
    }
    gaps = identify_gaps(classified)
    assert "style" in gaps
    assert "identity" not in gaps


def test_identify_gaps_no_gaps():
    classified = {
        "identity": ["dev"],
        "rules": ["be concise"],
        "style": ["Chinese", "short replies"],
        "memory": ["project X"],
    }
    gaps = identify_gaps(classified)
    assert gaps == {}


def test_build_bond_from_classified():
    classified = {
        "identity": ["data scientist", "Python expert"],
        "rules": ["no emoji", "no summaries"],
        "style": ["Chinese", "concise"],
        "memory": ["working on claude-bond"],
    }
    dimensions = build_bond_from_classified(classified)
    assert len(dimensions) == 4
    names = {d.name for d in dimensions}
    assert names == {"identity", "rules", "style", "memory"}
    identity = next(d for d in dimensions if d.name == "identity")
    assert "data scientist" in identity.content
