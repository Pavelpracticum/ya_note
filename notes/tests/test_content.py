# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
# Импортируем класс комментария.
from notes.models import Note
from pytils.translit import slugify

# Получаем модель пользователя.
User = get_user_model()


class TestContent(TestCase):
    """Тестирование контента."""

    @classmethod
    def setUpTestData(cls):
        """Создаем фикстуры."""
        cls.user = User.objects.create(username='Авторизованный пользователь')
        cls.author = User.objects.create(username='Автор')
        # cls.note = Note.objects.create(
        #     title='Заголовок', text='Текст',
        #     author=cls.author)
        # cls.note.slug = slugify(cls.note.title)
        # cls.note.save()
        title = 'Заголовок'
        text = 'Текст'
        slug = slugify(title)  # Генерируем slug на основе заголовка

        cls.note = Note.objects.create(
            title=title, text=text,
            author=cls.author, slug=slug)

    def test_note_in_note_list(self):
        """
        Проверка.

        Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list, в словаре context.
        В список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        users_statuses = (
            (self.author, True),
            (self.user, False),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            with self.subTest(user=user):
                url = reverse('notes:list')
                # Запрашиваем страницу со списком заметок:
                response = self.client.get(url)
                # Получаем список объектов из контекста:
                object_list = response.context['object_list']
                if status:
                    self.assertIn(self.note, object_list)
                else:
                    self.assertNotIn(self.note, object_list)

    def test_note_form_in_add_edit_page(self):
        """
        Проверка.

        На страницы создания и редактирования заметки передаются формы.
        """
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        self.client.force_login(self.author)
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                # запросили страницу
                response = self.client.get(url)
                # Проверяем, есть ли объект формы в словаре контекста:
                self.assertIn('form', response.context)
                # Проверяем, что объект формы относится к нужному классу.
                self.assertIsInstance(response.context['form'], NoteForm)
