# from parameterized import parameterized
# from rest_framework.test import APITestCase
#
# from .factories import PageFactory
# from ..models import Page
# from user.tests import factories
#
#
# class TestPage(APITestCase):
#     @classmethod
#     def setUpTestData(cls):
#         users = factories.UserFactory.create_batch(3)
#         u = users[0]
#         u2 = users[1]
#         u3 = users[2]
#
#         page1 = PageFactory.create(author=users[0], is_public=True, title="book_1")  # 1
#         pages1 = PageFactory.create_batch(3, parent=page1, author=users[0], is_public=True)  # 2 3 4
#
#         page2 = PageFactory.create(author=users[1], is_public=True, title="book_2")  # 5
#         pages2 = PageFactory.create_batch(2, parent=page2, author=users[1], is_public=True)  # 6 7
#         p1 = PageFactory.create(parent=page2, author=users[0], is_public=True)  # 8
#         p1 = PageFactory.create(parent=page2, author=users[2], is_public=False)  # 9
#         p1 = PageFactory.create(parent=p1, author=users[2], is_public=False)  # 10
#
#     @parameterized.expand([
#         ('', 200, [5, 6, 7, 8]),
#     ])
#     def test_reader_list(self, address, status, resp):
#         response = self.client.get("/page-reader-list/"+address, format='json')
#         assert response.status_code == status
#         assert len(response.data) == len(resp)
#         for r1, r2 in zip(response.data, resp):
#             assert r1['id'] == r2