from src.knowledge_bot import KnowledgeBot, KnowledgeNote, Question


class FakeEmbeddings:
    def create(self, model, input):
        class Item:
            embedding = [1.0, 0.0]

        class Result:
            data = [Item()]

        return Result()


class FakeOpenAI:
    embeddings = FakeEmbeddings()


class FakeVectors:
    def create_collection(self, payload):
        return {}

    def upsert(self, payload):
        return {}

    def query(self, payload):
        return {"matches": [{"metadata": {"text": "Send the shift reminder 48 hours before the volunteer start time."}}]}


def test_volunteer_question_returns_reminder_policy(monkeypatch):
    monkeypatch.setattr("src.knowledge_bot.OpenAI", lambda **kwargs: FakeOpenAI())
    bot = KnowledgeBot(FakeVectors(), "from-environment")
    answer = bot.answer(Question("When should we remind a volunteer?", topic="volunteers"))
    assert "48 hours" in answer

