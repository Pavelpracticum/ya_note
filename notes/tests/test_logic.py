# тесты на unittest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note
# import assertFormError

from pytils.translit import slugify
from http import HTTPStatus

User = get_user_model()


class TestLogic(TestCase):
    """Тестирование логики."""

    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_SLUG = 'Novy-slug'
    # WARNING = как сюда импортировать WARNING из notes.forms
    WARNING = WARNING

    @classmethod
    def setUpTestData(cls):
        """Создаем фикстуры."""
        cls.user = User.objects.create(username='Авторизованный пользователь')
        cls.author = User.objects.create(username='Автор')
        # cls.auth_client = Client()

        title = 'Заголовок'
        text = 'Текст'
        slug = slugify(title)  # Генерируем slug на основе заголовка

        cls.note = Note.objects.create(
            title=title, text=text,
            author=cls.author, slug=slug)
        # Адрес страницы добавления заметки.
        cls.url = reverse('notes:add')
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {'title': cls.NOTE_TITLE, 'text': cls.NOTE_TEXT,
                         'slug': cls.NOTE_SLUG}

    # def setUp(self):
    #     """Каждый тест выполняется с чистым состоянием.

    #     Иначе ошибка в тесте def test_anonymous_user_cant_create_note.
    #     """
    #     # Очищаем заметки перед каждым тестом
    #     Note.objects.all().delete()

    def test_anonymous_user_cant_create_note(self):
        """
        Проверка.

        Анонимный пользователь не может создать заметку.
        """
        Note.objects.all().delete()
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        response = self.client.post(self.url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url}'
        # Проверяем, что произошла переадресация на страницу логина:
        self.assertRedirects(response, expected_url)
        # Считаем количество заметок в БД, ожидаем 0 заметок.
        self.assertEqual(Note.objects.count(), 0)

    def test_authenticated_user_can_create_note(self):
        """Проверка.

        Авторизованный пользователь может создать заметку.
        """
        Note.objects.all().delete()
        self.client.force_login(self.user)  # Логиним авторизованного

        # Создаем заметку
        response = self.client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с комментами.
        self.assertRedirects(response, reverse('notes:success'))

        # Проверяем, что заметка была создана
        self.assertEqual(Note.objects.count(), 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        Note.objects.all().delete()
        url = reverse('notes:add')

        # Создаем заметку, чтобы привести к конфликту
        self.note = Note.objects.create(
            title=self.NOTE_TITLE, text=self.NOTE_TEXT,
            author=self.author, slug=self.NOTE_SLUG)
        # Подменяем slug новой заметки на slug уже существующей записи:
        self.form_data['slug'] = self.note.slug

        self.client.force_login(self.author)  # Логиним автора
        # Пытаемся создать новую заметку:
        response = self.client.post(url, data=self.form_data)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + self.WARNING))
        # Убеждаемся, что количество заметок в базе осталось равным 1:
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Проверка.

        Если при создании заметки не заполнен slug,
        то он формируется автоматически,
        с помощью функции pytils.translit.slugify.
        """
        Note.objects.all().delete()
        url = reverse('notes:add')
        # Убираем поле slug из словаря:
        self.form_data.pop('slug')
        self.client.force_login(self.author)  # Логиним автора
        response = self.client.post(url, data=self.form_data)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор может редактировать свои заметки."""
        # Получаем адрес страницы редактирования заметки:
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.author)  # Логиним автора
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.client.post(url, self.form_data)
        # Проверяем редирект:
        self.assertRedirects(response, reverse('notes:success'))
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        self.note.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Не автор не может редактировать заметки."""
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.user)  # Логиним не автора
        response = self.client.post(url, self.form_data)
        # Проверяем, что страница не найдена:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем новый объект запросом из БД.
        note_from_db = Note.objects.get(id=self.note.pk)
        # Проверяем, атрибуты объекта из БД равны атрибутам заметки до запроса.
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Автор может удалять свои заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        self.client.force_login(self.author)  # Логиним автора
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Не автор не может редактировать заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        self.client.force_login(self.user)  # Логиним не автора
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
