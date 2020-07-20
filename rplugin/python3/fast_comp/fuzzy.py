from dataclasses import asdict, dataclass
from locale import strxfrm
from typing import Any, Callable, Dict, Iterator, Sequence, Set, Union, cast

from .nvim import VimCompletion
from .types import SourceFeed, FuzzyOptions, Payload, SourceCompletion, Step


@dataclass(frozen=True)
class FuzzyStep:
    step: Step
    non_overlapping: bool
    full_match: bool
    matches: Dict[int, str]
    rank: Sequence[Union[int, str]]


def fuzzify(feed: SourceFeed, step: Step) -> FuzzyStep:
    original = feed.context.alnums
    normalized = step.normalized_alnums
    matches: Dict[int, str] = {}
    idx = 0

    for o_char, char in zip(original, normalized):
        m_idx = normalized.find(char, idx)
        if m_idx != -1:
            matches[m_idx] = o_char
            idx = m_idx + 1

    rank = (len(matches) * -1, sum(matches))
    full_match = normalized.startswith(original)
    non_overlapping = True
    return FuzzyStep(
        step=step,
        non_overlapping=non_overlapping,
        full_match=full_match,
        matches=matches,
        rank=rank,
    )


def rank(fuzz: FuzzyStep) -> Sequence[Union[float, int, str]]:
    comp = fuzz.step.comp
    text = strxfrm(comp.sortby or comp.label or fuzz.step.text).lower()
    return (*fuzz.rank, fuzz.step.priority * -1, text)


def gen_payload(comp: SourceCompletion) -> Payload:
    return Payload(
        row=comp.position.row,
        col=comp.position.col,
        old_prefix=comp.old_prefix,
        new_prefix=comp.new_prefix,
        old_suffix=comp.old_suffix,
        new_suffix=comp.new_suffix,
    )


def context_gen(fuzz: FuzzyStep) -> str:
    match_set = fuzz.matches
    comp = fuzz.step.comp
    text = fuzz.step.text
    label = comp.label or text

    def gen() -> Iterator[str]:
        for idx, char in enumerate(text):
            inclusive = idx in match_set
            if inclusive and (idx - 1) not in match_set:
                yield "["
            m_char = match_set[idx] if inclusive else char
            yield m_char
            if inclusive and (idx + 1) not in match_set:
                yield "]"

    fuzzy_label = "".join(gen())
    return f"{label} <- {fuzzy_label}"


def vimify(fuzz: FuzzyStep) -> VimCompletion:
    step = fuzz.step
    source = f"[{step.source_shortname}]"
    comp = step.comp
    menu = f"{comp.kind} {source}" if comp.kind else source
    abbr = (
        (comp.label or (comp.new_prefix + comp.new_suffix))
        if fuzz.full_match
        else context_gen(fuzz)
    )
    user_data = gen_payload(comp=comp)
    ret = VimCompletion(
        equal=1,
        icase=1,
        dup=1,
        empty=1,
        word="",
        abbr=abbr,
        menu=menu,
        info=comp.doc,
        user_data=asdict(user_data),
    )
    return ret


def fuzzer(
    options: FuzzyOptions, limits: Dict[str, float]
) -> Callable[[SourceFeed, Iterator[Step]], Iterator[VimCompletion]]:
    def fuzzy(feed: SourceFeed, steps: Iterator[Step]) -> Iterator[VimCompletion]:
        seen: Set[str] = set()
        seen_by_source: Dict[str, int] = {}

        fuzzy_steps = (fuzzify(feed, step=step) for step in steps)
        for fuzz in sorted(fuzzy_steps, key=cast(Callable[[FuzzyStep], Any], rank)):
            step = fuzz.step
            source = step.source
            seen_count = seen_by_source.get(source, 0) + 1
            seen_by_source[source] = seen_count
            text = step.text
            matches = len(fuzz.matches)

            if (
                seen_count <= limits[source]
                and text not in seen
                and fuzz.non_overlapping
                and (fuzz.full_match or matches >= options.min_match)
            ):
                seen.add(text)
                yield vimify(fuzz=fuzz)

    return fuzzy
