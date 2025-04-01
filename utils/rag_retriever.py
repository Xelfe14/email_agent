import os
from typing import List, Dict, Any, Tuple
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document

class RAGRetriever:
    """
    Retrieval-Augmented Generation (RAG) for finding similar email-response pairs
    and generating style-matched draft responses.
    """

    def __init__(self, api_key: str, vectorstore_path: str = None):
        """
        Initialize the RAG retriever.

        Args:
            api_key: OpenAI API key
            vectorstore_path: Path to save/load the vectorstore
        """
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            api_key=api_key
        )
        self.vectorstore_path = vectorstore_path
        self.vectorstore = None

        # Create or load vector store
        if vectorstore_path:
            try:
                if os.path.exists(os.path.join(vectorstore_path, "chroma")):
                    self.vectorstore = Chroma(
                        persist_directory=vectorstore_path,
                        embedding_function=self.embeddings
                    )
            except Exception as e:
                print(f"Warning: Could not load vectorstore: {e}")
                print("A new vectorstore will be created when data is ingested.")

        self.style_prompt = ChatPromptTemplate.from_template("""
        You are a professional investment fund email writer. Your task is to generate a draft response based on the style, tone, and structure of similar past responses, but adapted for the new inquiry.

        New inquiry to respond to:
        {new_email}

        Extracted information about the inquiry:
        {extracted_info}

        Similar historical email-response pair examples:
        {similar_examples}

        Based on the style and tone of these historical responses, draft a partial response to the new inquiry. Focus on matching the writing style, tone, greeting style, sign-off style, and overall structure.

        The draft should be well-structured but incomplete, as we will add specific details about the company later.
        """)

    def ingest_email_data(self, emails_df: pd.DataFrame) -> None:
        """
        Ingest email-response pairs into the vector store.

        Args:
            emails_df: DataFrame with columns 'email_text', 'response_text', and metadata columns
        """
        documents = []

        for idx, row in emails_df.iterrows():
            # Create a combined document with both email and response
            combined_text = f"EMAIL: {row['email_text']}\n\nRESPONSE: {row['response_text']}"

            # Extract metadata fields
            metadata = {col: row[col] for col in emails_df.columns
                       if col not in ['email_text', 'response_text']}
            metadata['id'] = idx

            doc = Document(page_content=combined_text, metadata=metadata)
            documents.append(doc)

        # Create or update vectorstore
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.vectorstore_path if self.vectorstore_path else None
            )
        else:
            self.vectorstore.add_documents(documents)

        # Save if path provided
        if self.vectorstore_path:
            self.vectorstore.persist()

    def retrieve_similar_examples(self, query_email: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve similar email-response pairs from the vector store.

        Args:
            query_email: The email text to find similar examples for
            k: Number of examples to retrieve

        Returns:
            List of similar email-response pairs with metadata
        """
        if self.vectorstore is None:
            return []

        results = self.vectorstore.similarity_search(query_email, k=k)

        similar_pairs = []
        for doc in results:
            # Split into email and response
            parts = doc.page_content.split("\n\nRESPONSE: ")
            if len(parts) == 2:
                email = parts[0].replace("EMAIL: ", "")
                response = parts[1]

                similar_pairs.append({
                    "email": email,
                    "response": response,
                    "metadata": doc.metadata
                })

        return similar_pairs

    def generate_style_based_draft(self,
                                  query_email: str,
                                  extracted_info: Dict[str, Any],) -> str:
        """
        Generate a draft response based on similar historical responses' style.

        Args:
            query_email: The new email to respond to
            extracted_info: Extracted structured information from the email
            similar_examples: Similar email-response pairs from the vector store
            style_prompt: Prompt for style-based generation
        Returns:
            Draft response based on historical style
        """
        # Retrieve similar examples
        similar_pairs = self.retrieve_similar_examples(query_email)

        if not similar_pairs:
            # If no similar examples found, return basic template
            return "Thank you for reaching out to us. We appreciate your interest in our fund."

        # Format similar examples for the prompt
        similar_examples_text = ""
        for i, pair in enumerate(similar_pairs):
            similar_examples_text += f"Example {i+1}:\n"
            similar_examples_text += f"Email: {pair['email']}\n"
            similar_examples_text += f"Response: {pair['response']}\n\n"

        # Format extracted info as text
        extracted_info_text = "\n".join([f"{k}: {v}" for k, v in extracted_info.items()])

        # Generate style-based draft
        chain = self.style_prompt | self.llm
        result = chain.invoke({
            "new_email": query_email,
            "extracted_info": extracted_info_text,
            "similar_examples": similar_examples_text
        })

        return result.content
