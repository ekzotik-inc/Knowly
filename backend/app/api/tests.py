from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.models import (
    Question,
    ResultAnswer,
    SessionAnswer,
    Test,
    TestQuestion,
    TestResult,
    TestSession,
    User,
    Profile,
)
from app.db.session import get_db
from app.services.analytics import record_event
from app.services.payments import user_has_entitlement
from app.services.progression import award_xp

router = APIRouter(prefix="/api/v1", tags=["tests"])


class QuestionInput(BaseModel):
    text: str = Field(min_length=3, max_length=500)
    options: list[str] = Field(min_length=2, max_length=8)
    correct_option: str | None = Field(default=None, min_length=1, max_length=255)
    correct_options: list[str] = Field(default_factory=list, max_length=8)
    multiple: bool = False
    difficulty: Literal["easy", "medium", "hard", "personal"] = "easy"
    category: str | None = Field(default=None, max_length=64)
    is_secret: bool = False

    @model_validator(mode="after")
    def normalize_correct_options(self) -> "QuestionInput":
        self.options = [item.strip() for item in self.options if item.strip()]
        if len(set(self.options)) != len(self.options):
            raise ValueError("Варианты ответа не должны повторяться")
        selected = list(dict.fromkeys([item.strip() for item in self.correct_options if item.strip()]))
        if not selected and self.correct_option:
            selected = [self.correct_option.strip()]
        if self.multiple and len(selected) < 2:
            raise ValueError("Для мультивыбора отметьте минимум два правильных варианта")
        if not self.multiple and len(selected) != 1:
            raise ValueError("Отметьте ровно один правильный вариант")
        self.correct_options = selected
        self.correct_option = selected[0]
        return self


class CreateTestRequest(BaseModel):
    title: str = Field(default="Насколько ты меня знаешь?", min_length=3, max_length=128)
    privacy_mode: Literal["public", "friends", "private"] = "public"
    expires_hours: int | None = Field(default=None, ge=1, le=168)
    max_attempts: int | None = Field(default=None, ge=1, le=1000)
    secret_message_80: str | None = Field(default=None, max_length=500)
    secret_message_100: str | None = Field(default=None, max_length=500)
    questions: list[QuestionInput] = Field(min_length=3, max_length=15)


class TestSummary(BaseModel):
    id: uuid.UUID
    title: str
    public_token: str
    status: str
    question_count: int
    attempt_count: int = 0
    average_percentage: int = 0
    best_percentage: int = 0


class PublicQuestion(BaseModel):
    id: uuid.UUID
    text: str
    options: list[str]
    position: int
    multiple: bool = False


class PublicTest(BaseModel):
    id: uuid.UUID
    title: str
    owner_name: str
    public_token: str
    questions: list[PublicQuestion]


class StartSessionResponse(BaseModel):
    session_id: uuid.UUID
    test_id: uuid.UUID
    total_questions: int


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option: str | None = Field(default=None, min_length=1, max_length=255)
    selected_options: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def normalize_selected_options(self) -> "AnswerRequest":
        selected = list(dict.fromkeys([item.strip() for item in self.selected_options if item.strip()]))
        if not selected and self.selected_option:
            selected = [self.selected_option.strip()]
        if not selected:
            raise ValueError("Выберите хотя бы один вариант")
        self.selected_options = selected
        self.selected_option = selected[0]
        return self


class ResultResponse(BaseModel):
    result_id: uuid.UUID
    test_id: uuid.UUID
    correct_answers: int
    total_questions: int
    percentage: int


class ReviewItem(BaseModel):
    question_id: uuid.UUID
    selected_option: str
    correct_option: str
    selected_options: list[str] = Field(default_factory=list)
    correct_options: list[str] = Field(default_factory=list)
    is_correct: bool


class ResultDetail(ResultResponse):
    review_locked: bool
    review: list[ReviewItem]


class StatisticsResponse(BaseModel):
    tests_count: int
    attempts_count: int
    average_percentage: int
    best_percentage: int | None


class AttemptResponse(BaseModel):
    result_id: uuid.UUID
    participant_name: str
    percentage: int
    correct_answers: int
    total_questions: int
    completed_at: datetime | None
    attempt_number: int


class LeaderboardEntry(BaseModel):
    participant_name: str
    best_percentage: int
    attempts_count: int
    latest_percentage: int


class TestAnalyticsResponse(BaseModel):
    test_id: uuid.UUID
    title: str
    total_attempts: int
    unique_participants: int
    average_percentage: int
    best_percentage: int
    attempts: list[AttemptResponse]
    leaderboard: list[LeaderboardEntry]


def _new_public_token() -> str:
    return secrets.token_urlsafe(12).replace("-", "_").replace(".", "_")[:24]


@router.post("/tests", response_model=TestSummary, status_code=status.HTTP_201_CREATED)
async def create_test(
    request: CreateTestRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TestSummary:
    for item in request.questions:
        options = [option.strip() for option in item.options if option.strip()]
        if len(options) < 2 or len(options) > 8:
            raise HTTPException(status_code=422, detail="У вопроса должно быть от 2 до 8 вариантов")
        if len(set(options)) != len(options):
            raise HTTPException(status_code=422, detail="Варианты ответа не должны повторяться")
        if any(option not in options for option in item.correct_options):
            raise HTTPException(status_code=422, detail="Правильные ответы должны быть вариантами вопроса")

    test = Test(
        id=uuid.uuid4(),
        owner_id=current_user.id,
        title=request.title,
        mode="know_me",
        public_token=_new_public_token(),
        status="published",
        privacy_mode=request.privacy_mode,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=request.expires_hours) if request.expires_hours else None,
        max_attempts=request.max_attempts,
        secret_message_80=request.secret_message_80,
        secret_message_100=request.secret_message_100,
    )
    db.add(test)
    await db.flush()

    for position, item in enumerate(request.questions):
        options = [option.strip() for option in item.options if option.strip()]
        question = Question(
            id=uuid.uuid4(),
            owner_id=current_user.id,
            text=item.text,
            options=options,
            correct_option=item.correct_options[0],
            correct_options=item.correct_options,
            multiple_answers=item.multiple,
            difficulty=item.difficulty,
            category=item.category,
            is_secret=item.is_secret,
        )
        db.add(question)
        await db.flush()
        db.add(TestQuestion(test_id=test.id, question_id=question.id, position=position))

    await award_xp(db, user_id=current_user.id, amount=25, created_test=True)
    await record_event(db, event_name="test_created", actor_user_id=current_user.id, test_id=test.id)
    await db.commit()
    return TestSummary(
        id=test.id,
        title=test.title,
        public_token=test.public_token,
        status=test.status,
        question_count=len(request.questions),
    )


@router.get("/tests", response_model=list[TestSummary])
async def list_my_tests(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[TestSummary]:
    result = await db.execute(select(Test).where(Test.owner_id == current_user.id).order_by(Test.created_at.desc()))
    tests = list(result.scalars())
    response: list[TestSummary] = []
    for test in tests:
        count = len((await db.execute(select(TestQuestion.id).where(TestQuestion.test_id == test.id))).scalars().all())
        attempts = list((await db.execute(select(TestResult).where(TestResult.test_id == test.id))).scalars())
        response.append(TestSummary(
            id=test.id, title=test.title, public_token=test.public_token, status=test.status,
            question_count=count, attempt_count=len(attempts),
            average_percentage=round(sum(item.percentage for item in attempts) / len(attempts)) if attempts else 0,
            best_percentage=max((item.percentage for item in attempts), default=0),
        ))
    return response


@router.get("/tests/{test_id}/analytics", response_model=TestAnalyticsResponse)
async def get_test_analytics(
    test_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TestAnalyticsResponse:
    test = await db.scalar(select(Test).where(Test.id == test_id, Test.owner_id == current_user.id))
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    rows = await db.execute(
        select(TestResult, User, Profile)
        .join(User, User.id == TestResult.participant_user_id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .where(TestResult.test_id == test.id)
        .order_by(TestResult.created_at.desc())
    )
    attempts: list[AttemptResponse] = []
    participant_attempts: dict[str, list[TestResult]] = {}
    participant_names: dict[str, str] = {}
    for result, participant, profile in rows.all():
        participant_id = str(participant.id)
        history = participant_attempts.setdefault(participant_id, [])
        participant_names[participant_id] = (profile.display_name if profile else None) or participant.first_name or "Участник"
        history.append(result)
        attempts.append(AttemptResponse(
            result_id=result.id,
            participant_name=participant_names[participant_id],
            percentage=result.percentage,
            correct_answers=result.correct_answers,
            total_questions=result.total_questions,
            completed_at=result.created_at,
            attempt_number=len(history),
        ))
    leaderboard = [LeaderboardEntry(
        participant_name=participant_names[participant_id],
        best_percentage=max(result.percentage for result in history),
        attempts_count=len(history),
        latest_percentage=history[0].percentage,
    ) for participant_id, history in participant_attempts.items()]
    leaderboard.sort(key=lambda item: (-item.best_percentage, -item.latest_percentage, item.participant_name.lower()))
    percentages = [item.percentage for item in attempts]
    return TestAnalyticsResponse(
        test_id=test.id,
        title=test.title,
        total_attempts=len(attempts),
        unique_participants=len(participant_attempts),
        average_percentage=round(sum(percentages) / len(percentages)) if percentages else 0,
        best_percentage=max(percentages, default=0),
        attempts=attempts,
        leaderboard=leaderboard,
    )


@router.get("/public/tests/{public_token}", response_model=PublicTest)
async def get_public_test(
    public_token: str,
    db: AsyncSession = Depends(get_db),
) -> PublicTest:
    test = await db.scalar(select(Test).where(Test.public_token == public_token, Test.status == "published"))
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if test.expires_at and test.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Срок действия теста истёк")
    if test.privacy_mode != "public":
        raise HTTPException(status_code=403, detail="Тест доступен по другой privacy-настройке")

    owner = await db.get(User, test.owner_id)
    owner_profile = await db.scalar(select(Profile).where(Profile.user_id == test.owner_id))
    rows = await db.execute(
        select(TestQuestion, Question)
        .join(Question, Question.id == TestQuestion.question_id)
        .where(TestQuestion.test_id == test.id)
        .order_by(TestQuestion.position)
    )
    questions = [
        PublicQuestion(id=question.id, text=question.text, options=question.options, position=link.position, multiple=question.multiple_answers)
        for link, question in rows.all()
    ]
    return PublicTest(
        id=test.id,
        title=test.title,
        owner_name=(owner_profile.display_name if owner_profile else None) or (owner.first_name if owner else None) or "Друг",
        public_token=test.public_token,
        questions=questions,
    )


@router.post("/public/tests/{public_token}/sessions", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_test_session(
    public_token: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StartSessionResponse:
    test = await db.scalar(select(Test).where(Test.public_token == public_token, Test.status == "published"))
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if test.expires_at and test.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Срок действия теста истёк")
    if test.privacy_mode != "public":
        raise HTTPException(status_code=403, detail="Тест доступен по другой privacy-настройке")
    if test.max_attempts is not None:
        used_attempts = int((await db.execute(select(func.count(TestSession.id)).where(TestSession.test_id == test.id))).scalar_one())
        if used_attempts >= test.max_attempts:
            raise HTTPException(status_code=410, detail="Лимит прохождений исчерпан")
    count = len((await db.execute(select(TestQuestion.id).where(TestQuestion.test_id == test.id))).scalars().all())
    if count == 0:
        raise HTTPException(status_code=409, detail="В тесте нет вопросов")

    session = TestSession(
        id=uuid.uuid4(),
        test_id=test.id,
        participant_user_id=current_user.id,
        status="in_progress",
        current_position=0,
    )
    db.add(session)
    await db.commit()
    return StartSessionResponse(session_id=session.id, test_id=test.id, total_questions=count)


@router.post("/sessions/{session_id}/answers")
async def save_answer(
    session_id: uuid.UUID,
    request: AnswerRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    session = await db.get(TestSession, session_id)
    if session is None or session.participant_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Сессия уже завершена")

    question = await db.get(Question, request.question_id)
    link = await db.scalar(
        select(TestQuestion).where(
            TestQuestion.test_id == session.test_id,
            TestQuestion.question_id == request.question_id,
        )
    )
    if question is None or link is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    selected_options = request.selected_options
    if any(option not in question.options for option in selected_options):
        raise HTTPException(status_code=422, detail="Недопустимый вариант ответа")
    if not question.multiple_answers and len(selected_options) != 1:
        raise HTTPException(status_code=422, detail="Для этого вопроса выберите один вариант")

    answer = await db.scalar(
        select(SessionAnswer).where(
            SessionAnswer.session_id == session.id,
            SessionAnswer.question_id == question.id,
        )
    )
    if answer is None:
        db.add(SessionAnswer(session_id=session.id, question_id=question.id, selected_option=selected_options[0], selected_options=selected_options))
    else:
        answer.selected_option = selected_options[0]
        answer.selected_options = selected_options
    session.current_position = max(session.current_position, link.position + 1)
    await db.commit()
    return {"status": "saved"}


@router.post("/sessions/{session_id}/complete", response_model=ResultResponse)
async def complete_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ResultResponse:
    session = await db.get(TestSession, session_id, with_for_update=True)
    if session is None or session.participant_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    existing = await db.scalar(select(TestResult).where(TestResult.session_id == session.id))
    if existing is not None:
        return ResultResponse(
            result_id=existing.id,
            test_id=existing.test_id,
            correct_answers=existing.correct_answers,
            total_questions=existing.total_questions,
            percentage=existing.percentage,
        )
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Сессия уже завершена")

    links = list((await db.execute(select(TestQuestion).where(TestQuestion.test_id == session.test_id).order_by(TestQuestion.position))).scalars())
    answers = list((await db.execute(select(SessionAnswer).where(SessionAnswer.session_id == session.id))).scalars())
    answer_by_question = {answer.question_id: answer for answer in answers}
    if len(answer_by_question) != len(links) or any(link.question_id not in answer_by_question for link in links):
        raise HTTPException(status_code=409, detail="Ответьте на все вопросы перед завершением")

    questions = {question.id: question for question in (await db.execute(select(Question).where(Question.id.in_(list(answer_by_question))))).scalars()}
    def stored_options(answer: SessionAnswer) -> list[str]:
        return list(answer.selected_options or [answer.selected_option])

    def correct_options(question: Question) -> list[str]:
        return list(question.correct_options or [question.correct_option])

    correct = sum(set(stored_options(answer_by_question[link.question_id])) == set(correct_options(questions[link.question_id])) for link in links)
    total = len(links)
    percentage = round(correct * 100 / total)
    result = TestResult(
        id=uuid.uuid4(),
        session_id=session.id,
        test_id=session.test_id,
        owner_id=(await db.scalar(select(Test.owner_id).where(Test.id == session.test_id))),
        participant_user_id=current_user.id,
        correct_answers=correct,
        total_questions=total,
        percentage=percentage,
    )
    await award_xp(db, user_id=current_user.id, amount=25, completed_test=True)
    await record_event(db, event_name="test_completed", actor_user_id=current_user.id, test_id=session.test_id, event_metadata={"percentage": percentage})
    db.add(result)
    # ResultAnswer references test_results.result_id; flush the parent row before bulk child inserts.
    await db.flush()
    for link in links:
        question = questions[link.question_id]
        answer = answer_by_question[link.question_id]
        db.add(ResultAnswer(
            result_id=result.id,
            question_id=question.id,
            selected_option=answer.selected_option,
            correct_option=question.correct_option,
            selected_options=stored_options(answer),
            correct_options=correct_options(question),
            is_correct=set(stored_options(answer)) == set(correct_options(question)),
        ))
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return ResultResponse(
        result_id=result.id,
        test_id=result.test_id,
        correct_answers=result.correct_answers,
        total_questions=result.total_questions,
        percentage=result.percentage,
    )


@router.get("/results/{result_id}", response_model=ResultDetail)
async def get_result(
    result_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ResultDetail:
    result = await db.get(TestResult, result_id)
    if result is None or current_user.id not in {result.owner_id, result.participant_user_id}:
        raise HTTPException(status_code=404, detail="Результат не найден")
    review_locked = current_user.id != result.owner_id and not await user_has_entitlement(
        db,
        user_id=current_user.id,
        entitlement_key="premium_results",
    )
    rows = await db.execute(select(ResultAnswer).where(ResultAnswer.result_id == result.id).order_by(ResultAnswer.id))
    return ResultDetail(
        result_id=result.id,
        test_id=result.test_id,
        correct_answers=result.correct_answers,
        total_questions=result.total_questions,
        percentage=result.percentage,
        review_locked=review_locked,
        review=[] if review_locked else [ReviewItem(
            question_id=item.question_id,
            selected_option=item.selected_option,
            correct_option=item.correct_option,
            selected_options=list(item.selected_options or [item.selected_option]),
            correct_options=list(item.correct_options or [item.correct_option]),
            is_correct=item.is_correct,
        ) for item in rows.scalars()],
    )


@router.get("/statistics/me", response_model=StatisticsResponse)
async def get_my_statistics(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StatisticsResponse:
    tests_count = int((await db.execute(select(func.count(Test.id)).where(Test.owner_id == current_user.id))).scalar_one())
    attempts_count = int((await db.execute(select(func.count(TestResult.id)).where(TestResult.owner_id == current_user.id))).scalar_one())
    average = await db.scalar(select(func.avg(TestResult.percentage)).where(TestResult.owner_id == current_user.id))
    best = await db.scalar(select(func.max(TestResult.percentage)).where(TestResult.owner_id == current_user.id))
    return StatisticsResponse(
        tests_count=tests_count,
        attempts_count=attempts_count,
        average_percentage=round(float(average)) if average is not None else 0,
        best_percentage=int(best) if best is not None else None,
    )
