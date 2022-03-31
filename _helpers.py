from models.notification import Notification
from models.user import User


def join_notifications(notifications):
    return '\n\n'.join(notifications.values())


def get_notification_by_id(id, db_session):
    session = db_session.create_session()
    notification = session.query(Notification).get(id)
    session.close()
    return notification


def get_user_by_id(id, db_session):
    session = db_session.create_session()
    user = session.query(User).get(id)
    session.close()
    return user


def add_notifications_to_user(notification_ids, user_id, db_session):
    session = db_session.create_session()
    for notification_id in notification_ids:
        notification = Notification(id=int(notification_id), user_id=int(user_id))
        session.add(notification)
    session.commit()
    session.close()
    
