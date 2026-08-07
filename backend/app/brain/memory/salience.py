from app.brain.context_engine.models import ContextKind
from .models import MemoryCandidate,MemoryClass,MemoryDecision
class SalienceEngine:
 def evaluate(self,item,*,repeated_count=1,user_confirmed=False,aspiration_signal=False,identity_sensitive=False):
  repeated_count=max(1,int(repeated_count)); salience=round(min(1.0,item.relevance*.45+item.confidence*.25+min(1,repeated_count/5)*.2+(1 if user_confirmed else 0)*.1),10)
  if identity_sensitive: mc,dec,reason=MemoryClass.IDENTITY_SENSITIVE,MemoryDecision.REVIEW,'Identity-related material requires explicit review.'
  elif aspiration_signal: mc,dec,reason=MemoryClass.DORMANT_ASPIRATION,(MemoryDecision.PROMOTE if user_confirmed else MemoryDecision.REVIEW),'Possible aspiration preserved even without current activity.'
  elif item.kind==ContextKind.LEARNING and repeated_count>=3: mc,dec,reason=MemoryClass.SEMANTIC,MemoryDecision.PROMOTE,'Repeated approved learning becomes semantic memory.'
  elif item.kind==ContextKind.EVENT and repeated_count>=3: mc,dec,reason=MemoryClass.PROCEDURAL,MemoryDecision.REVIEW,'Repeated event may represent a procedure.'
  elif salience>=.60: mc,dec,reason=MemoryClass.EPISODIC,MemoryDecision.PROMOTE,'High-salience event enters episodic memory.'
  elif salience>=.4: mc,dec,reason=MemoryClass.WORKING,MemoryDecision.RETAIN,'Relevant item stays in working memory.'
  elif salience>=.2: mc,dec,reason=MemoryClass.TRANSIENT,MemoryDecision.RETAIN,'Low-salience item retained temporarily.'
  else: mc,dec,reason=MemoryClass.ARCHIVE,MemoryDecision.ARCHIVE,'Very low-salience item archived.'
  return MemoryCandidate(item.reference_id,item.label,item.kind.value,salience,item.confidence,mc,dec,reason,item.world,item.occurred_at,{'repeated_count':repeated_count,'user_confirmed':user_confirmed})
