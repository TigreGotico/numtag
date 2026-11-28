"""Marwari grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/mwr.json."""
import pytest

from helpers import read

C = "cardinal"


@pytest.mark.parametrize("text, expected", [
    # अरब (Arabia) with no count before it is a word
    ("म्हैं अरब देस गयो हो।", []),
    ("अरब रा घोड़ा घणा चोखा व्है।", []),
    ("अरब सागर घणौ मोटौ है।", []),
    # a count before अरब: 2 × 10^9, 1 × 10^9, 5 × 10^9
    ("सरकार दो अरब रुपिया खरच किया।", [("दो अरब", "2000000000", C)]),
    ("एक अरब लोग", [("एक अरब", "1000000000", C)]),
    ("5 अरब रुपिया", [("5 अरब", "5000000000", C)]),
])
def test_mwr_arab_is_a_number_only_after_a_count(text, expected):
    assert read(text, "mwr") == expected


@pytest.mark.parametrize("text, expected", [
    # बारै (outside) after रै or सूं, or before a singular verb of going out
    ("वो बारै गयो।", []),
    ("छोरो घर रै बारै बैठो है।", []),
    ("गांव सूं बारै एक कुवो है।", [("एक", "1", C)]),
    ("डोकरी बारै गई।", []),
    # बारै (12) as a count
    ("बारै बजे रोटी खावां।", [("बारै", "12", C)]),
    ("बारै मास मेह बरसै।", [("बारै", "12", C)]),
    ("म्हारै कनै बारै रुपिया है।", [("बारै", "12", C)]),
    # 100 + 12
    ("एक सौ बारै गायां", [("एक सौ बारै", "112", C)]),
])
def test_mwr_barai_outside_is_a_word(text, expected):
    assert read(text, "mwr") == expected
