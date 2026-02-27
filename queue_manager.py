
import asyncio
import time
import uuid

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

class QueueManager:
    def __init__(self, max_concurrent=2):
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue()
        self.active_tasks = {}
        self.waiting_tasks = []
        self._loop_task = None

    def start(self):
        if not self._loop_task:
            self._loop_task = asyncio.create_task(self._worker_loop())

    async def _worker_loop(self):
        while True:
            # We don't really use the queue to store the tasks themselves if we want to manage them easily
            # Instead we use it as a signal
            await asyncio.sleep(1)
            if len(self.active_tasks) < self.max_concurrent and self.waiting_tasks:
                task = self.waiting_tasks.pop(0)
                self.active_tasks[task.id] = task
                task.status = "Running"
                task.start_time = time.time()
                # Task execution is handled by the caller waiting on an event or similar
                # Or we can just let the caller proceed when it's their turn
                task.ready_event.set()

    async def add_task(self, user_id, chat_id, command, message):
        task = Task(user_id, chat_id, command, message)
        task.ready_event = asyncio.Event()
        self.waiting_tasks.append(task)
        return task

    def remove_task(self, task_id):
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        else:
            self.waiting_tasks = [t for t in self.waiting_tasks if t.id != task_id]

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
