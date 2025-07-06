import sys
import os

sys.path.append(os.path.abspath('c:/Users/pietr/.vscode/arte_comercial/01_PROCESOS/government_apis_integration.py'))


class GovernmentAPIManager:
    def __init__(self, config):
        self.config = config

class APICredentials:
    def __init__(self, key, token):
        self.key = key
        self.token = token