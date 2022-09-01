from django.test import TestCase
from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_object_name_title(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_objects = {
            str(post): post.text,
            str(group): group.title
        }
        for field, expected_value in expected_objects.items():
            with self.subTest(field=field):
                self.assertEqual(expected_value, field)

    def test_object_name_title_post(self):
        task = PostModelTest.post
        expected_object_name = task.text[:15]
        self.assertEqual(expected_object_name, 'Тестовый пост')

    def test_verbose_name(self):
        task = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        task = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).help_text, expected)
