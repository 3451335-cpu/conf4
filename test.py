import unittest
import sys
import io
from main import Converter

class TestConverter(unittest.TestCase):
    def setUp(self):
        self.converter = Converter()

    def test_empty(self):
        data = "/* комментарий */"
        result = self.converter.parse_content(data)
        self.assertEqual(result, {})

    def test_simple_dict(self):
        data = """
            [
                name: q(John),
                age: 25.5
            ]
        """
        result = self.converter.parse_content(data)
        expected = {
            'name': 'John',
            'age': 25.5
        }
        self.assertEqual(result, expected)

    def test_array(self):
        data = """
            [
                numbers: { 1.5. 2.5. 3.5 },
                strings: { q(a). q(b). q(c) }
            ]
        """
        result = self.converter.parse_content(data)
        expected = {
            'numbers': [1.5, 2.5, 3.5],
            'strings': ['a', 'b', 'c']
        }
        self.assertEqual(result, expected)

    def test_nested_dict(self):
        data = """
            [
                user: [
                    name: q(Alice),
                    address: [
                        city: q(Moscow),
                        zip: 101000.0
                    ]
                ]
            ]
        """
        result = self.converter.parse_content(data)
        expected = {
            'user': {
                'name': 'Alice',
                'address': {
                    'city': 'Moscow',
                    'zip': 101000.0
                }
            }
        }
        self.assertEqual(result, expected)

    def test_constants(self):
        data = """
            var PORT 8080.0
            var HOST q(localhost)
            [
                server: [
                    host: $HOST$,
                    port: $PORT$
                ]
            ]
        """
        result = self.converter.parse_content(data)
        expected = {
            'server': {
                'host': 'localhost',
                'port': 8080.0
            }
        }
        self.assertEqual(result, expected)
        self.assertEqual(self.converter.transformer.consts['PORT'], 8080.0)
        self.assertEqual(self.converter.transformer.consts['HOST'], 'localhost')

    def test_mixed_structure(self):
        data = """
            var VERSION 2.0
            [
                app: [
                    name: q(MyApp),
                    version: $VERSION$,
                    modules: { q(auth). q(db). q(api) },
                    settings: [
                        timeout: 30.0
                    ]
                ]
            ]
        """
        result = self.converter.parse_content(data)
        expected = {
            'app': {
                'name': 'MyApp',
                'version': 2.0,
                'modules': ['auth', 'db', 'api'],
                'settings': {
                    'timeout': 30.0
                }
            }
        }
        self.assertEqual(result, expected)

    def test_undefined_constant(self):
        data = "[value: $UNDEFINED$]"
        with self.assertRaisesRegex(ValueError, "Константа 'UNDEFINED' не определена"):
            self.converter.parse_content(data)

    def test_syntax_error(self):
        data = "[key: 123"
        with self.assertRaisesRegex(ValueError, "Синтаксическая ошибка"):
            self.converter.parse_content(data)

    def test_invalid_number(self):
        data = "[value: 123]"
        with self.assertRaisesRegex(ValueError, "Синтаксическая ошибка"):
            self.converter.parse_content(data)

    def test_empty_array(self):
        data = "[arr: {}]"
        result = self.converter.parse_content(data)
        self.assertEqual(result['arr'], [])

    def test_empty_dict(self):
        data = "[empty: []]"
        result = self.converter.parse_content(data)
        self.assertEqual(result['empty'], {})

    def test_top_level_array(self):
        data = "{ q(item1). q(item2). q(item3) }"
        result = self.converter.parse_content(data)
        self.assertEqual(result, ["item1", "item2", "item3"])

    def test_top_level_array_with_dict(self):
        data = """
            var X 10.0
            { q(a). q(b) }
            [key: q(value)]
        """
        result = self.converter.parse_content(data)
        self.assertIn("arrays", result)
        self.assertEqual(result["arrays"], [["a", "b"]])
        self.assertEqual(result["key"], "value")

    def test_number_formats(self):
        data = """
            [
                positive: 123.45,
                negative: -67.89,
                with_plus: +10.5
            ]
        """
        result = self.converter.parse_content(data)
        expected = {
            'positive': 123.45,
            'negative': -67.89,
            'with_plus': 10.5
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    sys.stderr = io.StringIO()
    try:
        unittest.main(exit=False)
    finally:
        sys.stderr = sys.__stderr__
