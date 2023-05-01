from fastapi import Depends, FastAPI
from pydantic import BaseModel

from model import Model, get_model

app = FastAPI(title="Toxicity Binary Classifier")


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    probabilities: list
    sentiment: int


@app.get("/health")
def health():
    return 'Ok'


@app.post("/predict", response_model=SentimentResponse)
def predict(request: SentimentRequest, model: Model = Depends(get_model)):
    sentiment, probabilities = model.predict(request.text)
    return SentimentResponse(
        sentiment=sentiment,
        probabilities=probabilities
    )
