"""Tag schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.constants import TagKind
from app.schemas.common import SoftDeleteRead


class TagBase(BaseModel):
    name: str
    kind: TagKind = TagKind.USER


class TagCreate(TagBase):
    pass


class TagRead(SoftDeleteRead, TagBase):
    pass
