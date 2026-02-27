
import asyncio
import time
import uuid
import logging

logger = logging.getLogger(__name__)

class Task:
    def __init__(self, user_id, chat_id, command, message):
        self.id = str(uuid.uuid4())[:8]
        self.user_id = user_id
        self.chat_id = chat_id
        self.command = command
        self.message = message
        self.status = "Queued"
        self.start_time = None
        self.cancel_event = asyncio.Event()
        self.ready_event = asyncio.Event()

class QueueManager:
    def __init__(self, max_concurrent=2):
        self.max_concurrent = max_concurrent
        self.waiting_tasks = []
        self.active_tasks = {}
        self._loop_task = None
        self._signal_event = asyncio.Event()

    def start(self):
        if not self._loop_task:
            self._loop_task = asyncio.create_task(self._worker_loop())

    async def _worker_loop(self):
        logger.info("Queue manager worker loop started.")
        while True:
            try:
                # Wait until we have space and there are waiting tasks
                if len(self.active_tasks) >= self.max_concurrent or not self.waiting_tasks:
                    await self._signal_event.wait()
                    self._signal_event.clear()

                while len(self.active_tasks) < self.max_concurrent and self.waiting_tasks:
                    task = self.waiting_tasks.pop(0)
                    if task.cancel_event.is_set():
                        continue

                    self.active_tasks[task.id] = task
                    task.status = "Running"
                    task.start_time = time.time()
                    task.ready_event.set()
                    logger.info(f"Task {task.id} moved to running state.")

            except Exception as e:
                logger.error(f"Error in queue worker loop: {e}")
                await asyncio.sleep(1)

    async def add_task(self, user_id, chat_id, command, message):
        task = Task(user_id, chat_id, command, message)
        self.waiting_tasks.append(task)
        self._signal_event.set()
        return task

    def remove_task(self, task_id):
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        else:
            self.waiting_tasks = [t for t in self.waiting_tasks if t.id != task_id]
        self._signal_event.set()

    def cancel_task(self, task_id):
        task = self.active_tasks.get(task_id)
        if not task:
            for t in self.waiting_tasks:
                if t.id == task_id:
                    task = t
                    break
        if task:
            task.cancel_event.set()
            task.status = "Cancelled"
            # If it's active, it's already running, so we just set the cancel event.
            # If it's waiting, it will be skipped by the worker loop.
            self._signal_event.set()
            return True
        return False

    def get_queue_info(self):
        info = "**Active Tasks:**\n"
        if not self.active_tasks:
            info += "None\n"
        else:
            for tid, t in self.active_tasks.items():
                info += f"- `{tid}`: {t.command} (User: {t.user_id})\n"

        info += "\n**Queued Tasks:**\n"
        if not self.waiting_tasks:
            info += "None\n"
        else:
            for t in self.waiting_tasks:
                info += f"- `{t.id}`: {t.command} (User: {t.user_id})\n"
        return info

queue_manager = QueueManager(max_concurrent=2)
