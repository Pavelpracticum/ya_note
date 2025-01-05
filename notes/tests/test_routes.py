from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """Создаем фикстуры."""
        cls.user = User.objects.create(username='Авторизованный пользователь')
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', author=cls.author)
        # Создаём двух пользователей с разными именами:
        # cls.user = User.objects.create(username='Авторизованный')
        # cls.reader = User.objects.create(username='Читатель простой')
        # От имени одного пользователя создаём комментарий к новости:
        # cls.comment = Comment.objects.create(
        #     news=cls.news,
        #     author=cls.author,
        #     text='Текст комментария'
        # )
        # произольное
        # def setUpTestData(cls):
        # # Создаём пользователя.
        # cls.user = User.objects.create(username='testUser')
        # # Создаём объект клиента.
        # cls.user_client = Client()
        # "Логинимся" в клиенте при помощи метода force_login().
        # cls.user_client.force_login(cls.user)
        # # Теперь через этот клиент можно отправлять запросы
        # от имени пользователя с логином "testUser".

    def test_pages_availability(self):
        """
        Проверка доступности страниц анонимному пользователю.

        Главной страницы, регистрации, логина, логаута.
        """
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            # Путь для главной страницы не принимает
            # никаких позиционных аргументов,
            # поэтому вторым параметром ставим None.
            ('notes:home', None),
            # Путь для страницы новости
            # принимает в качестве позиционного аргумента
            # id записи; передаём его в кортеже.
            # ('notes:detail', (self.notes.slug,)),
            # ('notes:list', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        # Итерируемся по внешнему кортежу
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_list_add_done(self):
        """
        Доступность страниц для авторизованного пользователя.

        Проверка страниц списка, добавления, успешного добавления заметки.
        """
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
        )
        users_statuses = (
            (self.user, HTTPStatus.OK),
            # (None, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            # if user:
            self.client.force_login(user)
            # else:
            #    pass
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name[0], args=name[1])
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_availability_for_note_detail_edit_and_delete(self):
        """
        Доступность страниц для автора.

        Проверка отдельной страницы, добавления, редактирования заметки.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.user, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:edit', 'notes:delete', 'notes:detail'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректов."""
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
        )
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in urls:
            with self.subTest(name=name):
                # Получаем адрес редактирования или удаления комментария:
                url = reverse(name[0], args=name[1])
                # Получаем ожидаемый адрес страницы логина,
                # на который будет перенаправлен пользователь.
                # Учитываем,в адресе будет параметр next, в котором передаётся
                # адрес страницы, с которой пользователь был переадресован.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
