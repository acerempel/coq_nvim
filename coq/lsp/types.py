from dataclasses import dataclass
from typing import Literal, Optional, Sequence, Union

# https://microsoft.github.io/language-server-protocol/specification


@dataclass(frozen=True)
class _Position:
    line: int
    character: int


@dataclass(frozen=True)
class _Range:
    start: _Position
    end: _Position


@dataclass(frozen=True)
class TextEdit:
    newText: str
    range: _Range


@dataclass(frozen=True)
class InsertReplaceEdit:
    newText: str
    insert: _Range
    replace: _Range


_CompletionItemKind = int


@dataclass(frozen=True)
class MarkupContent:
    kind: Union[Literal["plaintext", "markdown"], str]
    value: str


_InsertTextFormat = int


@dataclass(frozen=True)
class CompletionItem:
    label: str
    additionalTextEdits: Optional[Sequence[TextEdit]] = None
    detail: Optional[str] = None
    documentation: Union[str, MarkupContent, None] = None
    filterText: Optional[str] = None
    insertText: Optional[str] = None
    insertTextFormat: Optional[_InsertTextFormat] = None
    kind: Optional[_CompletionItemKind] = None
    textEdit: Union[TextEdit, InsertReplaceEdit, None] = None


@dataclass(frozen=True)
class CompletionList:
    isIncomplete: bool
    items: Sequence[CompletionItem]


Resp = Union[None, Literal[0, False], Sequence[CompletionItem], CompletionList]
