from __future__ import annotations

import secrets
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
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
)
from app.db.session import get_db
from app.services.payments import user_has_entitlement

router = APIRouter(prefix="/api/v1", tags=["tests"])


class QuestionInput(BaseModel):
    text: str = Field(min_length=3, max_length=500)
    options: list[str] = Field(min_length=2, max_length=4)
    correct_option: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=64)


class CreateTestRequest(BaseModel):
    title: str = Field(default="Насколько ты меня знаешь?", min_length=3, max_length=128)
    questions: list[QuestionInput] = Field(min_length=3, max_length=15)


class TestSummary(BaseModel):
    id: uuid.UUID
    title: str
    public_token: str
    status: str
    question_count: int


class PublicQuestion(BaseModel):
    id: uuid.UUID
    text: str
    options: list[str]
    position: int


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
    selected_option: str = Field(min_length=1, max_length=255)


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
    is_correct: bool


class ResultDetail(ResultResponse):
    review_locked: bool
    review: list[ReviewItem]


class StatisticsResponse(BaseModel):
    tests_count: int
    attempts_count: int
    average_percentage: int
    best_percentage: int | None


def _new_public_token() -> str:
    return secrets.token_urlsafe(12).replace("-", "_").replace(".", "_")[:24]


@router.post("/tests", response_model=TestSummary, status_code=status.HTTP_201_CREATED)
async def create_test(
    request: CreateTestRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TestSummary:
    for item in request.questions:
        if len(set(item.options)) != len(item.options):
            raise HTTPException(status_code=422, detail="Варианты ответа не должны повторяться")
        if item.correct_option not in item.options:
            raise HTTPException(status_code=422, detail="Правильный ответ должен быть одним из вариантов")

    test = Test(
        id=uuid.uuid4(),
        owner_id=current_user.id,
        title=request.title,
        mode="know_me",
        public_token=_new_public_token(),
        status="published",
    )
    db.add(test)
    await db.flush()

    for position, item in enumerate(request.questions):
        question = Question(
            id=uuid.uuid4(),
            owner_id=current_user.id,
            text=item.text,
            options=item.options,
            correct_option=item.correct_option,
            category=item.category,
        )
        db.add(question)
        await db.flush()
        db.add(TestQuestion(test_id=test.id, question_id=question.id, position=position))

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
        response.append(TestSummary(id=test.id, title=test.title, public_token=test.public_token, status=test.status, question_count=count))
    return response


@router.get("/public/tests/{public_token}", response_model=PublicTest)
async def get_public_test(
    public_token: str,
    db: AsyncSession = Depends(get_db),
) -> PublicTest:
    test = await db.scalar(select(Test).where(Test.public_token == public_token, Test.status == "published"))
    if test is None:
        raise HTTPException(status_code=404, detail="Тест не найден")

    owner = await db.get(User, test.owner_id)
    rows = await db.execute(
        select(TestQuestion, Question)
        .join(Question, Question.id == TestQuestion.question_id)
        .where(TestQuestion.test_id == test.id)
        .order_by(TestQuestion.position)
    )
    questions = [
        PublicQuestion(id=question.id, text=question.text, options=question.options, position=link.position)
        for link, question in rows.all()
    ]
    return PublicTest(
        id=test.id,
        title=test.title,
        owner_name=owner.first_name if owner else "Друг",
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
    if request.selected_option not in question.options:
        raise HTTPException(status_code=422, detail="Недопустимый вариант ответа")

    answer = await db.scalar(
        select(SessionAnswer).where(
            SessionAnswer.session_id == session.id,
            SessionAnswer.question_id == question.id,
        )
    )
    if answer is None:
        db.add(SessionAnswer(session_id=session.id, question_id=question.id, selected_option=request.selected_option))
    else:
        answer.selected_option = request.selected_option
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
    correct = sum(questions[link.question_id].correct_option == answer_by_question[link.question_id].selected_option for link in links)
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
    db.add(result)
    for link in links:
        question = questions[link.question_id]
        answer = answer_by_question[link.question_id]
        db.add(ResultAnswer(
            result_id=result.id,
            question_id=question.id,
            selected_option=answer.selected_option,
            correct_option=question.correct_option,
            is_correct=answer.selected_option == question.correct_option,
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
