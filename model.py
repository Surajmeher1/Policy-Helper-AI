# DEPRECATED: This file is no longer used
# 
# Previously, this file downloaded and cached the facebook/bart-large-cnn model
# from Hugging Face Hub for local text summarization/simplification.
#
# MIGRATION TO API-BASED APPROACH:
# ================================
# To reduce RAM and storage consumption, the project now uses the Groq API
# for text simplification instead of loading the ~1.6GB BART model locally.
#
# Key Changes:
# - ml_simplify() function in app.py now calls Groq API (llama-3.3-70b-versatile)
# - No more local model loading needed
# - Freed up storage: ~1.6GB previously used by the BART model
# - Freed up RAM: No longer loading large transformer model in memory
# - HF_TOKEN in .env is now optional (only needed if you want to load other HF models)
#
# Benefits:
# ✓ Significantly reduced memory footprint
# ✓ Faster startup time (no model loading delay)
# ✓ Cleaner deployment (no large model files to package)
# ✓ Same functionality provided by Groq API
#
# If you need to revert to local model usage, see git history for the original version.


