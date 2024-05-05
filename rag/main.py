from typing import TYPE_CHECKING

from mistral_common.tokens.instruct.normalize import ChatCompletionRequest
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistralai.models.chat_completion import ChatMessage

if TYPE_CHECKING:
    from mistralai.client import MistralClient
    from pinecone import Index
    import voyageai


class WordPressRAG:
    """
    An interface to perform Retrieval Augmented Generation on WordPress
    websites.
    """
    def __init__(
        self,
        site_domain: str,
        llm_client: "MistralClient",
        model_name: str,
        embedder: "voyageai.Client",
        vector_db: "Index"
    ):
        """
        Args:
            site_domain: Site's domain name. E.g. "www.example.com"
            llm_client: Client object to communicate with the LLM.
            model_name: Model name to be passed to the client.
            embedder: Model to generate text embeddings to query the database.
            vector_db: Vector database to serve as a knowledge base for the LLM.
        """
        self.site = site_domain
        self.client = llm_client
        self.model = model_name
        self.tokenizer = MistralTokenizer.v3()
        self.embedder = embedder
        self.db = vector_db

    def generate(
        self,
        chat_input: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        "Generate response from the chatbot."
        chat: list[ChatMessage] = []
        for msg in chat_input:
            chat.append(ChatMessage(**msg))

        if self.count_chat_tokens(chat[:-1]) > 1000:
            chat = self.summarize_chat(chat[:-1], 400) + [chat[-1]]

        retrieved_texts = self.retrieve_similar(chat[-1].content, 5)
        rag_msg = "You can use the following data to answer the user query:"
        for text in retrieved_texts:
            rag_msg += "\n\n-----\n\n" + text
        rag_msg = ChatMessage(role="system", content=rag_msg)
        chat = chat[:-1] + [rag_msg, self.add_cot_prompt(chat[-1])]
        res = self.client.chat(chat, self.model,
                               temperature=temperature,
                               safe_prompt=True)
        return res.choices[0].message.content

    def count_chat_tokens(self, chat: list[ChatMessage]) -> int:
        tokens, _ = self.tokenizer.encode_chat_completion(
            ChatCompletionRequest(model=self.model, messages=chat)
        )
        return len(tokens)

    def summarize_chat(
        self,
        chat: list[ChatMessage],
        summmary_length_words: int,
    ) -> list[ChatMessage]:

        if chat[0].role == "system":
            system_prompt = [chat[0]]
            chat = chat[1:]
        else:
            system_prompt = []

        s = summmary_length_words
        prompt = f"Summarize our conversation till now under {s} words. "
        prompt += "Keep any important pieces of information and user queries "
        prompt += "which may be necessary for future conversations."
        chat.append(ChatMessage(role="user", content=prompt))
        res = self.client.chat(chat, self.model, temperature=0.3)
        return system_prompt + [res.choices[0].message]

    @staticmethod
    def add_cot_prompt(msg: ChatMessage) -> ChatMessage:
        "Add text to the prompt to engage LLM in Zero-shot Chain of Thought."
        cot_prompt = "\nLet's think step by step."
        return ChatMessage(role=msg.role, content=msg.content + cot_prompt)

    def retrieve_similar(self, text: str, count: int) -> list[str]:
        "Retrieve semantically similar chunks of text from the vector database."
        embedding = self.embedder.embed(
            [text],
            model="voyage-large-2-instruct",
            input_type="query",
        ).embeddings[0]
        matches = self.db.query(namespace=self.site, vector=embedding,
                                top_k=count, include_metadata=True)["matches"]
        chunks: list[str] = []
        for match in matches:
            md = match["metadata"]
            chunks.append(f"{md['title']}, source: {md['link']}\n{md['text']}")
        return chunks
