import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import sleep

import requests

logger = logging.getLogger(__file__)


@dataclass
class IndexerConfig:
    host: str = os.environ.get("INDEXER_API_HOST", "devtermgpu-a100.risc.local")
    port: str = os.environ.get("INDEXER_API_PORT", "8008")
    version: int = int(os.environ.get("INDEXER_API_VERSION", 1))


class IndexerClient:
    def __init__(self, config: IndexerConfig):
        self.config = config
        self.base_url = f"http://{self.config.host}:{self.config.port}/api/v{self.config.version}/indexing"

    def create_collection(
        self,
        collection_name: str,
        create: bool,
        document_path: str,
        timeout: int = 1800,
    ):
        """
        Adds a collection to the indexer.
        """
        api_url = f"{self.base_url}/create_collection"
        request_data = {
            "collection_name": collection_name,
            "create": create,
            "documents": document_path,
        }
        response = requests.post(api_url, json=request_data, timeout=timeout)
        return response.json()

    def add_to_collection(self, collection_name: str, document_path: str):
        """
        Adds a document to a collection.
        """
        api_url = f"{self.base_url}/add_to_collection"
        request_data = {"collection_name": collection_name, "documents": document_path}
        response = requests.post(api_url, json=request_data, timeout=500)
        return response.json()

    def remove_collection(self, collection_name: str, force: bool):
        """
        Remove a collection from the indexer service.
        """
        api_url = f"{self.base_url}/remove_collection"
        request_data = {"collection_name": collection_name, "force": force}
        response = requests.post(api_url, json=request_data, timeout=60)
        return response.json()

    def get_collection_metadata(self, collection_name: str):
        """
        Retrieve metadata for a specified collection from the indexing service.
        """
        api_url = f"{self.base_url}/get_collection_metadata"
        request_data = {"collection_name": collection_name}
        response = requests.post(api_url, json=request_data, timeout=60)
        return response.json()

    def get_collection_content(self, collection_name: str):
        """
        Fetches the content of a specified collection from the indexing service.
        """
        api_url = f"{self.base_url}/get_collection_content"
        request_data = {"collection_name": collection_name}
        response = requests.post(api_url, json=request_data, timeout=60)
        return response.json()

    def get_collection_content_astream(self, collection_name: str):
        """
        Fetches the content of a specified collection as a stream.
        """
        api_url = f"{self.base_url}/get_collection_content_astream"
        request_data = {"collection_name": collection_name}

        with requests.post(api_url, json=request_data, timeout=60, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                yield chunk.decode("utf-8")

    def list_collections(self):
        """
        List all collections from the indexer service.
        """
        api_url = f"{self.base_url}/list_collections"
        response = requests.post(api_url, timeout=60)
        return response.json()


class SSHFileHandler:
    def __init__(self, hostname: str, username: str, remote_folder: Path):
        self.hostname = hostname
        self.username = username
        self.remote_folder = remote_folder

    def connect(self):
        """Ensure the remote folder exists."""
        pass
        # subprocess.run([
        #     "ssh", f"{self.username}@{self.hostname}", f"mkdir -p {self.remote_folder}"
        # ], check=True)

    def copy_files(self, local_files: list[str]):
        """Copy files to the remote folder using scp."""
        for local_file in local_files:
            subprocess.run(
                ["scp", local_file, f"{self.hostname}:{self.remote_folder}/"],
                check=True,
            )

    def delete_files(self):
        """Delete all files in the remote folder."""
        subprocess.run(["ssh", f"{self.hostname}", f"rm -r {self.remote_folder}/*"], check=True)

    def disconnect(self):
        """Delete the remote folder."""
        pass


class QAndABundleClient:
    def __init__(
        self,
        indexer_client: IndexerClient,
        ssh_handler: SSHFileHandler,
        collection_name: str,
        local_files: list[str],
        remote_folder: str,
        qa_endpoint_url: str,
        delete_remote_folder: bool = True,
    ):
        self.indexer_client = indexer_client
        self.collection_name = collection_name
        self.delete_folder = delete_remote_folder
        self.remote_folder = remote_folder

        self.qa_endpoint_url = qa_endpoint_url

        self.ssh_handler = ssh_handler
        self.local_files = local_files

    def __enter__(self):
        self.ssh_handler.copy_files(self.local_files)
        self.indexer_client.create_collection(
            collection_name=self.collection_name,
            create=True,
            document_path=self.remote_folder,
        )
        self.indexer_client.add_to_collection(self.collection_name, self.remote_folder)
        sleep(1)
        return self

    def ask_questions(self, questions: list[str]):
        base_payload = {
            # "query": "What is the newest news?",
            "model": "mistral_7b",
            "collection_names": [self.collection_name],
            "memory_aware": False,
            "chat_history": [],
        }

        for question in questions:
            payload = base_payload.copy()
            payload["query"] = question
            # Send the POST request
            response = requests.post(self.qa_endpoint_url, json=payload, timeout=500)

            # Check the response
            if response.status_code == 200:
                # Response: {'response': '\nKoala: The newest news can be found in the News Datasphere, a dynamic network of interconnected tags (keywords) derived from millions of news articles produced daily. This network allows for the analysis of short-term trends and long-term connections, such as "ChatGPT" and "Natural Language Processing", or "Queen Elizabeth II" and "Begräbnis". The News Datasphere is part of the NEEED project, where data is further structured and utilized.', 'context': ['{"page_content": "Ein evolution\\u00e4rer Graph zum lokalen, nationalen und internationalen Nachrichtengeschehen. Im von der FFG gef\\u00f6rderten Forschungsprojekt NEEED (\\u201eNews-Extracted Evolving European Datasphere\\u201c) arbeiteten Forscher*innen und Entwickler*innen der RISC Software GmbH, SCCH GmbH und Newsadoo GmbH gemeinsam an der Weiterentwicklung der Plattform Newsadoo. Newsadoo sammelt, analysiert und sortiert Nachrichten aus lokalen, nationalen und internationalen Quellen vollautomatisch und erm\\u00f6glicht das personalisierte, themenspezifische und dezentrale Ausspielen von relevanten News. Bereits im Vorprojekt TIDE gelang es den Kooperationspartner*innen, Optimierungen an der automatischen Verarbeitung der Newsartikel sowie dem dahinterliegenden Empfehlungsalgorithmus zu erzielen. Mit NEEED konnte die Newsadoo-Technologie in die n\\u00e4chste Ausbaustufe gehoben werden, in der es nun m\\u00f6glich ist, die gesammelten Daten in Form eines Tag-Graphen (News Datasphere) weiter zu strukturieren und zu nutzen. Auf", "metadata": {"source": "/root/koala_data/raw_data/NEEED/neeed_demo_text.txt"}}', '{"page_content": "Mit \\u00fcber 30.000 produzierten Newsartikeln aus deutschen und englischen Newsquellen pro Tag wird die Data Sphere t\\u00e4glich um topaktuelle Themen erweitert. Mit mehreren Mio. Newsartikeln, aus denen \\u00fcber eine Million Tags hervorgehen, sto\\u00dfen herk\\u00f6mmliche Methoden zur Datenverarbeitung schnell an ihre Grenzen. Durch den Einsatz von Big Data-Technologien wird die Analyse des aktuellen Datenbestandes \\u00fcberhaupt erst m\\u00f6glich und kann durch den besonderen Fokus auf die Skalierbarkeit des Systems auch", "metadata": {"source": "/root/koala_data/raw_data/NEEED/neeed_demo_text.txt"}}', '{"page_content": "erm\\u00f6glicht das personalisierte, themenspezifische und dezentrale Ausspielen von relevanten News. Bereits im Vorprojekt TIDE gelang es den Kooperationspartner*innen, Optimierungen an der automatischen Verarbeitung der Newsartikel sowie dem dahinterliegenden Empfehlungsalgorithmus zu erzielen. Mit NEEED konnte die Newsadoo-Technologie in die n\\u00e4chste Ausbaustufe gehoben werden, in der es nun m\\u00f6glich ist, die gesammelten Daten in Form eines Tag-Graphen (News Datasphere) weiter zu strukturieren und", "metadata": {"source": "/root/koala_data/raw_data/NEEED/neeed_demo_text.txt"}}', '{"page_content": "Daten in Form eines Tag-Graphen (News Datasphere) weiter zu strukturieren und zu nutzen. Auf tagesaktueller Basis k\\u00f6nnen Informationen aus Newsartikel zu einem dynamischen Netzwerk an zusammenh\\u00e4ngenden Tags (Schlagworte) fusioniert und deren zeitliche Entwicklung weiterverfolgt werden. Damit k\\u00f6nnen sowohl langfristige Zusammenh\\u00e4nge (z.B. \\u201eRom\\u201c und \\u201eVatikan\\u201c) als auch kurzfristige Trends (z.B. \\u201eChatGPT\\u201c und \\u201eNatural Language Processing\\u201c, \\u201eQueen Elizabeth II\\u201c und \\u201eBegr\\u00e4bnis\\u201c) anhand des t\\u00e4glich produzierten, qualitativen News Contents abgeleitet und analysiert werden. Big Data in der Data Sphere: Analyse von Millionen an Newsartikeln", "metadata": {"source": "/root/koala_data/raw_data/NEEED/neeed_demo_text.txt"}}', '{"page_content": "und zu nutzen. Auf tagesaktueller Basis k\\u00f6nnen Informationen aus Newsartikel zu einem dynamischen Netzwerk an zusammenh\\u00e4ngenden Tags (Schlagworte) fusioniert und deren zeitliche Entwicklung weiterverfolgt werden. Damit k\\u00f6nnen sowohl langfristige Zusammenh\\u00e4nge (z.B. \\u201eRom\\u201c und \\u201eVatikan\\u201c) als auch kurzfristige Trends (z.B. \\u201eChatGPT\\u201c und \\u201eNatural Language Processing\\u201c, \\u201eQueen Elizabeth II\\u201c und \\u201eBegr\\u00e4bnis\\u201c) anhand des t\\u00e4glich produzierten, qualitativen News Contents abgeleitet und analysiert werden.", "metadata": {"source": "/root/koala_data/raw_data/NEEED/neeed_demo_text.txt"}}']}
                print("Response:", response.json()["response"])
            else:
                # log the response error
                logger.error(
                    f"Failed to get a valid response. Status Code: {response.status_code}. Text: {response.text}"
                )

    def __exit__(self, exc_type, exc_value, traceback):
        self.indexer_client.remove_collection(collection_name=self.collection_name, force=False)
        self.ssh_handler.delete_files()
        pass
