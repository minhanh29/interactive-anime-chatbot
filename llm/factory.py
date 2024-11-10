from llama_index.llms.bedrock import Bedrock
from llama_index.llms.gemini import Gemini
from anthropic import AnthropicBedrock
from llama_index.core import ServiceContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import instructor
from time import time
import google.generativeai as genai
from config import settings


genai.configure(api_key=settings.GEMINI_API_KEY)


class _Factory:
    def __init__(self):
        self.model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")
        self.llm_client = instructor.from_gemini(
            client=self.model,
            mode=instructor.Mode.GEMINI_JSON,
        )
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_folder="./data/hf")
        self.service_context = ServiceContext.from_defaults(
            llm=Gemini(
                model="models/gemini-1.5-flash-latest",
                api_key=settings.GEMINI_API_KEY
            ),
            embed_model=self.embed_model
        )

    def invoke_llm(self, prompt, response_model=None):
        st = time()
        res = self.llm_client.messages.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_model=response_model
        )
        print("Invoke", time() - st)
        return res

    def invoke_llm_with_stop_sequence(self, prompt, stop_sequences=[]):
        st = time()
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                stop_sequences=stop_sequences,
                max_output_tokens=4096,
                temperature=0,
            ),
        )
        print("Raw", time() - st)
        return response.text


Factory: _Factory = _Factory()
