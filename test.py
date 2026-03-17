import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

load_dotenv()

HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "facebook/bart-large-cnn")
HF_TOKEN = os.getenv("HF_TOKEN")

tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME, token=HF_TOKEN)
model = AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_NAME, token=HF_TOKEN)

print(f"Model loaded successfully from Hugging Face Hub: {HF_MODEL_NAME}")

