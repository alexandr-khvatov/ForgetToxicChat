import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from config.config import config
from services.toxicity.toxicity_classifier import ToxicityClassifier


# MODEL_PATH = './save_model'
#
# tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
# model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
#
# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# if torch.cuda.is_available():
#     model.cuda()
#
#
# def predict(text):
#     encoding = tokenizer.encode_plus(
#         text,
#         add_special_tokens=True,
#         max_length=64,
#         return_token_type_ids=False,
#         truncation=True,
#         padding='max_length',
#         return_attention_mask=True,
#         return_tensors='pt',
#     )
#
#     out = {
#         'text': text,
#         'input_ids': encoding['input_ids'].flatten(),
#         'attention_mask': encoding['attention_mask'].flatten()
#     }
#
#     input_ids = out["input_ids"].to(device)
#     attention_mask = out["attention_mask"].to(device)
#     with torch.no_grad():
#         outputs = model(
#             input_ids=input_ids.unsqueeze(0),
#             attention_mask=attention_mask.unsqueeze(0)
#         )
#
#     proba = torch.nn.functional.softmax(outputs.logits, dim=1).cpu().numpy()[0]
#     prediction = np.argmax(proba)
#
#     return prediction, proba
# while True:
#     txt = input()
#     start_time = time.time()
#     prediction, proba = predict(txt.lower())
#     print("--- %s seconds ---" % (time.time() - start_time))
#     print(f'proba: {proba} -> prediction: {prediction}')


class BertToxicityClassifier(ToxicityClassifier):

    def __init__(self, path_model, path_tokenizer):
        self.tokenizer = AutoTokenizer.from_pretrained(path_tokenizer)
        model = AutoModelForSequenceClassification.from_pretrained(path_model)
        model.eval()
        self.device = torch.device("cpu")
        self.model = model.to(self.device)
        LABEL: dict[str, str] = {
            '0': 'НЕЙТРАЛЬНЫЙ',
            '1': 'ТОКСИЧНЫЙ'
        }
        self.LABEL = LABEL
        self.MAX_LEN = 64

    def predict(self, text: str):
        encoding = self.tokenizer.encode_plus(
            text.lower(),
            add_special_tokens=True,
            max_length=self.MAX_LEN,
            return_token_type_ids=False,
            truncation=True,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
        )

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            probabilities = torch.nn.functional.softmax((self.model(input_ids, attention_mask)).logits, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)
        predicted_class = predicted_class.cpu().item()
        probabilities = probabilities.flatten().cpu().numpy().tolist()
        return (
            confidence.item(),
            probabilities,
            predicted_class,
            self.LABEL[str(predicted_class)]
        )


model = BertToxicityClassifier(
    path_model=config.tg_bot.model_path,
    path_tokenizer=config.tg_bot.path_tokenizer)


def get_model():
    return model
