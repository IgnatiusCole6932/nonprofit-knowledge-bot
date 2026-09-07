import sys

from src.knowledge_bot import KnowledgeBot, InfraiVectorClient, KnowledgeNote, Question, build_bot


NOTES = [
    KnowledgeNote("Donor receipts", "Send a receipt within seven days of a confirmed donation.", "receipts"),
    KnowledgeNote("Volunteer reminders", "Send the shift reminder 48 hours before the volunteer start time.", "volunteers"),
    KnowledgeNote("Campaign reporting", "Share the campaign report with the board on the first Monday of each month.", "campaigns"),
]


if __name__ == "__main__":
    bot = build_bot()
    bot.index_notes(NOTES)
    question = " ".join(sys.argv[1:]) or "When should we remind a volunteer?"
    print(bot.answer(Question(question)))

