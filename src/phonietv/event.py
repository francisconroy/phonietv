from dataclasses import dataclass


@dataclass
class PhonieTVEvent:
    eventType: str
    eventPayload: object
