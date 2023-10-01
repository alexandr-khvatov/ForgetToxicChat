import numpy as np
import onnxruntime
from onnxruntime import (
    InferenceSession,
    SessionOptions
)
from transformers import AutoTokenizer

from config import cfg


def _create_onnx_session(
        model_path: str,
        provider: str = "CPUExecutionProvider"
) -> InferenceSession:
    options = SessionOptions()
    options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = InferenceSession(model_path, options, providers=[provider])
    session.disable_fallback()
    return session


def softmax(vec):
    exponential = np.exp(vec)
    probs = exponential / np.sum(exponential)
    return probs


class Model:

    def __init__(self, path_model, path_tokenizer, threshold):
        self.tokenizer = AutoTokenizer.from_pretrained(path_tokenizer)
        session = _create_onnx_session(
            model_path=path_model,
            provider='CPUExecutionProvider')
        self.session = session
        self.MAX_LEN = 64
        self.threshold = threshold

    def predict(self, text):
        inputs = self.tokenizer(
            text.lower(),
            add_special_tokens=True,
            max_length=self.MAX_LEN,
            return_token_type_ids=False,
            truncation=True,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='np',
        )
        input_feed = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }
        logits = self.session.run(
            output_names=["logits"],
            input_feed=input_feed
        )[0][0]

        probs = softmax(logits)
        sentiment = 1 if probs[1] >= self.threshold else 0
        return sentiment, probs.tolist()


model = Model(
    path_model='assets/model_onnx/model_onnx.onnx',
    path_tokenizer='assets/tokenizer',
    threshold=cfg.threshold
)


def get_model():
    return model
