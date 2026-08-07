from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
class MemoryClass(StrEnum):
 TRANSIENT='transient'; WORKING='working'; EPISODIC='episodic'; SEMANTIC='semantic'; PROCEDURAL='procedural'; IDENTITY_SENSITIVE='identity_sensitive'; DORMANT_ASPIRATION='dormant_aspiration'; ARCHIVE='archive'
class MemoryDecision(StrEnum):
 RETAIN='retain'; PROMOTE='promote'; ARCHIVE='archive'; REVIEW='review'
@dataclass(slots=True)
class MemoryCandidate:
 reference_id:str; label:str; source_kind:str; salience:float; confidence:float; memory_class:MemoryClass; decision:MemoryDecision; reason:str; world:str|None=None; occurred_at:str|None=None; metadata:dict[str,Any]=field(default_factory=dict)
 def __post_init__(self):
  if not self.reference_id.strip() or not self.label.strip() or not self.reason.strip(): raise ValueError('required fields missing')
  if not 0<=float(self.salience)<=1 or not 0<=float(self.confidence)<=1: raise ValueError('scores must be between 0 and 1')
 def to_dict(self):
  d=asdict(self); d['memory_class']=self.memory_class.value; d['decision']=self.decision.value; return d
