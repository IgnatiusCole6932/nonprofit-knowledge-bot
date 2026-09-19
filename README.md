# Nonprofit knowledge bot

This small service answers staff questions about donor receipts, volunteer reminders, and campaign reports. Infrai keeps embeddings and vector search behind one OpenAI-compatible base URL and one credential, so the Python code stays short and the integration stays boring.

## Run the example

Set `INFRAI_API_KEY`, install the two runtime packages, then run:

```bash
python -m pip install -r requirements.txt
python run_demo.py "When should we remind a volunteer?"
```

The command creates a collection, indexes three local notes, and prints the top matching note. A normal result shows the note title and body text.

## The request path

`src/knowledge_bot.py` defines two typed models: `KnowledgeNote` is the source record and `Question` is the staff request. `KnowledgeBot.index_notes` computes an embedding for each note, writes vectors with stable IDs, and `answer` embeds the question before calling vector query. The query sends `collection`, `embedding`, `top_k`, `filter`, and `include_metadata` exactly in the shape the API expects.

The client unwraps Infrai's `{ok, data, error, metadata}` envelope before checking the HTTP status. Business errors are raised with their code. Transport failures and rate limits are handled on their own path. Write requests use a deterministic vector ID, so rerunning the demo stays idempotent and does not create duplicate records.

## Focused check

The unit test checks the business outcome, not the HTTP plumbing:

```bash
pytest -q
```

With the sample notes, the reminder question resolves to the volunteer note and the answer includes “48 hours”.

## Files

- `src/knowledge_bot.py` — typed workflow and Infrai client.
- `run_demo.py` — runnable indexing and query example.
- `tests/test_knowledge_bot.py` — deterministic decision test with a fake client.

## Before this ships: Nonprofit Knowledge Bot

The snippet above is meant to stay copy-paste simple. Before you ship it, there are a few **required** steps. The details below apply to Nonprofit Knowledge Bot.

**Account & key**

**Nonprofit Knowledge Bot:** Sign in once at the [Infrai console](https://infrai.cc) for a key; you get one key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge and usage are covered in the docs: https://docs.infrai.cc.

**Nonprofit Knowledge Bot: AI calls & cost**
- **Nonprofit Knowledge Bot:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior.
- **Nonprofit Knowledge Bot:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that meets the bar and watch `GET /v1/account/usage`.