import unittest
from collections import Counter
from io import StringIO
import sys
import os
from text_analyzer import TextProcessor, WordCounter, FileWordsFinder, InMemoryWordsFinder


class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()

    def test_process_text(self):
        text = "Hello, world! This is a test."
        expected = ['hello', 'world', 'this', 'is', 'a', 'test']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_mixed_case(self):
        text = "Hello, World! hello, WORLD!"
        expected = ['hello', 'world', 'hello', 'world']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_empty_text(self):
        text = ""
        expected = []
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_special_characters(self):
        text = "Hello, world! @2023 #Python"
        expected = ['hello', 'world', 'python']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_numbers(self):
        text = "Hello 123, world 456!"
        expected = ['hello', 'world']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_non_alpha(self):
        text = "Hello! @#$%^&*()"
        expected = ['hello']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_newlines(self):
        text = "Hello, world!\nThis is a test.\nNew line here."
        expected = ['hello', 'world', 'this', 'is', 'a', 'test', 'new', 'line', 'here']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_only_spaces(self):
        text = "     "
        expected = []
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_special_characters_only(self):
        text = "!@#$%^&*()"
        expected = []
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_unicode_characters(self):
        text = "Hello, мир! Привет, world!"
        expected = ['hello', 'мир', 'привет', 'world']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)

    def test_process_text_with_mixed_languages(self):
        text = "Hello, мир! Привет, world!"
        expected = ['hello', 'мир', 'привет', 'world']
        result = self.processor._process_text(text)
        self.assertEqual(result, expected)


class TestWordCounter(unittest.TestCase):
    def setUp(self):
        self.counter = WordCounter()

    def test_add_words(self):
        self.counter.add_words("file1.txt", ["hello", "world", "hello"])
        self.assertEqual(self.counter.get_all_words()["file1.txt"]["hello"], 2)
        self.assertEqual(self.counter.get_all_words()["file1.txt"]["world"], 1)

    def test_count_word_occurrences(self):
        self.counter.add_words("file1.txt", ["hello", "world", "hello"])
        occurrences = self.counter.count_word_occurrences("hello")
        self.assertEqual(occurrences, {"file1.txt": 2})

    def test_count_word_occurrences_nonexistent_word(self):
        occurrences = self.counter.count_word_occurrences("nonexistent")
        self.assertEqual(occurrences, {})

    def test_add_words_case_insensitive(self):
        self.counter.add_words("file1.txt", ["Hello", "world", "HELLO"])
        self.assertEqual(self.counter.get_all_words()["file1.txt"]["hello"], 2)
        self.assertEqual(self.counter.get_all_words()["file1.txt"]["world"], 1)

    def test_add_words_with_none(self):
        with self.assertRaises(TypeError):
            self.counter.add_words("file1.txt", None)

    def test_count_word_occurrences_empty(self):
        occurrences = self.counter.count_word_occurrences("")
        self.assertEqual(occurrences, {})

    def test_count_word_occurrences_in_empty_counter(self):
        occurrences = self.counter.count_word_occurrences("hello")
        self.assertEqual(occurrences, {})


    def test_add_duplicate_words(self):
        self.counter.add_words("file1.txt", ["hello", "world", "hello"])
        self.counter.add_words("file1.txt", ["hello"])
        self.assertEqual(self.counter.get_all_words()["file1.txt"]["hello"], 3)



class TestFileWordsFinder(unittest.TestCase):
    def setUp(self):
        # Создаем временный файл для тестирования
        self.test_file = 'test_file.txt'
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("Hello world! This is a test. Hello again.")

        self.finder = FileWordsFinder(self.test_file)

    def tearDown(self):
        # Удаляем временный файл после тестов
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_find_word(self):
        result = self.finder.find("hello")
        self.assertEqual(result, {self.test_file: 2})  # "Hello" встречается 2 раза

    def test_count_word_occurrences(self):
        result = self.finder.count_word_occurrences("test")
        self.assertEqual(result, {self.test_file: 1})  # "test" встречается 1 раз

    def test_filter_words(self):
        result = self.finder.filter_words(min_length=4)
        self.assertIn("hello", result[self.test_file])
        self.assertIn("world", result[self.test_file])
        self.assertNotIn("is", result[self.test_file])

    def test_find_word_in_empty_file(self):
        empty_file = 'empty_file.txt'
        with open(empty_file, 'w', encoding='utf-8') as f:
            f.write("")
        finder = FileWordsFinder(empty_file)
        result = finder.find("hello")
        self.assertEqual(result, {})
        os.remove(empty_file)

    def test_find_word_large_file(self):
        large_file = 'large_file.txt'
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write("hello " * 1000)  # 1000 раз "hello"
        finder = FileWordsFinder(large_file)
        result = finder.find("hello")
        self.assertEqual(result, {large_file: 1000})
        os.remove(large_file)

    def test_find_word_with_special_characters(self):
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("Hello, world! Hello again! @2023 #Python")
        result = self.finder.find("hello")
        self.assertEqual(result, {self.test_file: 2})

    def test_find_word_case_insensitive(self):
        result = self.finder.find("Hello")
        self.assertEqual(result, {self.test_file: 2})

    def test_find_word_in_nonexistent_file(self):
        finder = FileWordsFinder("nonexistent_file.txt")
        result = finder.find("hello")
        self.assertEqual(result, {})


    def test_find_word_in_file_with_only_special_characters(self):
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("!!! @@@ ###")
        result = self.finder.find("nonexistent")
        self.assertEqual(result, {})


    def test_find_word_in_large_file(self):
        large_file = 'large_file.txt'
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write("hello " * 10000)  # 10000 раз "hello"
        finder = FileWordsFinder(large_file)
        result = finder.find("hello")
        self.assertEqual(result, {large_file: 10000})
        os.remove(large_file)


if __name__ == '__main__':
    unittest.main()
