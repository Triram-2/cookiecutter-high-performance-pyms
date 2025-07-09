import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
import main


@pytest.mark.asyncio
async def test_should_finish_tasks_on_shutdown() -> None:
    finished = asyncio.Event()

    async def fake_process(cfg, handler, event):
        await event.wait()
        finished.set()

    with (
        patch("main.process_tasks", side_effect=fake_process),
        patch("main.logger.info") as log_info,
    ):
        await main._start_processor()
        await asyncio.sleep(0)
        await main._stop_processor()
        log_info.assert_any_call("graceful shutdown")

    assert finished.is_set()
    assert main.app.state.processor_task.done()
