# Deployment Platforms

## ⭐ Option 1: Hugging Face Spaces (Recommended for ML/AI)

**Resources:** ~2GB RAM, free tier with auto-deploy from GitHub  
**Setup Time:** ~5 minutes  
**Best For:** Quick deployment, ML project showcase, community integration

Perfect for ML/AI projects. Automatic deployment when you push to GitHub.

👉 See [HF_SPACES_DEPLOYMENT.md](HF_SPACES_DEPLOYMENT.md) for step-by-step guide

---

## ⭐ Option 2: Oracle Cloud Always Free Tier

**Resources:** 24GB RAM, 4 ARM CPUs, 100GB storage - **FOREVER FREE**  
**Setup Time:** ~20 minutes  
**Best For:** Production, unlimited resources, full control

Best for scaling and production workloads with no cost limits.

👉 See [ORACLE_DEPLOYMENT.md](ORACLE_DEPLOYMENT.md) for complete setup guide

---

## Alternative: Render

**Resources:** 512MB RAM free tier (may be limiting for ML models)

If you prefer Render's simplicity, follow the guide below.

---

## Step 1: Create a Render Account
1. Go to [render.com](https://render.com)
2. Sign up for a free account (recommended)
3. Link your GitHub account

## Step 2: Create a New Web Service
1. Click **"New +"** → **"Web Service"**
2. Select your GitHub repository: `Policy-Helper-AI`
3. Fill in the details:
   - **Name**: `Policy-Helper-AI` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

## Step 3: Set Environment Variables
In the Render dashboard, go to **Environment** and add:

```
SECRET_KEY=<generate-a-random-string>
GROQ_API_KEY=<your-groq-api-key>
HF_MODEL_NAME=facebook/bart-large-cnn
HF_TOKEN=<your-huggingface-token>
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email@gmail.com>
MAIL_PASSWORD=<your-app-password>
```

⚠️ **Important Notes:**
- Generate a strong `SECRET_KEY` using: `python -c "import secrets; print(secrets.token_hex(32))"`
- For Gmail, use an **App Password** (not your regular password). [Learn how](https://support.google.com/accounts/answer/185833)
- Never commit `.env` file to GitHub

## Step 4: Deploy
1. Click **"Deploy"**
2. Render will automatically:
   - Pull your code from GitHub
   - Install dependencies from `requirements.txt`
   - Run the app with `gunicorn`
3. Your app will be live at: `https://<your-app-name>.onrender.com`

## Step 5: Enable Auto-Deploy (Optional)
Go to **Settings** → **Auto-Deploy** and enable to automatically redeploy when you push to GitHub.

## Database Notes
- Currently uses SQLite (`users.db`)
- For production, consider upgrading to PostgreSQL:
  1. In Render dashboard, create a **PostgreSQL** database
  2. Update `app.config['SQLALCHEMY_DATABASE_URI']` in `app.py`
  3. Redeploy

## Troubleshooting

**Deployment fails?**
- Check build logs in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

**App running but not loading?**
- Check if PORT environment variable is being used (✅ configured)
- Review logs: Render → Logs tab

**Performance issues with large models?**
- Free tier has 512MB RAM - may struggle with ML models
- Upgrade to Pro tier or use a GPU service
