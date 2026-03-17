import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

load_dotenv()

HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "facebook/bart-large-cnn")
HF_TOKEN = os.getenv("HF_TOKEN")

# Download and cache the model + tokenizer from Hugging Face Hub
tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME, cache_dir="./models", token=HF_TOKEN)
model = AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_NAME, cache_dir="./models", token=HF_TOKEN)

print(f"Model downloaded from Hugging Face Hub and cached in ./models: {HF_MODEL_NAME}")

