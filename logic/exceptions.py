class RetrieveException(Exception):
    def __init__(self, messaggio):
        super().__init__(messaggio)

class NoResultException(Exception):
    def __init__(self, word):
        super().__init__(f"Non ho trovato risultati nel DOP per la parola {word}")