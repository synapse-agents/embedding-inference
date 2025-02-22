"""
This module implements the Embedding class, which handles token counting,
embedding generation, and cosine similarity calculations.

It uses the tiktoken library for tokenization and embedding generation.
"""

import tiktoken
import numpy as np
from numpy import floating
from numpy._typing import _64Bit
from tiktoken import Encoding
from dotenv import load_dotenv
from typing import Any, List
from scipy.spatial import distance
from pydantic import Field, ConfigDict
from embedding.data_models import TokenUsage, BaseModule, EmbeddingRequest
from embedding.config import get_config, Config


load_dotenv()


encoding = tiktoken.get_encoding


class Embedding(BaseModule):
    config: Config = Field(default=get_config())
    token_usage: TokenUsage = Field(default=TokenUsage)
    historical_list: List[TokenUsage] = Field(default=list)
    embedding_function: Encoding = Field(default=encoding)
    __pydantic_fields_set__ = {"token_usage", "historical_list", "embedding_function", "config"}
    __pydantic_extra__ = {"allow_population_by_field_name": True}
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        __pydantic_extra__={"allow_population_by_field_name": True}
        )

    def __init__(self) -> None:
        """
        Initializes the TikTokenManager object with the provided keyword arguments.

        Parameters:
            **kwargs (dict): A dictionary of keyword arguments.
                - total (int): The total number of tokens.
                - response_tokens (int): The number of response tokens.
                - prompt_tokens (int): The number of prompt tokens.

        Returns:
            None
        """
        super().__init__()
        self.token_usage: TokenUsage = TokenUsage()
        self.historical_list: List[TokenUsage] = []
        self.embedding_function: Encoding = encoding("cl100k_base")

    def remove(self, index) -> TokenUsage:
        """
        Remove an element from the historical list at the specified index.

        Parameters:
            index (int): The index of the element to remove.

        Returns:
            str: A message indicating that the index has been removed.

        Raises:
            IndexError: If the index is out of range.

        Side Effects:
            - The element at the specified index is removed from the historical list.
            - If the index is 0, the session_total, prompt_tokens, request_tokens, response_tokens, and historical_list attributes are reset to 0 or an empty list.
        """
        self.historical_list.remove(self.historical_list[index])
        if index == 0:
            self.token_usage.total_tokens = 0
            self.token_usage.prompt_tokens = 0
            self.token_usage.request_tokens = 0
            self.token_usage.response_tokens = 0
            self.historical_list.append(TokenUsage(**self.token_usage.model_dump()))

        return self.token_usage

    def update(self, request: int, response: int) -> TokenUsage:
        """
        Updates the session total, prompt tokens, request tokens, and response tokens with the provided values.

        Parameters:
            total (int): The total number of tokens.
            request (int): The number of request tokens.
            response (int): The number of response tokens.

        Returns:
            str: A message indicating that the update was successful.
        """
        self.token_usage.request_tokens = request or 0
        self.token_usage.response_tokens = response or 0
        self.token_usage.prompt_tokens = self.token_usage.request_tokens + self.token_usage.response_tokens
        self.token_usage.total_tokens += self.token_usage.prompt_tokens
        self.historical_list.append(TokenUsage(**self.token_usage.model_dump()))
        return self.token_usage

    def count_tokens(self, string: str, encoding_name: str = "cl100k_base") -> int:
        """
        Counts the number of tokens in a given string using the specified encoding.

        Parameters:
            string (str): The input string to count the tokens of.
            encoding_name (str, optional): The name of the encoding to use. Defaults to "cl100k_base".

        Returns:
            int: The number of tokens in the input string.
        """
        embedding_array: tiktoken.Encoding = tiktoken.get_encoding(
            encoding_name=encoding_name
        )
        return len(embedding_array.encode(text=string))

    def cosine_similarity(
        self, embedding1: List[int], embedding2: List[int]
    ) -> floating[_64Bit | Any]:
        """
        Calculates the cosine similarity between two embeddings.

        Parameters:
            embedding1 (List[int]): The first embedding.
            embedding2 (List[int]): The second embedding.

        Returns:
            float: The cosine similarity between the two embeddings.
        """


        np_embedding1 = np.array(object=embedding1)
        np_embedding2 = np.array(object=embedding2)
        return 1 - distance.cosine(u=np_embedding1, v=np_embedding2)

    def process(self, embedding_request: EmbeddingRequest) -> List[int]:
        request_data = embedding_request.text
        embedding = self.embedding_function.encode(request_data)
        self.update(request=len(embedding), response=0)
        return embedding

# Create a closure to keep the embedding model in memory
def get_embedding_module():
    embedding_model = Embedding()
    
    def get_model():
        return embedding_model
    
    return get_model()
    
if __name__ == '__main__':
    module = get_embedding_module()
    print(module.process("hello world"))