"""Context cues: the word before and the word after a lone homograph decide
it (issue 407). Each expected value is the meaning of the sentence, worked
out by hand; the sources of each cue are in numtag/lexicon/<lang>.json."""
import json

import pytest

from helpers import sure
from numtag.lexicon import _check

C = "cardinal"


@pytest.mark.parametrize("text, lang, expected", [
    # "segundo"/"secondo" before an article or a determiner is "according to" (#311)
    ("Segundo o último relatório, a cooperativa vendeu.", "pt-PT", []),
    ("Segundo a polícia, ninguém ficou ferido.", "pt-PT", []),
    ("Segundo este estudo, o consumo caiu.", "pt-BR", []),
    ("Secondo il rapporto, la cooperativa ha venduto.", "it", []),
    ("Secondo questa ricerca, i prezzi salgono.", "it", []),
    # the plural time unit after a cardinal: 66 seconds, no ordinal 2 (#313)
    ("Esperou sessenta e seis segundos.", "pt-PT", [("sessenta e seis", "66", 1.0)]),
    ("A cozinha ficou pronta em 30 segundos.", "pt-BR", [("30", "30", 1.0)]),
    ("Esperó sesenta segundos.", "es", [("sesenta", "60", 1.0)]),
    ("Ha aspettato sessanta secondi.", "it", [("sessanta", "60", 1.0)]),
    ("Va esperar seixanta segons.", "ca", [("seixanta", "60", 1.0)]),
    ("Agardou sesenta segundos.", "gl", [("sesenta", "60", 1.0)]),
])
def test_a_cue_decides_the_lone_word(text, lang, expected):
    assert sure(text, lang) == expected


@pytest.mark.parametrize("text, lang, expected", [
    # no cue decides "segundo lugar": the word stays a homograph
    ("Chegou em segundo lugar.", "pt-PT", [("segundo", "2", 0.4)]),
    # after its determiner the ordinal stays, also before the article "a"
    ("Foi o segundo a chegar.", "pt-PT", [("segundo", "2", 0.4)]),
    ("Leu o segundo relatório.", "pt-PT", [("segundo", "2", 0.4)]),
    # a cue has no effect inside a longer number: 20 + 2 = 22
    ("Chegou no vigésimo segundo lugar.", "pt-PT", [("vigésimo segundo", "22", 1.0)]),
    # the article with no restrictive adverb before it stays weak
    ("Comprei um livro.", "pt-PT", [("um", "1", 0.3)]),
    ("Compré un libro.", "es", [("un", "1", 0.3)]),
    # a restrictive adverb before an article in a predicate does not make
    # it a count: "only an example", "only a child"
    ("É só um exemplo.", "pt-PT", [("um", "1", 0.3)]),
    ("Ela é apenas uma criança.", "pt-PT", [("uma", "1", 0.3)]),
    ("Es solo un ejemplo.", "es", [("un", "1", 0.3)]),
    # the singular after the article: unit or ordinal, no cue decides
    ("Espera um segundo.", "pt-PT", [("um", "1", 0.3), ("segundo", "2", 0.4)]),
])
def test_no_cue_keeps_the_old_reading(text, lang, expected):
    assert sure(text, lang) == expected


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="https://github.com/TigreGotico/numtag/issues/312: a restrictive adverb before the "
                          "article makes a count only in some clauses, and no cue tells them apart")
@pytest.mark.parametrize("text, lang, expected", [
    ("Apareceu apenas um aluno.", "pt-PT", [("um", "1", 1.0)]),
    ("Só falta um dia.", "pt-BR", [("um", "1", 1.0)]),
    ("Solo queda un día.", "es", [("un", "1", 1.0)]),
])
def test_a_restrictive_adverb_before_the_article_counts(text, lang, expected):
    assert sure(text, lang) == expected


def _file(**entry) -> dict:
    return {"format_version": 6, "extends": "pt-PT",
            "entries": [{"word": "x", "role": "unit", "value": "1", "source": "s", **entry}]}


@pytest.mark.parametrize("cue", [
    {"prev": ["a"], "then": "word"},  # no source
    {"prev": ["a"], "then": "maybe", "source": "s"},  # unknown verdict
    {"then": "word", "source": "s"},  # no side
    {"prev": ["a"], "then": "word", "source": "s", "after": ["b"]},  # unknown key
])
def test_the_loader_refuses_a_bad_cue(cue):
    with pytest.raises(ValueError):
        _check("x", _file(context=[cue]))


def test_the_context_key_needs_format_version_6():
    data = _file(context=[{"prev": ["a"], "then": "word", "source": "s"}])
    data["format_version"] = 5
    with pytest.raises(ValueError, match="needs format_version 6"):
        _check("x", data)
    data = json.loads(json.dumps(data))
    data["format_version"] = 5
    data["entries"][0].pop("context")
    data["words"] = {"cue_x": {"value": ["a"], "source": "s"}}
    with pytest.raises(ValueError, match="needs format_version 6"):
        _check("x", data)
