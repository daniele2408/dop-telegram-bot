import tempfile
import traceback
from typing import Dict, Optional, List, Tuple, Set

from bs4 import BeautifulSoup
from requests import post, get

from logic.exceptions import RetrieveException, NoResultException
from model.records import Lemma
from repository.phonetics import DICT_DOP_FONT_FAMILY


def post_url(url: str, body: Dict[str, str]) -> Optional[str]:

    try:
        response = post(url=url, data=body)
        if response.status_code == 200:
            return response.content.decode("utf-8")
        else:
            raise RuntimeError(f"Calling url {url} for a status code {response.status_code}")
    except Exception as e:
        print(f"Got some exception calling URL {url}: " + str(e))


def get_url(url: str) -> Optional[str]:

    try:
        response = get(url=url)
        if response.status_code == 200:
            return response.content.decode("utf-8")
        else:
            raise RuntimeError(f"Calling url {url} for a status code {response.status_code}")
    except Exception as e:
        print(f"Got some exception calling URL {url}: " + str(e))


def create_body_look_up(word: str) -> Dict[str, str]:
    return {"cerca": word}


def retrieve_page_look_for_word(word: str) -> str:
    return post_url("https://www.dizionario.rai.it/p.aspx?nID=cerca", create_body_look_up(word))


def extract_word_page_url(raw_html: str, word: str) -> str:
    soup = BeautifulSoup(raw_html, 'html.parser')
    hrefs_content = [tag['href'] for tag in soup.find_all(lambda x: x.name == "a" and x.text is not None and x.text.lower() == word)]
    param_dicts: List[Dict[str, str]] = [extract_parameters(content) for content in hrefs_content]

    lId: str = param_dicts.pop()['lID']

    return f"https://www.dizionario.rai.it/p.aspx?nID=lemma&lID={lId}"


def extract_word_page_url_multi(raw_html: str, word: str) -> List[str]:
    soup = BeautifulSoup(raw_html, 'html.parser')
    hrefs_content = [tag['href'] for tag in soup.find_all(lambda x: x.name == "a" and x.text is not None and x.text.lower() == word)]
    param_dicts: List[Dict[str, str]] = [extract_parameters(content) for content in hrefs_content]

    res: List[str] = list()

    if len(param_dicts) == 0:
        raise NoResultException(word)

    while len(param_dicts) != 0:
        lId: str = param_dicts.pop()['lID']
        res.append(f"https://www.dizionario.rai.it/p.aspx?nID=lemma&lID={lId}")

    return res


def extract_lemma_href(raw_html: str) -> Tuple[Optional[str], str]:
    soup = BeautifulSoup(raw_html, 'html.parser')
    href_lemma = soup.find('a', href=lambda x: x.startswith("Audio"))
    if href_lemma is not None:
        audio_url = href_lemma['href']
        lemma_word = href_lemma.text
        return audio_url, decode_dop_style(lemma_word)
    else:
        lemma_word = soup.find("div", class_="lemma-text").find("em").text
        return None, decode_dop_style(lemma_word)


def decode_dop_style(word: str) -> str:
    return "".join(DICT_DOP_FONT_FAMILY.get(c, c) for c in word)


def extract_parameters(param_string: str) -> Dict[str, str]:
    _, params = param_string.split('?')
    return {keyval.split("=")[0]:keyval.split("=")[1] for keyval in params.split("&")}


def download_audio_file(url: str):
    response = get(url)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(response.content)


def generate_lemma(word: str) -> Lemma:
    word = word.lower()
    try:
        txt = retrieve_page_look_for_word(word)
    except Exception as e:
        raise RetrieveException(f"Errore nel recuperare la landing page per la parola {word}: {str(e)}")
    try:
        page_word_url = extract_word_page_url(txt, word)
    except Exception as e:
        traceback.print_exc()
        raise RetrieveException(f"Errore nel recuperare l'url per la parola {word}.")
    try:
        page_word = get_url(page_word_url)
    except Exception as e:
        traceback.print_exc()
        raise RetrieveException(f"Errore nel recuperare la pagina per la parola {word} presso l'URL {page_word_url}")
    try:
        audio_url, lemma_word = extract_lemma_href(page_word)
    except Exception as e:
        traceback.print_exc()
        raise RetrieveException(f"Errore le informazioni per la parola {word} presso l'URL {page_word}")

    return Lemma.from_input(word, page_word_url, audio_url, lemma_word)


def generate_lemma_multi(word: str) -> Set[Lemma]:
    word = word.lower()
    try:
        txt = retrieve_page_look_for_word(word)
    except Exception as e:
        raise RetrieveException(f"Errore nel recuperare la landing page per la parola {word}: {str(e)}")
    try:
        page_word_urls: List[str] = extract_word_page_url_multi(txt, word)
    except NoResultException as nre:
        raise nre
    except Exception as e:
        traceback.print_exc()
        raise RetrieveException(f"Errore nel recuperare l'url per la parola {word}.")
    res: Set[Lemma] = set()
    for page_word_url in page_word_urls:
        try:
            page_word = get_url(page_word_url)
        except Exception as e:
            traceback.print_exc()
            raise RetrieveException(f"Errore nel recuperare la pagina per la parola {word} presso l'URL {page_word_url}")
        try:
            audio_url, lemma_word = extract_lemma_href(page_word)
        except Exception as e:
            traceback.print_exc()
            raise RetrieveException(f"Errore le informazioni per la parola {word} presso l'URL {page_word}")
        res.add(Lemma.from_input(word, page_word_url, audio_url, lemma_word))
    return res
