# -*- coding: utf-8 -*-
__all__ = ('AppendStatement',)

from typing import Any, ClassVar, Iterator, Mapping, Optional
import typing

import attr
import kaskara

from .base import StatementTransformation, StatementTransformationSchema
from ..base import Transformation, TransformationSchema
from ..config import TransformationSchemaConfig
from ... import exceptions as exc
from ...snippet import (StatementSnippet, SnippetDatabase,
                        StatementSnippetDatabase)
from ...core import (Replacement, FileLine, FileLocationRange, FileLocation,
                     LocationRange)

if typing.TYPE_CHECKING:
    from ..problem import Problem


@attr.s(frozen=True, repr=False, auto_attribs=True)
class AppendStatement(StatementTransformation):
    _schema: 'AppendStatementSchema'
    at: kaskara.Statement
    insertion: StatementSnippet

    def __repr__(self) -> str:
        s = "AppendStatement[{}]<{}>"
        return s.format(str(self.location), repr(str(self.insertion.content)))

    @property
    def location(self) -> FileLocationRange:
        return self.at.location

    @property
    def schema(self) -> TransformationSchema:
        return self._schema

    @property
    def line(self) -> FileLine:
        return FileLine(self.location.filename, self.location.start.line)

    def to_replacement(self) -> Replacement:
        at_location = self.location

        # TODO toggle via preserve_indentation
        # determine and apply appropriate indentation
        indentation = self._schema._indentation(self.at)
        source = self.insertion.content
        source = self._schema._source_with_indentation(source, indentation)
        source += f'\n{indentation}'

        r = FileLocationRange(at_location.filename,
                              LocationRange(at_location.stop, at_location.stop))
        return Replacement(r, source)


class AppendStatementSchema(StatementTransformationSchema):
    def should_insert_at_location(self, location: FileLocation) -> bool:
        """Determines whether an insertion should be made at a location."""
        problem = self._problem
        if not problem.analysis:
            return True
        if not problem.analysis.is_inside_function(location):
            return False
        return True

    def all_at_statement(self,
                         statement: kaskara.Statement
                         ) -> Iterator[Transformation]:
        location = FileLocation(statement.location.filename,
                                statement.location.start)
        if not self.should_insert_at_location(location):
            yield from []
        for snippet in self.viable_snippets(statement):
            yield AppendStatement(self, statement, snippet)


@attr.s(frozen=True)
class AppendStatementSchemaConfig(TransformationSchemaConfig):
    NAME: ClassVar[str] = 'append-statement'

    preserve_indentation: bool = attr.ib()

    @classmethod
    def from_dict(cls,
                  d: Mapping[str, Any],
                  dir_: Optional[str] = None
                  ) -> 'TransformationSchemaConfig':
        if 'preserve_indentation' not in d:
            preserve_indentation = True
        else:
            preserve_indentation = d['preserve-indentation']
            if not isinstance(preserve_indentation, bool):
                m = "illegal value for 'preserve-indentation': expected bool"
                raise exc.BadConfigurationException(m)

        return AppendStatementSchemaConfig(
            preserve_indentation=preserve_indentation)

    def build(self,
              problem: 'Problem',
              snippets: SnippetDatabase
              ) -> 'TransformationSchema':
        assert isinstance(snippets, StatementSnippetDatabase)
        return AppendStatementSchema(problem=problem, snippets=snippets)
