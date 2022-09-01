from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.public_urls_code = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            '/group/wrong_slug/': HTTPStatus.NOT_FOUND,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        self.private_urls_code = {
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse('posts:post_create'): HTTPStatus.OK,
        }
        self.author_urls_code = {
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
        }
        cache.clear()

    def test_guest_client_urls_status(self):
        """status_code для неавторизованного юзера."""
        for url, response in self.public_urls_code.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, response)

    def test_authorized_client_urls_status(self):
        """status_code для авторизованного юзера."""
        for url, response in self.private_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_client.get(url).status_code
                self.assertEqual(status_code, response)

    def test_post_author_urls_status(self):
        """status_code для автора."""
        for url, response in self.author_urls_code.items():
            with self.subTest(url=url):
                status_code = self.post_author.get(url).status_code
                self.assertEqual(status_code, response)

    def test_urls_correct_template(self):
        """URL соответствует шаблону."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.author}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
