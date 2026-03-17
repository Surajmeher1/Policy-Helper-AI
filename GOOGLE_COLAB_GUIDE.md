# Google Colab - Easy AI Development Guide

**Google Colab** is a FREE Jupyter notebook in the cloud. Perfect for your AI project!

## Why Google Colab?

| Feature | Google Colab |
|---------|--------------|
| Cost | 100% FREE |
| RAM | 12GB+ (more than enough!) |
| GPU | Free GPU available |
| Storage | Google Drive integration |
| Setup | Zero - just open browser |
| Best For | ML/AI development |

## Step 1: Open Google Colab

1. Go to **[colab.research.google.com](https://colab.research.google.com)**
2. Sign in with your Google account (create one if needed)
3. Click **"+ New notebook"**

## Step 2: Install Your Dependencies

In the first cell, paste this and run (Ctrl+Enter):

```python
# Install dependencies
!pip install transformers torch language-tool-python textstat groq python-dotenv flask flask-sqlalchemy

# Check GPU (optional - you get free GPU!)
!nvidia-smi
```

## Step 3: Mount Google Drive (Save Your Work)

This lets you save files to Google Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
```

Click the link, allow access, copy the code into the cell.

## Step 4: Create Your API Keys File

```python
# Create .env file in Google Drive to store your API keys
env_content = """
GROQ_API_KEY=your_groq_key_here
HF_MODEL_NAME=facebook/bart-large-cnn
HF_TOKEN=your_hf_token_here
SECRET_KEY=test_secret_key
"""

with open('/content/drive/MyDrive/.env', 'w') as f:
    f.write(env_content)

print("✅ .env file created in Google Drive")
```

Replace with your actual API keys!

## Step 5: Load Your Project Code

**Option A: Upload from GitHub**
```python
!git clone https://github.com/Surajmeher1/Policy-Helper-AI.git
%cd Policy-Helper-AI
```

**Option B: Upload ZIP file**
1. Download your project as ZIP
2. Upload to Colab (Files button on left) or Google Drive
3. Extract:
```python
!unzip /content/Policy-Helper-AI.zip
%cd Policy-Helper-AI
```

## Step 6: Test Your Code

Copy the main functions from your `app.py`:

```python
# Load environment variables
from dotenv import load_dotenv
import os
load_dotenv('/content/drive/MyDrive/.env')

# Your imports from app.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import language_tool_python
import textstat
import re

HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "facebook/bart-large-cnn")
HF_TOKEN = os.getenv("HF_TOKEN")

# Load model (first time takes 1-2 min)
print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME, token=HF_TOKEN)
model = AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_NAME, token=HF_TOKEN)
print("✅ Model loaded!")

# Test it
test_text = "The Data Protection Act mandates compliance with strict regulations."
inp = tokenizer.encode(test_text, return_tensors="pt", max_length=1024, truncation=True)
output = model.generate(inp, max_length=150, min_length=40, num_beams=4)
result = tokenizer.decode(output[0], skip_special_tokens=True)
print(f"Input: {test_text}")
print(f"Simplified: {result}")
```

## Step 7: Run Your ML Functions

Test your simplification functions:

```python
def ml_simplify(text):
    inp = tokenizer.encode(text, return_tensors="pt", max_length=1024, truncation=True)
    output = model.generate(inp, max_length=150, min_length=40, num_beams=4)
    simplified = tokenizer.decode(output[0], skip_special_tokens=True)
    return simplified.strip()

# Test
policy_text = "Pursuant to the Digital Personal Data Protection Act, organizations shall ensure compliance with data retention policies."
simplified = ml_simplify(policy_text)
print(f"Simplified: {simplified}")
```

## Step 8: Use Groq API for Chat

```python
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_groq(query):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": query}],
        "temperature": 0.7
    }
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

# Test
answer = ask_groq("What is a privacy policy?")
print(answer)
```

## Useful Colab Tips

### Save Your Notebook
```
Ctrl+S (or click File → Save)
```
Saves to Google Drive automatically!

### Upload Files
```python
from google.colab import files
uploaded = files.upload()
# Select file from your computer
```

### Download Results
```python
files.download('results.txt')
```

### Use GPU
```python
# Check if GPU is available
import torch
print(torch.cuda.is_available())  # Should print True
print(torch.cuda.get_device_name(0))  # Shows GPU type
```

### Increase Runtime (if needed)
- Runtime → Change runtime type → GPU or TPU (select one)

## Useful Commands

```python
# Current directory
!pwd

# List files
!ls -la

# Install package
!pip install package_name

# Check Python version
!python --version

# Run Python file
!python script.py
```

## Save to Google Drive

```python
# Save results
with open('/content/drive/MyDrive/results.txt', 'w') as f:
    f.write("Your results here")

# Read from Drive
with open('/content/drive/MyDrive/.env', 'r') as f:
    print(f.read())
```

## Next: Deploy When Ready

Once you're happy with your code in Colab:
1. Export notebook as Python script
2. Upload to GitHub
3. Deploy on HF Spaces or Replit (much simpler than Flask!)

## Common Issues

**"CUDA out of memory"**
```python
# Reduce batch size or use smaller model
# Or switch to CPU: model = model.cpu()
```

**"Model not found"**
- Check HF_TOKEN is correct
- Models require authentication token

**"Too slow"**
- Enable GPU: Runtime → Change runtime type
- Use smaller model from Hugging Face

---

**Start here:** [colab.research.google.com](https://colab.research.google.com)

Click **"+ New notebook"** and paste the code above!

Your project will run with **12GB+ RAM and free GPU** 🚀
