from _types import NotificationDataType, NotificationTypes, StatusTypes

import requests
from dotenv import load_dotenv

load_dotenv()


class BaseNotification:
    LMS_LINK = '<a href="https://lyceum.yandex.ru">Проверяй LMS!</a>'

    def __init__(self, notification: NotificationDataType):
        self.id = notification['id']
        self.is_read = notification['isRead']
        self.type = notification['type']
        self.added_time = notification['addedTime']
        self.data = notification['objectData']

    def format(self, add_lms_link=True):
        """
        Форматирует уведомление для отправки сообщения
        """
        return f"<b>Тебе пришло новое уведомление!</b>\n\n\
{BaseNotification.LMS_LINK if add_lms_link else ''}"

    def __str__(self):
        return f"Notification {self.id}: {self.type}"

    def __repr__(self):
        return f"Notification {self.id}: {self.type}"


class BonusScoreNotification(BaseNotification):
    def __init__(self, notification: NotificationDataType):
        super(BonusScoreNotification, self).__init__(notification)

        self.new_score = int(self.data['newScore'])
        self.old_score = int(self.data['oldScore'])
        self.changed_by_name = self.data['changedBy']['displayName']

    def format(self):
        return f"<b>Ты получил бонусный балл!</b>\n\n\
{self.changed_by_name} поставил(-а) тебе {self.new_score - self.old_score} бонусных баллов!\n\
<b>Новый рейтинг</b>: {self.new_score} \n\n <a href='https://lyceum.yandex.ru'>Проверяй LMS!</a>"


class TaskCommentedNotification(BaseNotification):
    def __init__(self, notification: NotificationDataType):
        super(TaskCommentedNotification, self).__init__(notification)
        self.comment = self.data['data']
        self.author_display_name = self.data['author']['displayName']
        self.task = self.data['taskSolution']['task']
        self.task_title = self.task['title']

    def format(self):
        return f"<b>{self.author_display_name} прокомментировал задачу `{self.task_title}`</b>\n\n\
<i>{self.comment}</i>\n\n<a href='https://lyceum.yandex.ru'>Проверяй LMS!</a>"


class TaskAcceptedNotification(BaseNotification):
    def __init__(self, notification: NotificationDataType):
        super(TaskAcceptedNotification, self).__init__(notification)

        self.task = self.data['task']
        self.task_title = self.task['title']
        self.max_score = self.task['scoreMax']
        self.score = self.data['score']

    def format(self):
        return f"<b>Зачтена задача `{self.task_title}` !</b>\n\
<b>Баллы</b>: {self.score}/{self.max_score}\n\n<a href='https://lyceum.yandex.ru'>Проверяй LMS!</a>"


class TaskReworkNotification(BaseNotification):
    def __init__(self, notification: NotificationDataType):
        super(TaskReworkNotification, self).__init__(notification)

        self.task = self.data['task']
        self.task_title = self.task['title']

    def format(self):
        return f"<b>Задача `{self.task_title}` отправлена на доработку</b>\n\
<a href='https://lyceum.yandex.ru'>Проверяй LMS!</a>"


class YLNotifications:
    def __init__(self, login, password):
        self.sess = requests.session()
        self.auth(login, password)

    def auth(self, login, password):
        auth = self.sess.post('https://passport.yandex.ru/passport?mode=auth',
                              data={'login': login, 'passwd': password})
        if auth.url != 'https://passport.yandex.ru/profile':
            print(auth.url)
            print(auth.text)
            raise Exception(
                'Авторизация не удалась. Логин или пароль неправильные. (А может, возникает капча)')
        print('Авторизация прошла успешно')

    def get_all_notifications(self):
        req = self.sess.get(
            "https://lyceum.yandex.ru/api/notifications", params={'isRead': False})

        json_req = req.json()

        notifications: dict = json_req['notificationMap']
        messages = []

        for id, notification in notifications.items():
            match notification['type']:
                case NotificationTypes.NOTIFICATION_BONUS_SCORE_CHANGED:
                    message = BonusScoreNotification(notification).format()
                case NotificationTypes.NOTIFICATION_TASK_COMMENTED:
                    message = TaskCommentedNotification(notification).format()
                case NotificationTypes.NOTIFICATION_TASK_REVIEWED:

                    match notification['objectData']['status']['type']:
                        case StatusTypes.STATUS_ACCEPTED:
                            message = TaskAcceptedNotification(
                                notification).format()
                        case StatusTypes.STATUS_REWORK:
                            message = TaskReworkNotification(
                                notification).format()
                        case _:
                            message = BaseNotification(notification).format()

                case _:
                    message = BaseNotification(notification).format()

            messages.append(message)

        return messages

    def get_last_notification(self):
        return self.get_all_notifications()[-1]

    def read_notifications(self):
        """
        Прочитать уведомления
        """
        self.sess.patch('https://lyceum.yandex.ru/api/notifications/read', headers={
                        'Content-Type': 'application/json', 'X-CSRF-Token': self.sess.cookies['csrftoken']})
