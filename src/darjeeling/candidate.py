__all__ = ['Candidate', 'all_single_edit_patches']

from typing import List, Iterator, Dict, FrozenSet, Iterable

import attr
from bugzoo.core.patch import Patch

from .core import Replacement, FileLine
from .problem import Problem
from .transformation import Transformation


@attr.s(frozen=True, repr=False)
class Candidate(object):
    """
    Represents a candidate repair as a set of atomic program transformations.
    """
    transformations = attr.ib(type=FrozenSet[Transformation],
                              converter=frozenset)  # type: ignore  # bug in mypy (should be fixed in v0.610)  # noqa: pycodestyle

    def to_diff(self, problem: Problem) -> Patch:
        """
        Transforms this candidate patch into a concrete, unified diff.
        """
        replacements = \
            map(lambda t: t.to_replacement(problem), self.transformations)
        replacements_by_file = {}  # type: Dict[str, List[Replacement]]
        for rep in replacements:
            fn = rep.location.filename
            if fn not in replacements_by_file:
                replacements_by_file[fn] = []
            replacements_by_file[fn].append(rep)
        # FIXME order each collection of replacements by location
        return problem.sources.replacements_to_diff(replacements_by_file)

    def lines_changed(self, problem: Problem) -> List[FileLine]:
        """
        Returns a list of source lines that are changed by this candidate
        patch.
        """
        replacements = \
            map(lambda t: t.to_replacement(problem), self.transformations)
        locations = [rep.location for rep in replacements]
        lines = [FileLine(loc.filename, loc.start.line)
                 for loc in locations]
        return lines

    def __repr__(self) -> str:
        tx = [repr(t) for t in self.transformations]
        return "Candidate({})".format('; '.join(tx))


def all_single_edit_patches(transformations: Iterable[Transformation]
                            ) -> Iterable[Candidate]:
    """
    Returns an iterator over all of the single-edit patches that can be
    composed using a provided source of transformations.
    """
    for t in transformations:
        yield Candidate([t])  # type: ignore
