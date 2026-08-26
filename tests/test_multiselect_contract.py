import os

import pytest
from pydantic import ValidationError

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-that-is-at-least-32-chars")

from app.api.tests import AnswerRequest, QuestionInput


def test_question_input_accepts_eight_options_and_multiple_correct_answers():
    question = QuestionInput(
        text="Что я выберу?",
        options=["A", "B", "C", "D", "E", "F", "G", "H"],
        multiple=True,
        correct_options=["B", "D"],
    )
    assert question.correct_option == "B"
    assert question.correct_options == ["B", "D"]


def test_question_input_keeps_legacy_single_correct_option():
    question = QuestionInput(text="Один?", options=["Да", "Нет"], correct_option="Да")
    assert question.multiple is False
    assert question.correct_options == ["Да"]


def test_multiple_question_requires_two_correct_options():
    with pytest.raises(ValidationError):
        QuestionInput(text="Выбери", options=["A", "B"], multiple=True, correct_options=["A"])


def test_answer_request_normalizes_legacy_single_option():
    answer = AnswerRequest(question_id="00000000-0000-0000-0000-000000000001", selected_option="A")
    assert answer.selected_options == ["A"]


def test_answer_request_deduplicates_multi_selection():
    answer = AnswerRequest(question_id="00000000-0000-0000-0000-000000000001", selected_options=["A", "A", "C"])
    assert answer.selected_options == ["A", "C"]


def test_question_input_rejects_duplicate_options_after_trimming():
    with pytest.raises(ValidationError):
        QuestionInput(text="Повтор", options=[" A ", "A"], correct_option="A")
