import os
import unittest


# Create your tests here.
from resource_python.constants import birth, siling


class TestConstants(unittest.TestCase):

    def test_constants_exits(self):
        self.assertTrue(len(birth.keys()))
        self.assertTrue(len(siling.keys()))

    def test_constants_2018_birth_exits(self):
        list_2018 = []
        for one in birth.keys():
            if '2018' in one:
                list_2018.append(one)
        self.assertEqual(len(list_2018), 12)

    def test_constants_2019_birth_exits(self):
        list_2019 = []
        for one in birth.keys():
            if '2018' in one:
                list_2019.append(one)
        self.assertEqual(len(list_2019), 12)

    def test_constants_17_siling(self):
        self.assertEqual(list(siling.keys()), [str(one) for one in range(1, 18)])

    def test_constants_birth_context_argument(self):
        for one in birth.values():
            self.assertIn('亲爱的{Name}同学', one)
            self.assertIn('集团人力资源中心{Day}', one)

    def test_constants_siling_context_argument(self):
        for one in siling.values():
            self.assertIn('亲爱的{Name}同学', one)
            self.assertIn('集团人力资源中心{Day}', one)

class TestTemplates(unittest.TestCase):

    def test_email_templates_blessing(self):
        self.assertTrue(os.path.exists('templates/auto/blessing.html'))
        pass

    def test_email_templates_sms_receive(self):
        self.assertTrue(os.path.exists('templates/auto/sms_receive.html'))
        pass
    pass

# TODO 邮箱使用


if __name__ == '__main__':
    suite = unittest.TestSuite(unittest.TestLoader().discover(start_dir='.'))
