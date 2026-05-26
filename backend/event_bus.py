from collections import deque

class IEventSubscriber:
    def handle(self, envelope):
        raise NotImplementedError("Every service must have a handle() method")

class EventBus:
    def __init__(self, max_queue=10000):
        self._subscribers = {}
        self._queue = deque(maxlen=max_queue)

    def subscribe(self, event_type, subscriber):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type, subscriber):
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(subscriber)

    def publish(self, envelope):
        self._queue.append(envelope)
        subscribers = self._subscribers.get(envelope.event_type, [])
        for sub in subscribers:
            sub.handle(envelope)

    def get_queue_size(self):
        return len(self._queue)