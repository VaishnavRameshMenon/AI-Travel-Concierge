from collections import deque
from threading import Lock


class Metrics:
    def __init__(self):
        self._lock = Lock()

        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        self.total_generation_requests = 0
        self.successful_generation_requests = 0
        self.failed_generation_requests = 0

        self.request_durations = deque(maxlen=100)
        self.generation_durations = deque(maxlen=100)

    def record_request(self, duration: float, success: bool):
        with self._lock:
            self.total_requests += 1

            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            self.request_durations.append(duration)

    def record_generation(self, duration: float, success: bool):
        with self._lock:
            self.total_generation_requests += 1

            if success:
                self.successful_generation_requests += 1
            else:
                self.failed_generation_requests += 1

            self.generation_durations.append(duration)

    @staticmethod
    def _average(values):
        if not values:
            return 0.0

        return sum(values) / len(values)

    def snapshot(self):
        with self._lock:
            return {
                "requests": {
                    "total": self.total_requests,
                    "successful": self.successful_requests,
                    "failed": self.failed_requests,
                    "average_latency_seconds": round(
                        self._average(self.request_durations),
                        3,
                    ),
                },
                "trip_generation": {
                    "total": self.total_generation_requests,
                    "successful": self.successful_generation_requests,
                    "failed": self.failed_generation_requests,
                    "average_latency_seconds": round(
                        self._average(self.generation_durations),
                        3,
                    ),
                },
            }


# Global metrics instance used by FastAPI
metrics = Metrics()