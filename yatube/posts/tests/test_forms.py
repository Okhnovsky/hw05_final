import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus
from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.comm_author = User.objects.create_user(
            username='comm_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image.name, 'posts/small.gif')
        self.assertEqual(post.group_id, form_data['group'])

    def test_edit_post(self):
        """Проверяем редактирование и сохранение поста"""
        self.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        form_data_edit = {
            'text': 'Отредактированный тестовый пост',
            'group': self.new_group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_one = Post.objects.first()
        self.assertEqual(post_one.text, form_data_edit['text'])
        self.assertEqual(post_one.group_id, form_data_edit['group'])
        self.assertEqual(PostFormTest.post.id, self.post.id)

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизированным клиентом."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста',
            author=self.user)
        form_data = {'text': 'Тестовый коментарий'}
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post_id, post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail', args={post.id}))

    def test_nonauthorized_user_create_comment(self):
        """Проверка создания комментария не авторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.user)
        form_data = {'text': 'Тестовый коментарий'}
        response = self.guest_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.id})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, redirect)
