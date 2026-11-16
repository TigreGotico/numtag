"""The readings that numtag's consumers depend on, in tests/consumers/.

Each reader does what the consumer does with the mentions. The comment
names the consumer code it follows.
"""
import json
import unittest
from fractions import Fraction
from pathlib import Path

from numtag import Form, Kind, Reason, Scale, tag_numbers

CONSUMERS = Path(__file__).parent / "consumers"


def _kept(text: str, lang: str, scale: Scale | None = None) -> list:
    return [m for m in tag_numbers(text, lang, scale=scale) if Reason.ARTICLE not in m.reasons]


def count(text: str, lang: str) -> str | None:
    # ovos-skill-count ovos_skill_count/__init__.py _read_number: the last number
    mentions = _kept(text, lang)
    return mentions[-1].value if mentions else None


def volume(text: str, lang: str) -> str | None:
    # ovos-skill-volume __init__.py _extract_amount: the first number
    mentions = _kept(text, lang)
    return mentions[0].value if mentions else None


def number_facts(text: str, lang: str) -> str | None:
    # ovos-skill-number-facts __init__.py extract_number: the most confident number, as an int
    mentions = _kept(text, lang)
    return str(int(Fraction(max(mentions, key=lambda m: m.confidence).value))) if mentions else None


def days_in_history(text: str, lang: str) -> list[str]:
    # ovos-skill-days-in-history __init__.py _get_year: every number; the skill joins two into a year
    return [m.value for m in _kept(text, lang)]


def mark1(text: str, lang: str) -> str | None:
    # ovos-skill-mark1-ctrl __init__.py parse_brightness: the first cardinal or decimal of the slot
    mentions = [m for m in _kept(text, lang) if m.kind in (Kind.CARDINAL, Kind.DECIMAL)]
    return mentions[0].value if mentions else None


def _json_number(value: str) -> int | float:
    number = Fraction(value)
    return int(number) if number.denominator == 1 else float(number)


def typed_slots(text: str, lang: str) -> list[list]:
    # ovos-typed-slots-transformer __init__.py _numbers: every number, its span, surface and JSON number
    return [[*m.char_span, m.text, _json_number(m.value)] for m in _kept(text, lang)]


def simple_ner(text: str, lang: str) -> list[list[str]]:
    # simple_NER simple_NER/annotators/numbers_ner.py NumberNER: lower case, short scale, written numbers only
    return [[m.text, m.value] for m in tag_numbers(text.lower(), lang, scale=Scale.SHORT)
            if m.form is not Form.DIGITS and Reason.ARTICLE not in m.reasons]


def utterance_normalizer(text: str, lang: str) -> list[list[str]]:
    # ovos-utterance-normalizer normalizer.py numbers_to_digits: cardinals in words, no article or homograph
    return [[m.text, m.value] for m in tag_numbers(text, lang)
            if m.kind is Kind.CARDINAL and m.form is not Form.DIGITS
            and not m.reasons & {Reason.ARTICLE, Reason.HOMOGRAPH}]


READERS = {"ovos-skill-count": count, "ovos-skill-volume": volume, "ovos-skill-number-facts": number_facts,
           "ovos-skill-days-in-history": days_in_history, "ovos-skill-mark1-ctrl": mark1, "simple_NER": simple_ner,
           "ovos-typed-slots-transformer": typed_slots, "ovos-utterance-normalizer": utterance_normalizer}


class TestConsumerReadings(unittest.TestCase):
    def test_every_file_has_a_reader(self):
        self.assertEqual(sorted(p.stem for p in CONSUMERS.glob("*.jsonl")), sorted(READERS))

    def test_each_consumer_gets_its_reading(self):
        for path in sorted(CONSUMERS.glob("*.jsonl")):
            read = READERS[path.stem]
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            checked = 0
            for number, line in enumerate(lines, 1):
                row = json.loads(line)
                with self.subTest(consumer=path.stem, line=number, text=row["text"]):
                    self.assertEqual(read(row["text"], row["lang"]), row["reading"])
                checked += 1
            self.assertEqual(checked, len(lines), path.name)
