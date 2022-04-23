import requests
from dotenv import load_dotenv

from _types import NotificationTypes, StatusTypes
from notifications import (BaseNotification, BonusScoreNotification, LessonOpenedNotification,
                           TaskAcceptedNotification, TaskCommentedNotification,
                           TaskReworkNotification)

load_dotenv()


class YLNotifications:
    def __init__(self, login, password):
        self.sess = requests.session()
        self.auth(login, password)

    def auth(self, login, password):
        auth = self.sess.post('https://passport.yandex.ru/passport?mode=auth',
                              data={'login': login, 'passwd': password})
        if auth.url != 'https://passport.yandex.ru/profile':
            print(auth.url)
            raise Exception(
                'Авторизация не удалась. Логин или пароль неправильные. (А может, возникает капча)')
        print('Авторизация прошла успешно')

    def get_all_notifications(self):
        req = self.sess.get(
            "https://lyceum.yandex.ru/api/notifications", params={'isRead': False})

        json_req = req.json()

        notifications: dict = json_req['notificationMap']
        messages = {}

        for id, notification in notifications.items():
            n_type = notification['type']
            if n_type == NotificationTypes.NOTIFICATION_BONUS_SCORE_CHANGED:
                message = BonusScoreNotification(notification).format()
            elif n_type == NotificationTypes.NOTIFICATION_LESSON_OPENED:
                message = LessonOpenedNotification(notification).format()
            elif n_type == NotificationTypes.NOTIFICATION_TASK_COMMENTED:
                message = TaskCommentedNotification(notification).format()
            elif n_type == NotificationTypes.NOTIFICATION_TASK_REVIEWED:
                status_type = notification['objectData']['status']['type']
                if status_type == StatusTypes.STATUS_ACCEPTED:
                    message = TaskAcceptedNotification(notification).format()
                elif status_type == StatusTypes.STATUS_REWORK:
                    message = TaskReworkNotification(notification).format()
                else:
                    message = BaseNotification(notification).format()
            else:
                message = BaseNotification(notification).format()

            messages[id] = message

        return messages

    def get_last_notification(self):
        return list(self.get_all_notifications().values())[-1]

    def read_notifications(self):
        """
        Прочитать уведомления
        """
        self.sess.patch('https://lyceum.yandex.ru/api/notifications/read', headers={
                        'Content-Type': 'application/json', 'X-CSRF-Token': self.sess.cookies['csrftoken']})
