from urllib.parse import urlparse
from collections.abc import Iterator
from typing import TYPE_CHECKING

from .utils import extract_text_from_html
from .discover import find_api_root, supports_wp_v2
from .data import fetch_wordpress_site_content
from .exceptions import WordPressAPIException

if TYPE_CHECKING:
    from langchain_text_splitters import TextSplitter
    import voyageai
    from pinecone import Index


def build_vector_database(
    site_url: str,
    splitter: "TextSplitter",
    embedder: "voyageai.Client",
    database: "Index",
) -> None:
    """
    Build vector database from WordPress site content.

    Args:
        site_url: URL of the form 'https://www.example.com/'.
        splitter: A text splitter for chunking.
        embedder: A text embedder to generate embeddings.
        database: The database object to upload the data.
    """
    api_root: str = find_api_root(site_url)
    if not supports_wp_v2(api_root):
        raise WordPressAPIException(
            "Site does not support core (wp/v2) endpoints."
        )
    site_contents: Iterator[dict[str, str]] = fetch_wordpress_site_content(api_root)

    EMBEDDING_BATCH_SIZE = 128
    site_domain = urlparse(site_url).hostname
    chunk_dicts: list[dict] = []
    for item in site_contents:
        item["content"] = extract_text_from_html(item["content"])
        # Extremely short comments are not helpful, hence removing them
        if len(item["content"]) <= 200:
            continue
        chunks = splitter.split_text(item["content"])
        chunk_dicts += _create_chunk_dicts(item, chunks)
        if len(chunk_dicts) < EMBEDDING_BATCH_SIZE:
            continue
        _embed_and_upload(chunk_dicts[:EMBEDDING_BATCH_SIZE],
                          embedder, database, site_domain)
        chunk_dicts = chunk_dicts[EMBEDDING_BATCH_SIZE:]
    if chunk_dicts:
        _embed_and_upload(chunk_dicts, embedder, database, site_domain)


def _create_chunk_dicts(item: dict[str, str], chunks: list[str]) -> list[dict]:
    chunk_dicts: list[dict] = []
    for i, chunk in enumerate(chunks):
        chunk_dict = item.copy()
        del chunk_dict["content"]
        chunk_dict["chunk_idx"] = i
        chunk_dict["chunk"] = chunk
        chunk_dicts.append(chunk_dict)
    return chunk_dicts


def _embed_and_upload(
    chunk_dicts: list[dict],
    embedder: "voyageai.Client",
    database: "Index",
    namespace: str,
) -> None:

    documents = _stack_chunks_to_embed(chunk_dicts)
    embeddings = embedder.embed(
        documents, model="voyage-large-2-instruct", input_type="document"
    ).embeddings
    data = _create_database_inputs(chunk_dicts, embeddings)
    database.upsert(data, namespace)


def _stack_chunks_to_embed(chunk_dicts: list[dict]) -> list:
    values = []
    for d in chunk_dicts:
        values.append(f"Title=[{d['title']}]\n{d['chunk']}")
    return values


def _create_database_inputs(
    chunk_dicts: list[dict],
    embeddings: list[list[float]],
) -> list[dict]:

    inputs: list[dict] = []
    for ckd, embedding in zip(chunk_dicts, embeddings):
        inputs.append({
            "id": f"{ckd['type']}s/{ckd['id']}#chunk{ckd['chunk_idx']}",
            "values": embedding,
            "metadata": {
                "title": ckd["title"],
                "link": ckd["link"],
                "text": ckd["chunk"],
            },
        })
    return inputs
