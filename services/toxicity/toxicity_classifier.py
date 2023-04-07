from abc import ABC, abstractmethod


class ToxicityClassifier(ABC):
    @abstractmethod
    def predict(self, msg: str) -> bool:
        return False


class RulesClassifier(ToxicityClassifier):

    def predict(self, msg: str) -> bool:
        return "Йц" in msg



