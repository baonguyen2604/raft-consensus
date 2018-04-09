import asyncio

class Timer:
    """Scheduling periodic callbacks"""
    def __init__(self, interval, callback):
        self._interval = interval
        self._callback = callback
        self._loop = asyncio.get_event_loop()

        self._active = False

    def start(self):
        self._active = True
        self._handler = self._loop.call_later(self._interval, self._run)

    def _run(self):
        if self._active:
            self._callback()
            self._handler = self._loop.call_later(self._interval, self._run)

    def stop(self):
        self._active = False
        self._handler.cancel()

    def reset(self):
        self.stop()
        self.start()

    def get_interval(self):
        return self._interval() if callable(self._interval) else self._interval

