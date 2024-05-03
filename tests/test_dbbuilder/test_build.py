import re
import unittest as ut
from random import random

from httmock import HTTMock
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dbbuilder.build import build_vector_database
from tests.helpers import mock_wordpress_api


class TestBuildFunctions(ut.TestCase):

    def test_build_vector_database(self):
        site = "www.example.com"
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name = "gpt-3.5-turbo", chunk_size = 20, chunk_overlap = 4
        )
        embedder = MockEmbedder(1024)
        database = MockDatabase()
        with HTTMock(mock_wordpress_api):
            build_vector_database(f"https://{site}", splitter, embedder, database)

        self.assertEqual(database.namespace, site)
        is_present = {"page": False, "post": False, "comment": False}
        for v in database.vectors:
            id_pattern = r"(?:page)|(?:post)|(?:comment)s/\d+#chunk\d+$"
            self.assertTrue(re.match(id_pattern, v["id"]))
            self.assertEqual(len(v["values"]), embedder.embedding_size)
            self.assertIsInstance(v["values"][0], float)
            is_present[v["id"][:v["id"].index("/") - 1]] = True
            self.assertEqual(len(v["metadata"]), 3)
            for key in ["title", "link", "text"]:
                self.assertIn(key, v["metadata"])
                self.assertIsInstance(v["metadata"][key], str)
            self.assertNotIn("<", v["metadata"]["text"], "HTML tags not removed")

        self.assertTrue(all(is_present.values()))


class MockEmbedder:

    class Embeddings:
        pass

    def __init__(self, embedding_size: int):
        self.embedding_size = embedding_size

    def embed(self, texts, model, input_type) -> Embeddings:
        assert input_type in ["document", "query"], \
            "invalid 'input_type' for embedding."
        assert len(texts) <= 128, "Max batch size exceeded."

        output = MockEmbedder.Embeddings()
        output.embeddings = [[random() * 1000 for _ in range(self.embedding_size)]
                             for _ in range(len(texts))]
        return output


class MockDatabase:

    def __init__(self):
        self.vectors = []

    def upsert(self, vectors, namespace, batch_size = None, show_progress = True) -> None:
        self.vectors += vectors
        self.namespace = namespace
