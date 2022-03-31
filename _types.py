from typing import TypedDict


class NotificationTypes:
    NOTIFICATION_TASK_REVIEWED = 'task-solution-reviewed'
    NOTIFICATION_TASK_COMMENTED = 'task-solution-commented'
    NOTIFICATION_BONUS_SCORE_CHANGED = 'bonus-score-changed'


class StatusTypes:
    STATUS_REWORK = 'rework'
    STATUS_ACCEPTED = 'accepted'


class NotificationDataType(TypedDict):
    id: int
    isRead: bool
    type: str
    addedTime: str
    objectData: dict