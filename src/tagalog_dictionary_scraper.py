import json
import logging
import traceback
from string import ascii_lowercase
from typing import Generator, Callable, Dict, List

from requests_html import HTMLSession, AsyncHTMLSession, HTML, Element

logging.basicConfig(level=logging.INFO)


class TagalogDictionaryScraper:
    """
    Scraper for the website https://tagalog.pinoydictionary.com
    """

    url = 'https://tagalog.pinoydictionary.com'
    letters = list(ascii_lowercase)
    # Parts of speech extracted from https://www.pinoydictionary.com/js/dictionary.js
    parts_of_speech = [
        'n.',
        'syn.',
        'bot.',
        'zoo.',
        'by ext.',
        'interrog.',
        'gram.',
        'idiom.',
        'prep.',
        'pref.',
        'pers.',
        'conj.',
        'med.',
        'mat.',
        'electr.',
        'mil.',
        'intrj.',
        'adv.',
        'pron.',
        'comp.',
        'adj.',
        'v.',
        'inf.',
        'pl.',
        'coll.',
        'fig.',
        'poss.',
        'anat.',
        'rel.',
        'pseudo-verb',
        'existential',
        # added parts of speech that was not included or parts of speech that they carelessly put
        'imp.',
        'expr.',
        'excl.',
        'adj',
        '[n]',
        'vinf.',
        'n',
        'v.,inf.',
        'n.,zoo.',
        'adj./adv.'
    ]

    # noinspection PyMethodMayBeStatic
    def print_words(self, words: Dict) -> None:
        """
        Puts words dictionary to JSON file.

        :type words: Dict
        :param words: Words Dictionary in the form of {'word': {'part_of_speech': [], definition: ''}
        :rtype: None
        :return: Nothing
        """
        with open('../words/tagalog-words.json', 'w') as f:
            json.dump(words, f, indent=4)

    # noinspection PyMethodMayBeStatic
    def _get_url_content(self, url: str) -> HTML:
        """
        Gets content of URL synchronously.

        :type url: str
        :param url: URL where to get the content
        :rtype: HTML
        :return: requests_html.HTML instance
        """
        session = HTMLSession()
        response = session.get(url)

        return response.html

    def scrape(self, async_scrape=False, max_urls=10, sort=False) -> Dict:
        """
        Start scraping here.
        TODO: Sort

        :type async_scrape: False
        :param async_scrape: True if scrape asynchronously, False otherwise
        :type max_urls: int
        :param max_urls: Max URL per getting of page contents to minimize process.
                         Used only when async is True
        :rtype: Dict
        :return: Dictionary in the form of {'word': {'part_of_speech': [], definition: ''}
        """
        words = {}

        for letter in self.letters:
            logging.info('Current Letter: {}'.format(letter))
            current_url = '{url}/list/{letter}'.format(
                url=self.url,
                letter=letter
            )
            response = self._get_url_content(current_url)

            # When an AttributeError occurred, that means that there is only 1 page for that letter
            try:
                last_page = response.find('a[title^=Last]', first=True).attrs['href']
                last_page = last_page.split('/')
                last_page = int(last_page[-2]) + 1
            except AttributeError:
                last_page = 2

            urls = self._get_all_urls_by_letter(letter, last_page)

            if async_scrape is False:
                htmls = self._get_pages_content(urls)
            else:
                htmls = self._get_pages_content_async(urls, max_urls=max_urls)

            words.update(self._get_words_info(htmls))

        return words

    def _get_all_urls_by_letter(self, letter: str, last_page: int) -> List:
        """
        Gets all URLs for a letter.

        :type letter:
        :param letter: Current letter
        :type last_page: int
        :param last_page: Last page for the current letter
        :rtype: list
        :rtype: List
        :return: List of URLs
        """
        urls = []

        for current_page in range(1, last_page):
            if current_page == 1:
                current_page = ''

            current_url = '{url}/list/{letter}/{current_page}/'.format(
                url=self.url,
                letter=letter,
                current_page=current_page
            )
            urls.append(current_url)

        return urls

    # noinspection PyBroadException
    def _get_pages_content(self, urls):
        contents = []

        for url in urls:
            try:
                logging.info('Current URL: {}'.format(url))
                contents.append(self._get_url_content(url))
            except Exception:
                logging.error('Failed in the URL: {}'.format(url))
                logging.error(traceback.format_exc())

                continue

        return [self._get_url_content(url) for url in urls]

    # noinspection PyMethodMayBeStatic
    def _get_pages_content_async(self, urls: list, max_urls: int = 10) -> List:
        """
        Gets page content asynchronously.

        :type urls: list
        :param urls: List of all URLs
        :type max_urls: int
        :param max_urls: Max URL per getting of page contents to minimize process.
        :rtype: list
        :return: List of Page Contents/HTML
        """
        def create_coroutines(url: str) -> Callable:
            """
            Creates async functions for Async get and render

            :type url: str
            :param url: URL to get and render
            :rtype: list
            :return: Async Function that gets a url and renders it
            """
            async def coroutine():
                response = await AsyncHTMLSession().get(url)

                return response

            return coroutine

        def chunk_list(l: list, n: int) -> Generator:
            """
            Yields successive n-sized chunks from a list.

            :type l: list
            :param l: List to be chunked
            :type n: int
            :param n: Size per chunk
            :rtype: Generator
            :return: Chunked list
            """
            for i in range(0, len(l), n):
                yield l[i:i + n]

        chunk_urls = chunk_list(urls, max_urls)
        all_results = []

        for chunk in chunk_urls:
            results = AsyncHTMLSession().run(*(create_coroutines(url) for url in chunk))
            all_results.extend([result.html for result in results])

        return all_results

    # noinspection PyMethodMayBeStatic
    def _get_parts_of_speech(self, parts_of_speech: Element) -> List[str]:
        """
        Gets the parts of speech of current word.
        Extracts the parts of speech from the definition because it is not properly stated.

        :type parts_of_speech: Element
        :param parts_of_speech: Element find inside div.definition p.
        :rtype: List[str]
        :return: List of Part of Speech Tags
        """
        indices_pos_mapping = {}

        for part_of_speech in self.parts_of_speech:
            index = parts_of_speech.text.find(part_of_speech)

            if index != -1:
                indices_pos_mapping[index] = part_of_speech

        # max_index means that this part of speech is the nearest to the definition
        max_index = max(indices_pos_mapping.keys())
        # remove it from the part of speech by index mapping for now to append it as the last part of speech
        last_part_of_speech = indices_pos_mapping.pop(max_index)
        parts_of_speech = [part_of_speech for part_of_speech in indices_pos_mapping.values()]
        parts_of_speech.append(last_part_of_speech)

        return parts_of_speech

    # noinspection PyMethodMayBeStatic
    def _get_definition(self, definition: Element, part_of_speech: str) -> str:
        """
        Gets the definition for the current word.
        The definition was split by the last part of speech because the structure of the definition is
        word part_of_speech definition
        So to get the definition, just split by part of speech then get the last element

        :type definition: Element
        :param definition: Element from .find
        :type part_of_speech: str
        :param part_of_speech: str where to split on
        :rtype: str
        :return: Word definition
        """
        return definition.text.split(part_of_speech)[-1].strip()

    def _get_words_info(self, htmls: List[HTML]) -> Dict:
        """
        Gets all words

        :type htmls: List[HTML]
        :param htmls: List of HTMLs
        :rtype: Dict
        :return: Dictionary in the form of {'word': {'part_of_speech': [], definition: ''}
        """
        words = {}

        for html in htmls:
            word_group = html.find('div.word-group')

            for group in word_group:
                word = group.find('a', first=True).text
                definition = group.find('div.definition p', first=True)
                parts_of_speech = self._get_parts_of_speech(definition)
                definition = self._get_definition(definition, parts_of_speech[-1])
                words[word] = {
                    'parts_of_speech': parts_of_speech,
                    'definition': definition
                }
                logging.info('Word: {} Part of Speech: {} Definition: {}'.format(
                    word,
                    parts_of_speech,
                    definition
                ))

        return words


if __name__ == '__main__':
    t = TagalogDictionaryScraper()
    w = t.scrape(async_scrape=True, max_urls=500)
    t.print_words(w)
