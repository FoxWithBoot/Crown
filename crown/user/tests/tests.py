from rest_framework.test import APITestCase
from parameterized import parameterized

from .factories import UserFactory
from ..models import User


class TestUser(APITestCase):
    url = '/user/'
    count = 3

    @classmethod
    def setUpTestData(cls):
        UserFactory.create_batch(3)

    @parameterized.expand([
        (None, None, 400, '{"username":["Это поле не может быть пустым."],'
                          '"password":["Это поле не может быть пустым."]}', 0),
        ('Margo', '', 400, '{"password":["Это поле не может быть пустым."]}', 0),
        ('', 'Ammonit', 400, '{"username":["Это поле не может быть пустым."]}', 0),
        ('[]', 'Ammonit', 400, '{"username":["Введите правильное имя пользователя. '
                               'Оно может содержать только буквы, цифры и знаки @/./+/-/_."]}', 0),
        ('Margo', 'A}mmoni@/-.t', 201, '', 1),
        ('Margo', 'Ammonit', 201, '', 1),
    ])
    def test_registration_user(self, username, password, status, resp, c):
        response = self.client.post(self.url,
                                    {'username': username, 'password': password},
                                    format='json')
        assert response.status_code == status
        assert response.content.decode('utf-8') == resp
        assert User.objects.count() == self.count + c

    @parameterized.expand([
        (None, None, 400, '{"username":["Это поле не может быть пустым."],'
                          '"password":["Это поле не может быть пустым."]}'),
        ('Margo', '', 400, '{"password":["Это поле не может быть пустым."]}'),
        ('', 'Ammonit', 400, '{"username":["Это поле не может быть пустым."]}'),
        ('[]', 'Ammonit', 401, '{"detail":"Не найдено активной учетной записи с указанными данными"}'),
        ('Margo', 'Ammonit', 401, '{"detail":"Не найдено активной учетной записи с указанными данными"}'),
        ('User1', '123', 200, ''),
        ('User1', '1234', 401, '{"detail":"Не найдено активной учетной записи с указанными данными"}')
    ])
    def test_login_user(self, username, password, status, resp):
        response = self.client.post(self.url + 'token/',
                                    {'username': username, 'password': password},
                                    format='json')
        assert response.status_code == status
        if status != 200:
            assert response.content.decode('utf-8') == resp
