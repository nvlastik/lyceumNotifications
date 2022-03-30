import requests
from pprint import pprint
import time
import datetime
from enum import IntEnum
import telegram


class Type(IntEnum):
    TASK_SOLUTION_REVIEWED = 1
    TASK_SOLUTION_COMMENTED = 2
    LESSON_OPENED = 3


class TypeStatusTask(IntEnum):
    REVIEW = 2
    REWORK = 3
    ACCEPTED = 4


class TypeLesson(IntEnum):
    NORMAL = 0


TypeTr = {'task-solution-reviewed': Type.TASK_SOLUTION_REVIEWED,
          'task-solution-commented': Type.TASK_SOLUTION_COMMENTED,
          'lesson-opened': Type.LESSON_OPENED}

TypeLessonTr = {'normal': TypeLesson.NORMAL}


class Lesson:
    def __init__(self, data):
        self.data = data
        self.id = data['id']
        self.isAccepted = data['isAccepted']
        self.shortTitle = data['shortTitle']
        self.title = data['title']
        self.type = TypeLesson(TypeLessonTr[data['type']])


class Task:
    def __init__(self, data):
        self.data = data
        self.id = data['id']
        self.course = data['course']
        self.group = data['group']
        self.lesson = Lesson(data['lesson'])
        self.scoreMax = data['scoreMax']
        self.shortTitle = data['shortTitle']
        self.title = data['title']


class Author:
    def __init__(self, data):
        self.data = data
        self.id = data['id']
        self.uid = data['uid']
        self.avatar = data['avatar']
        self.displayName = data['displayName']
        self.firstName = data['firstName']
        self.lastName = data['lastName']
        self.middleName = data['lastName']
        self.username = data['username']


class LessonOpen:
    def __init__(self, data):
        self.data = data
        self.course = data['course']
        self.group = data['group']
        self.lessonId = data['lessonId']
        self.shortTitle = data['shortTitle']
        self.title = data['title']
        self.type = TypeLesson(TypeLessonTr[data['type']])


class Event:
    def __init__(self, data):
        self.data = data
        self.type = Type(TypeTr[data['type']])
        self.id = data['id']
        self.isRead = data['isRead']
        self.time = datetime.datetime.strptime(data['addedTime'], '%Y-%m-%dT%H:%M:%S.%f+03:00')

        if self.type == Type.LESSON_OPENED:
            self._parse_opened_lesson()
        elif self.type == Type.TASK_SOLUTION_REVIEWED:
            self._parse_solution()
        elif self.type == Type.TASK_SOLUTION_COMMENTED:
            self._parse_solution_comment()

    def __str__(self):
        if self.type == Type.LESSON_OPENED:
            return f'Открыт урок "{self.lesson.title}"'
        elif self.type == Type.TASK_SOLUTION_REVIEWED:
            return f'Изменился статус задачи "{self.task.title}": {self.score}/{self.task.scoreMax}'
        elif self.type == Type.TASK_SOLUTION_COMMENTED:
            return f'Прокомментировали задачу "{self.task.title}": {self.commentText}'

    def _parse_solution(self):
        od = self.data['objectData']
        self.score = od['score']
        self.solutionId = od['taskSolutionId']
        self.status = TypeStatusTask(od['status']['id'])
        self.task = Task(od['task'])

    def _parse_solution_comment(self):
        od = self.data['objectData']
        self.commentId = od['commentId']
        self.commentText = od['data']
        self.solutionId = od['taskSolution']['id']
        self.task = Task(od['taskSolution']['task'])

    def _parse_opened_lesson(self):
        self.lesson = LessonOpen(self.data['objectData'])


class YLNotifications:
    def __init__(self, login, password):
        self.sess = requests.session()
        self.auth(login, password)

    def auth(self, login, password):
        auth = self.sess.post('https://passport.yandex.ru/passport?mode=auth', data={'login': login, 'passwd': password})
        if auth.url != 'https://passport.yandex.ru/profile':
            print(auth.url)
            print(auth.text)
            raise Exception('Авторизация не удалась. Логин или пароль неправильные. (А может, возникает капча)')
        print('Авторизация прошла успешно')

    def run(self):
        while True:
            for event in self.get_notifications():
                yield event
            self.read_notifications()
            print(datetime.datetime.now())
            time.sleep(15)

    def get_notifications(self):  # получить уведомления
        r = self.sess.get("https://lyceum.yandex.ru/api/notifications", params={'isRead': False})
        j = r.json()
        pprint(j)
        return [Event(j['notificationMap'][e]) for e in j['notificationMap'] if j['notificationMap'][e]['type'] in TypeTr]

    def read_notifications(self):  # сделать уведомления прочитанными
        self.sess.patch("https://lyceum.yandex.ru/api/notifications/read", headers={"Content-Type": "application/json", 'X-CSRF-Token': self.sess.cookies['csrftoken']})


bot = telegram.Bot('')  # токен Telegram
n = YLNotifications('nvlastik', 'tutmoyparol')  # логин, пароль от Яндекса

while True:
    try:
        for i in n.run():
            print(i)
            bot.sendMessage(chat_id=1234567890, text=str(i))  # отсылка сообщения
    except BaseException as er:
        print(er)