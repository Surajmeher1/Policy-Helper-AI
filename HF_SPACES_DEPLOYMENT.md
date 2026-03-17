# Deployment Guide - Hugging Face Spaces

Deploy your Flask app on **Hugging Face Spaces** - a free, easy way to host ML/AI projects.

## Step 1: Create/Sign Into Hugging Face

1. Go to [huggingface.co](https://huggingface.co)
2. Create a free account or sign in
3. Create a new **Personal Access Token** for authentication:
   - Settings → Access Tokens → New token → Read/Write access
   - Copy the token (you'll need it later)

## Step 2: Create a New Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in details:
   - **Owner**: Your username
   - **Space name**: `policy-helper-ai` (or any name)
   - **Space SDK**: Select **"Docker"** (important for Flask!)
   - **Visibility**: Public or Private
   - **Hardware**: Select **"CPU basic"** (free) or **"CPU upgrade"** if available

4. Click **"Create Space"**

## Step 3: Set Environment Variables

1. Click your Space name
2. Go to **Settings** → **Repository secrets**
3. Add these secrets (copy from your `.env.example`):
   ```
   HF_MODEL_NAME=facebook/bart-large-cnn
   HF_TOKEN=your_hf_token_here
   GROQ_API_KEY=your_groq_key_here
   SECRET_KEY=your_random_secret_key
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```

## Step 4: Connect GitHub Repository

### Option A: Automatic (Recommended)

1. In the Space, go to **Settings** → **Linked repositories**
2. Click **"Link a repository"**
3. Select your GitHub repo: `Surajmeher1/Policy-Helper-AI`
4. Choose branch: `main`
5. Enable **"Sync with repo"** for auto-updates

The Space will automatically redeploy when you push to GitHub!

### Option B: Manual Push to HF Space Repository

```bash
# Navigate to your project
cd A:\Project-2

# Add HF Space remote
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/policy-helper-ai

# Push to HF Space
git push space main
```

Replace `YOUR_USERNAME` with your HuggingFace username.

## Step 5: Monitor Deployment

1. Go to your Space
2. Click the **"Logs"** tab to watch the build process
3. When complete, your Space will show a URL: `https://huggingface.co/spaces/YOUR_USERNAME/policy-helper-ai`
4. Click the deployed Space link to access your app

## Space URL Structure

Your app will be accessible at:
```
https://YOUR_USERNAME-policy-helper-ai.hf.space
```

## Important Notes

### Port Configuration
- HF Spaces uses port **7860** (configured in Dockerfile)
- The app must bind to `0.0.0.0:7860`
- ✅ Already configured in `app.py` and `Dockerfile`

### Database
- SQLite works but data resets when Space restarts
- For persistent data, upgrade to paid tier or use external database
- Consider connecting external PostgreSQL for production

### Resource Limits
- **Free tier**: ~2GB RAM, limited compute
- **CPU upgrade** (~$7/month): Better performance
- **GPU** (optional): For faster model inference

### Model Loading
- First run takes longer (model downloads)
- Subsequent runs are cached
- ~2-3GB for facebook/bart-large-cnn model

### HTTPS
- Automatically provided with SSL certificate
- Subdomain: `https://YOUR_USERNAME-policy-helper-ai.hf.space`

## Auto-Deploy from GitHub

With linked repository, your Space automatically redeploys when you push:

```bash
# Make changes locally
git add .
git commit -m "update feature"
git push origin main

# HF Space will automatically rebuild and deploy!
```

## Manage Your Space

### View Logs
```bash
# SSH into HF Space (if enabled)
# Or check logs via web interface: Settings → Logs
```

### Restart Space
1. Settings → "Restart this Space"

### Pause/Stop Space
1. Settings → "Pause this Space" (saves compute resources)
2. Space pauses after 48 hours of inactivity (free tier)

### Upgrade Hardware
1. Settings → Hardware
2. Choose upgraded tier if available

## Useful Commands

```bash
# Check your HF token is valid
huggingface-cli login --token YOUR_TOKEN

# Upload files to Space
huggingface-cli repo create policy-helper-ai --repo-type space --space-sdk docker

# Push updates
git push space main
```

## Troubleshooting

### "Build failed" error
```bash
# Check Dockerfile syntax
# Ensure all dependencies in requirements.txt
# View full error in Space Logs tab
```

### App won't start
- Check port is 7860 in Dockerfile
- Verify `app.py` can run with `gunicorn`
- Check environment variables are set

### Model download fails
- Ensure HF_TOKEN is set correctly
- Model may be too large for initial load
- Increase timeout in Dockerfile: `--timeout 120`

### Database persistence
- SQLite won't persist between restarts
- Add PostgreSQL for permanent storage
- Or use external database service

### Slow first load
- Model caching takes time
- Consider using lighter model
- Or accept 1-2 minute startup time

## Cost

| Tier | Price | Resources | Best For |
|------|-------|-----------|----------|
| **Free** | $0 | ~2GB RAM, CPU | Development & testing |
| **CPU** | $7/month | Better CPU | Light production use |
| **GPU** | $16/month | GPU support | Faster inference |

## Next Steps

1. Create your Space (Steps 1-2)
2. Set environment variables (Step 3)
3. Link GitHub repo (Step 4A) or push manually (Step 4B)
4. Wait for deployment
5. Access via the HF Space URL

Your app will be live at: `https://YOUR_USERNAME-policy-helper-ai.hf.space`

## Compare Deployments

| Feature | HF Spaces | Oracle Cloud | Render |
|---------|-----------|--------------|--------|
| RAM | 2GB | 24GB | 512MB |
| Cost | $0 (free tier) | $0 forever | $0 limited |
| Setup | 5 min (Docker) | 20 min (Linux) | 3 min |
| ML Support | Excellent | Excellent | Poor |
| Database | Limited | Excellent | Limited |
| Auto-deploy | Yes (from GitHub) | Manual | Yes |
| Best For | Quick deployment | Production | Hobby |

---

Need help? Check [huggingface.co/spaces](https://huggingface.co/spaces) or HF Docs.
