import asyncio

import pytest

from app.background.runner import Job, JobRunner, JobStatus


@pytest.mark.anyio
async def test_enqueue_executes_job() -> None:
    runner = JobRunner()
    counter = {"count": 0}

    async def handler() -> None:
        counter["count"] += 1

    await runner.enqueue(Job(key="job-1", handler=handler, backoff_seconds=0))
    await asyncio.wait_for(runner.drain(), timeout=1)

    assert counter["count"] == 1
    assert runner.status_for("job-1") == JobStatus.SUCCEEDED
    await runner.stop()


@pytest.mark.anyio
async def test_retry_until_success() -> None:
    runner = JobRunner()
    counter = {"count": 0}

    async def handler() -> None:
        counter["count"] += 1
        if counter["count"] < 3:
            raise RuntimeError("fail")

    await runner.enqueue(
        Job(key="job-retry", handler=handler, max_attempts=3, backoff_seconds=0)
    )
    await asyncio.wait_for(runner.drain(), timeout=1)

    assert counter["count"] == 3
    assert runner.status_for("job-retry") == JobStatus.SUCCEEDED
    await runner.stop()


@pytest.mark.anyio
async def test_duplicate_enqueue_is_idempotent() -> None:
    runner = JobRunner()
    counter = {"count": 0}

    async def handler() -> None:
        counter["count"] += 1

    job = Job(key="job-dup", handler=handler, backoff_seconds=0)
    await runner.enqueue(job)
    await runner.enqueue(job)
    await asyncio.wait_for(runner.drain(), timeout=1)

    assert counter["count"] == 1
    assert runner.status_for("job-dup") == JobStatus.SUCCEEDED
    await runner.stop()
