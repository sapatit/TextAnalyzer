import string
import logging
from collections import Counter
import argparse
from typing import List, Dict, Optional, Tuple, Any
from functools import lru_cache
from abc import ABC, abstractmethod


# Настройка логирования
def setup_logging(log_level: int) -> None:
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')


class TextProcessor:
    @lru_cache(maxsize=None)  # Кэширование результатов обработки текста
    def _process_text(self, text: str) -> List[str]:
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation.replace('-', '')))
        return text.split()


class WordCounter:
    def __init__(self) -> None:
        self.all_words: Dict[str, Counter] = {}

    def add_words(self, file_name: str, words: List[str]) -> None:
        if file_name not in self.all_words:
            self.all_words[file_name] = Counter()
        self.all_words[file_name].update(words)

    def get_all_words(self) -> Dict[str, Counter]:
        return self.all_words

    def count_word_occurrences(self, word: str) -> Dict[str, int]:
        word = word.lower()
        result: Dict[str, int] = {}
        for file_name, counter in self.all_words.items():
            count = counter[word]
            if count > 0:
                result[file_name] = count
        return result


class BaseWordsFinder(ABC):
    @abstractmethod
    def find(self, word: str) -> Dict[str, int]:
        pass

    @abstractmethod
    def count_word_occurrences(self, word: str) -> Dict[str, int]:
        pass

    @abstractmethod
    def count_all_words(self) -> Dict[str, Counter]:
        pass

    @abstractmethod
    def filter_words(self, min_length: int = 0, starts_with: Optional[str] = None) -> Dict[str, List[str]]:
        pass


class FileWordsFinder(BaseWordsFinder):
    def __init__(self, *file_names: str, encoding: str = 'utf-8') -> None:
        self.file_names: Tuple[str, ...] = file_names
        self.encoding: str = encoding
        self.text_processor: TextProcessor = TextProcessor()
        self.word_counter: WordCounter = WordCounter()
        self.get_all_words()

    def get_all_words(self) -> None:
        for file_name in self.file_names:
            try:
                with open(file_name, 'r', encoding=self.encoding) as file:
                    text = file.read()
                    words = self.text_processor._process_text(text)
                    self.word_counter.add_words(file_name, words)
            except FileNotFoundError:
                self.handle_error(file_name, "Файл не найден.")
            except UnicodeDecodeError:
                self.handle_error(file_name, "Ошибка декодирования.")
            except Exception as e:
                self.handle_error(file_name, str(e))

    def find(self, word: str) -> Dict[str, int]:
        return self.word_counter.count_word_occurrences(word)

    def count_word_occurrences(self, word: str) -> Dict[str, int]:
        return self.word_counter.count_word_occurrences(word)

    def count_all_words(self) -> Dict[str, Counter]:
        return self.word_counter.get_all_words()

    def filter_words(self, min_length: int = 0, starts_with: Optional[str] = None) -> Dict[str, List[str]]:
        filtered_words: Dict[str, List[str]] = {}
        for file_name, counter in self.word_counter.get_all_words().items():
            filtered_words[file_name] = [word for word in counter if len(word) >= min_length and
                                         (starts_with is None or word.startswith(starts_with))]
        return filtered_words

    def sort_results(self, all_word_counts: Dict[str, Counter], sort_by: str) -> Dict[str, Counter]:
        if sort_by == 'frequency':
            return {k: v for k, v in
                    sorted(all_word_counts.items(), key=lambda item: sum(item[1].values()), reverse=True)}
        elif sort_by == 'alphabetical':
            return dict(sorted(all_word_counts.items()))
        return all_word_counts

    def save_results(self, all_word_counts: Dict[str, Counter], output_file: str, format: str) -> None:
        with open(output_file, 'w', encoding='utf-8') as f:
            if format == 'json':
                import json
                json.dump(all_word_counts, f, ensure_ascii=False, indent=4)
            else:
                for file_name, counter in all_word_counts.items():
                    f.write(f"{file_name}:\n")
                    for word, count in counter.items():
                        f.write(f"{word}: {count}\n")
                    f.write("\n")

    def handle_error(self, file_name: str, error_message: str) -> None:
        logging.error(f"Ошибка при обработке файла {file_name}: {error_message}")


class InMemoryWordsFinder(BaseWordsFinder):
    def __init__(self, text: str) -> None:
        self.text_processor: TextProcessor = TextProcessor()
        self.word_counter: WordCounter = WordCounter()
        self.process_text(text)

    def process_text(self, text: str) -> None:
        words = self.text_processor._process_text(text)
        self.word_counter.add_words("in_memory_text", words)

    def find(self, word: str) -> Dict[str, int]:
        return self.word_counter.count_word_occurrences(word)

    def count_word_occurrences(self, word: str) -> Dict[str, int]:
        return self.word_counter.count_word_occurrences(word)

    def count_all_words(self) -> Dict[str, Counter]:
        return self.word_counter.get_all_words()

    def filter_words(self, min_length: int = 0, starts_with: Optional[str] = None) -> Dict[str, List[str]]:
        filtered_words: Dict[str, List[str]] = {}
        filtered_words["in_memory_text"] = [word for word in
                                            self.word_counter.get_all_words().get("in_memory_text", Counter())
                                            if len(word) >= min_length and
                                            (starts_with is None or word.startswith(starts_with))]
        return filtered_words

    def sort_results(self, all_word_counts: Dict[str, Counter], sort_by: str) -> Dict[str, Counter]:
        if sort_by == 'frequency':
            return {k: v for k, v in
                    sorted(all_word_counts.items(), key=lambda item: sum(item[1].values()), reverse=True)}
        elif sort_by == 'alphabetical':
            return dict(sorted(all_word_counts.items()))
        return all_word_counts

    def save_results(self, all_word_counts: Dict[str, Counter], output_file: str, format: str) -> None:
        with open(output_file, 'w', encoding='utf-8') as f:
            if format == 'json':
                import json
                json.dump(all_word_counts, f, ensure_ascii=False, indent=4)
            else:
                for file_name, counter in all_word_counts.items():
                    f.write(f"{file_name}:\n")
                    for word, count in counter.items():
                        f.write(f"{word}: {count}\n")
                    f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description='Поиск и анализ слов в текстовых файлах.')
    parser.add_argument('files', nargs='*',
                        help='Список файлов для обработки (можно оставить пустым для обработки текста в памяти)')
    parser.add_argument('--text', help='Текст для обработки в памяти')
    parser.add_argument('--encoding', default='utf-8', help='Кодировка файлов (по умолчанию utf-8)')
    parser.add_argument('--word', help='Слово для поиска')
    parser.add_argument('--count', help='Слово для подсчета вхождений')
    parser.add_argument('--filter', nargs=2, metavar=('MIN_LENGTH', 'STARTS_WITH'),
                        help='Фильтрация слов по длине и начальной букве')
    parser.add_argument('--output', help='Файл для сохранения результатов')
    parser.add_argument('--log-level', default='ERROR',
                        help='Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--sort', choices=['frequency', 'alphabetical'], help='Сортировка результатов по критериям')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Формат сохранения результатов')

    args = parser.parse_args()

    # Настройка уровня логирования
    log_level = getattr(logging, args.log_level.upper(), logging.ERROR)
    setup_logging(log_level)

    if not args.files and not args.text:
        parser.error("Необходимо указать хотя бы один файл для обработки или текст для обработки в памяти.")

    if args.files:
        finder = FileWordsFinder(*args.files, encoding=args.encoding)
    elif args.text:
        finder = InMemoryWordsFinder(args.text)

    if args.word:
        found_word = finder.find(args.word)
        print(f"Результаты поиска слова '{args.word}':")
        print(found_word)

    if args.count:
        counted_word = finder.count_word_occurrences(args.count)
        print(f"Количество вхождений слова '{args.count}':")
        print(counted_word)

    if args.filter:
        try:
            min_length = int(args.filter[0])
            starts_with = args.filter[1] if len(args.filter) > 1 else None
            filtered_words = finder.filter_words(min_length=min_length, starts_with=starts_with)
            print(f"Отфильтрованные слова (длина >= {min_length} и начинаются на '{starts_with}'): ")
            print(filtered_words)
        except ValueError:
            print("Ошибка: MIN_LENGTH должно быть целым числом.")

    if args.output:
        all_word_counts = finder.count_all_words()

        if args.sort:
            all_word_counts = finder.sort_results(all_word_counts, args.sort)

        finder.save_results(all_word_counts, args.output, format=args.format)
        print(f"Результаты подсчета сохранены в файл: {args.output}")


if __name__ == '__main__':
    main()
