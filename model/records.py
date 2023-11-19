import tempfile
from dataclasses import dataclass
from typing import Optional

from requests import get

from repository.hosts import URL_DOP


@dataclass(eq=False, frozen=True)
class Lemma:
    word: str
    url: str
    audio_url: Optional[str]
    lemma_decoded: str

    def __eq__(self, __o):
        return isinstance(__o, Lemma) and self.lemma_decoded == __o.lemma_decoded

    def __hash__(self):
        return hash(self.lemma_decoded)

    def is_there_audio(self) -> bool:
        return self.audio_url is not None

    def download_audio(self) -> Optional[str]:
        if self.audio_url is None:
            return None
        response = get(self.audio_url)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            return temp_file.name

    def info(self) -> str:
        return f"📝 {self.word}\n\n📖 {self.url}\n\n💬 {self.lemma_decoded}"

    @staticmethod
    def from_input(word: str, url: str, audio_url: Optional[str], lemma_decoded: str):
        return Lemma(word, url, audio_url if audio_url is None else Lemma.add_to_host_dop(audio_url), lemma_decoded)

    @staticmethod
    def add_to_host_dop(path: str) -> str:
        return URL_DOP + ("" if path.startswith("/") else "/") + path
