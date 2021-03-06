import codecs
import hashlib
import os
import re
import sys
import urllib.request
from os import name, path
from time import sleep
from typing import Optional

import jsonpickle
from bs4 import BeautifulSoup
from bs4.element import Tag

jsonpickle.set_encoder_options("json", ensure_ascii=False)


class const:
    rate_limit_s: int = 2
    cache_dir: str = path.join(path.dirname(__file__), "cache")


def download_kani(url: str) -> Optional[BeautifulSoup]:
    """
    Download page from Wanikani
    There is a builtin sleep due to rate limiting from Wanikani
    """
    print(f"Searching cache for {url}")
    if (cache := search_cache(url)) is None:
        print(f"Downloading {url}")
        if url[0] == "/":
            wani_url = f"https://wanikani.com{url}"
        else:
            wani_url = url
        response = urllib.request.urlopen(wani_url)
        sleep(const.rate_limit_s)
        if response is None or response == "":
            return None
        html = response.read()
        write_cache(url, html)
    else:
        html = cache
        print(f"Retrieved {url} from cache")
    return make_soup(html)


class LevelItem:
    def __init__(self, character: str, url: str, level: int):
        self.character = character
        self.url = url
        self.level = level

    def get_soup(self) -> Optional[BeautifulSoup]:
        cache = path.join(const.cache_dir, self.url)
        if path.isfile(cache):
            with open(cache, "r") as f:
                return make_soup(f.read())
        else:
            html = download_kani(self.url)
            return html

    def __str__(self) -> str:
        return self.character


class WaniLevel:
    def __init__(
        self,
        radicals: list[LevelItem],
        kanji: list[LevelItem],
        vocab: list[LevelItem],
    ):
        self.radicals = radicals
        self.kanji = kanji
        self.vocab = vocab

    def __str__(self) -> str:
        radicals = " ".join([str(r) for r in self.radicals])
        kanji = " ".join([str(k) for k in self.kanji])
        vocab = " ".join([str(v) for v in self.vocab])
        return (
            f"radicals: {radicals}{os.linesep}Kanji: {kanji}{os.linesep}Vocab: {vocab}"
        )


class Radical:
    def __init__(self, character: str, name: str, level: int):
        self.character = character
        self.name = name
        self.level = level

    def __str__(self) -> str:
        return f"[Radical][{self.level}]{self.character}: {self.name}"


class Reading:
    def __init__(
        self,
    ):
        self.onyomi: list[str] = []
        self.kunyomi: list[str] = []
        self.nanori: list[str] = []
        self.mnemonic = ""

    def __str__(self) -> str:
        return (
            f"On'yomi: {', '.join(self.onyomi)}. Kun'yomi: {', '.join(self.kunyomi)}."
        )


class Kanji:
    class Meaning:
        def __init__(self):
            self.primary = ""
            self.alternatives: list[str] = []
            self.mnemonic = ""

        def __str__(self) -> str:
            return f"{self.primary}, {', '.join(self.alternatives)}."

    def __init__(
        self,
        character: str,
        name: str,
        radical_combination: list[str],
        meaning: Meaning,
        readings: Reading,
        found_in_vocabulary: list[str],
        level,
    ):
        self.character = character
        self.name = name
        self.radical_combinarion = radical_combination
        self.meaning = meaning
        self.readings = readings
        self.found_in_vocabulary = found_in_vocabulary
        self.level = level

    def __str__(self) -> str:
        return f"[Kanji][{self.level}]{self.character} - {self.name}"


class Vocab:
    class Meaning:
        def __init__(self):
            self.primary = ""
            self.alternatives: list[str] = []
            self.explanation = ""

    class Reading:
        def __init__(self, reading: str = "", explanation: str = ""):
            self.reading = reading
            self.explanation = explanation

    class Context:
        def __init__(self, jp: str, eng: str):
            self.jp = jp
            self.eng = eng

    def __init__(
        self,
        level: int,
        vocab: str,
        reading: Reading,
        meaning: Meaning,
        context_sentences: list[Context],
        kanji_composition: list[str],
    ):
        self.level = level
        self.vocab = vocab
        self.reading = reading
        self.meaning = meaning
        self.context_sentences = context_sentences
        self.kanji_composition = kanji_composition


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def cache_file(url: str) -> str:
    """
    return th
    """
    hash = str(int(hashlib.md5(url.encode("utf-8")).hexdigest(), 16))
    return path.join(const.cache_dir, hash)


def search_cache(url: str) -> Optional[str]:
    """
    Search the cache directory to see if the html was already
    downloaded for a specific endpoint
    """
    if not path.exists(const.cache_dir):
        os.mkdir(const.cache_dir)
        return None
    url_path = cache_file(url)
    if path.isfile(url_path):
        print(f"Found {url_path}")
        with open(url_path, "r") as f:
            return f.read()
    return None


def write_cache(url: str, html: bytes) -> None:
    print(f"caching {url}")
    with open(cache_file(url), "wb") as f:
        f.write(html)


def get_level_html(level: int) -> Optional[BeautifulSoup]:
    if level < 1 or level > 60:
        return None

    endpoint = f"https://www.wanikani.com/level/{level}"
    return download_kani(endpoint)


def parse_radical_soup(radical_soup: BeautifulSoup) -> Radical:
    name = (
        radical_soup.body.find("span", {"class": "radical-icon"})
        .parent.findAll(text=True, recursive=False)[2]
        .__str__()
        .strip()
    )
    character = radical_soup.body.find("span", {"class": "radical-icon"}).text
    level = int(radical_soup.find("a", {"class": "level-icon"}).text)
    return Radical(character, name, level)


def parse_kanji_soup(kanji_soup: BeautifulSoup) -> Kanji:
    level_a = kanji_soup.find("a", {"class": "level-icon"})
    level = int(level_a.text)
    name = level_a.parent.findAll(text=True, recursive=False)[
        2].__str__().strip()
    character = kanji_soup.find("span", {"class": "kanji-icon"}).text
    radical_combination: list[str] = [
        span.text.strip()
        for span in kanji_soup.find_all("span", {"class": "radical-icon"})
    ]

    meaning = Kanji.Meaning()
    meaning_section = kanji_soup.find("section", id="meaning")
    meaning.mnemonic = (
        meaning_section.find("section", {"class": "mnemonic-content"})
        .find("p")
        .text.replace("\n", "")
    )
    for alternative_meaning in meaning_section.find_all(
        "div", {"class": "alternative-meaning"}
    ):
        p = alternative_meaning.find("p").text
        h3 = alternative_meaning.find("h2").text

        if h3 == "Primary":
            meaning.primary = p
        elif "Alternative" in h3:
            meaning.alternatives.append(p)

    reading = Reading()
    reading_section = kanji_soup.find("section", id="reading")
    spans = reading_section.find_all(
        "div", {"class": re.compile(r"span[0-9]+")})

    for span in spans:
        h3 = span.find("h3").text
        readings = span.find("p")
        if readings is None or (readings := readings.text.strip()) == "None":
            continue
        list_ptr = None

        if h3 == "On???yomi":
            list_ptr = reading.onyomi
        elif h3 == "Kun???yomi":
            list_ptr = reading.kunyomi
        elif h3 == "Nanori":
            list_ptr = reading.nanori

        if list_ptr is None:
            continue

        list_ptr.extend([r.strip() for r in readings.split(",")])

    reading.mnemonic = (
        reading_section.find(
            "section", {"class": "mnemonic-content"}).find("p").text
    )

    found_in_vocab = [
        li.find("span", {"class": "character"}).text
        for li in kanji_soup.find_all("li", {"class": re.compile(r"vocabulary-[0-9]+")})
    ]

    return Kanji(
        character=character,
        name=name,
        radical_combination=radical_combination,
        meaning=meaning,
        readings=reading,
        found_in_vocabulary=found_in_vocab,
        level=level,
    )


def parse_vocab_soup(vocab_soup: BeautifulSoup) -> Vocab:
    level = vocab_soup.find("a", {"class": "level-icon"}).text
    vocab = vocab_soup.find("span", {"class": "vocabulary-icon"}).text

    reading_section = vocab_soup.find("section", id="reading")
    jp_reading = reading_section.find(
        "p", {"class": "pronunciation-variant", "lang": "ja"}
    ).text
    reading_explanation = (
        reading_section.find(
            "section", {"class": "mnemonic-content mnemonic-content--new"}
        )
        .text.replace("\n", "")
        .strip()
    )
    reading = Vocab.Reading(jp_reading, reading_explanation)

    meaning = Vocab.Meaning()
    meaning_section = vocab_soup.find("section", id="meaning")
    meaning_divs = meaning_section.find_all(
        "div", {"class": "alternative-meaning"})
    for mdiv in meaning_divs:
        h2 = mdiv.find("h2").text
        p = mdiv.find("p").text
        if h2 == "Primary":
            meaning.primary = p
        elif "Alternative" in h2:
            meaning.alternatives.append(p)
    meaning.explanation = (
        meaning_section.find(
            "section", {"class": "mnemonic-content mnemonic-content--new"}
        )
        .text.replace("\n", "")
        .strip()
    )

    context_sentences: list[Vocab.Context] = []
    context_section = vocab_soup.find("section", id="context")
    context_groups = context_section.find_all(
        "div", {"class": "context-sentence-group"}
    )
    for cg in context_groups:
        ps = cg.find_all("p")
        context_sentences.append(
            Vocab.Context(
                jp=ps[0].text.replace("\n", ""), eng=ps[1].text.replace("\n", "")
            )
        )

    kanji_composition = [
        span.text.strip()
        for span in vocab_soup.find("section", id="components").find_all(
            "span", {"class": "character", "lang": "ja"}
        )
    ]

    return Vocab(
        level=level,
        vocab=vocab,
        reading=reading,
        meaning=meaning,
        context_sentences=context_sentences,
        kanji_composition=kanji_composition,
    )


def parse_level_soup(level_html: BeautifulSoup, level: int) -> WaniLevel:
    """
    Parse WaniKani level page html to get radicals, kanji, and vocab and the url to their page
    """
    radicals: list[LevelItem] = []
    kanji: list[LevelItem] = []
    vocab: list[LevelItem] = []

    radical_lis = level_html.find_all(
        "li", {"class": re.compile(r"radical-[0-9]+")})
    kanji_lis = level_html.find_all(
        "li", {"class": re.compile(r"kanji-[0-9]+")})
    vocab_lis = level_html.find_all(
        "li", {"class": re.compile(r"vocabulary-[0-9]+")})

    def add_to_list(lis: list[Tag], l: list[LevelItem]) -> None:
        for li in lis:
            href = li.find("a").attrs["href"]
            character = li.find(
                "span", {"class": "character", "lang": "ja"}
            ).text.strip()
            l.append(LevelItem(character, href, level))

    print(
        f"{len(radical_lis)} radicals, {len(kanji_lis)} kanji, {len(vocab_lis)} vocab  found"
    )

    add_to_list(radical_lis, radicals)
    add_to_list(kanji_lis, kanji)
    add_to_list(vocab_lis, vocab)

    return WaniLevel(radicals, kanji, vocab)


if __name__ == "__main__":
    radicals: list[Radical] = []
    kanji: list[Kanji] = []
    vocab: list[Vocab] = []
    for level in range(1, 61):
        html = get_level_html(level)
        if html is None:
            print("Did not get html")
        parsed = parse_level_soup(html, level)
        for v in parsed.vocab:
            vocab_html = v.get_soup()
            if vocab_html is None:
                continue
            vocab.append(parse_vocab_soup(vocab_html))

        for r in parsed.radicals:
            radical_html = r.get_soup()
            if radical_html is None:
                continue
            radicals.append(parse_radical_soup(radical_html))

        for k in parsed.kanji:
            kanji_soup = k.get_soup()
            if kanji_soup is None:
                continue
            kanji.append(parse_kanji_soup(kanji_soup))

    with codecs.open(path.join(const.cache_dir, "radicals.json"), "w", "utf-8") as f:
        f.write(jsonpickle.encode(radicals, unpicklable=False))

    with codecs.open(path.join(const.cache_dir, "kanji.json"), "w", "utf-8") as f:
        f.write(jsonpickle.encode(kanji, unpicklable=False))
    with codecs.open(path.join(const.cache_dir, "vocab.json"), "w", "utf-8") as f:
        f.write(jsonpickle.encode(vocab, unpicklable=False))
