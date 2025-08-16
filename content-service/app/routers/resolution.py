from fastapi import APIRouter
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
from pathlib import Path
router = APIRouter(prefix="/resolution", tags=["Resolution"])
MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "all-MiniLM-L6-v2"
model = SentenceTransformer(str(MODEL_PATH))

class ResolutionAnswer(BaseModel):
    questionId: int
    studentAnswer: str
    modelAnswer: str

@router.post("/score-resolution")
def score_resolution(answer: ResolutionAnswer):
    emb_model = model.encode(answer.modelAnswer, convert_to_tensor=True)
    emb_student = model.encode(answer.studentAnswer, convert_to_tensor=True)
    similarity = util.cos_sim(emb_model, emb_student).item()
    score = round(similarity * 100)  # convert similarity to percentage
    return {"questionId": answer.questionId, "score": score, "similarity": similarity}
