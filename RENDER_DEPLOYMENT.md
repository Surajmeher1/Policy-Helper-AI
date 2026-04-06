# Deploying to Render

## 📋 Prerequisites

- Render account (free at render.com)
- GitHub repository with the code
- Groq API key (from console.groq.com)
- Email credentials (for password reset)

## 🚀 Step-by-Step Deployment

### 1. Connect GitHub Repository
1. Go to [render.com](https://render.com)
2. Click **"New Web Service"**
3. Select **"Connect a repository"**
4. Choose your Policy-Helper-AI repository
5. Click **"Connect"**

### 2. Configure Deployment Settings

Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | policy-helper-ai |
| **Environment** | Python 3 |
| **Region** | Choose closest to you |
| **Branch** | main |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -w 4 -b 0.0.0.0:$PORT app:app` |
| **Plan** | Free (or Starter for production) |

### 3. Add Environment Variables ⚠️ IMPORTANT

Click **"Advanced"** → **"Add Environment Variable"**

Add each of these variables:

```
GROQ_API_KEY=your_groq_api_key_here
FLASK_ENV=production
SECRET_KEY=any-random-long-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
DB_TYPE=sqlite
PORT=5000
```

**🔑 Key Values to Replace:**

| Variable | Where to Get |
|----------|-------------|
| **GROQ_API_KEY** | https://console.groq.com → API Keys |
| **SECRET_KEY** | Any random long string (at least 32 characters) |
| **MAIL_USERNAME** | Your Gmail address |
| **MAIL_PASSWORD** | Gmail App Password (NOT your main password) |

### 4. Generate Gmail App Password

For email functionality:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Factor Authentication** (if not already enabled)
3. Search for **"App passwords"**
4. Select **Mail** and **Windows Computer** (or your OS)
5. Copy the 16-character password
6. Use this in `MAIL_PASSWORD`

### 5. Deploy

Click **"Create Web Service"**

Render will:
- Clone your repository
- Install dependencies
- Start the application
- Assign a `.onrender.com` URL

This takes 2-5 minutes.

## ✅ Verify Deployment

Visit your Render URL (e.g., `https://policy-helper-ai.onrender.com`)

### Check These Features:

- ✓ Landing page loads
- ✓ Can register a new account
- ✓ Can login
- ✓ Can submit a policy and get simplified text (uses `/index` route)
- ✓ Can use chat feature (uses `/chat` and `/api/explain`)

### Troubleshooting

**"Invalid API Key" error:**
- Go to Render Dashboard → Settings → Environment
- Verify `GROQ_API_KEY` is correct and complete
- Click **"Deploy"** to redeploy

**App won't start:**
- Click "Logs" in Render dashboard
- Look for errors like "ModuleNotFoundError" or "ImportError"
- Check that `requirements.txt` is in the root directory

**Email not working:**
- Verify `MAIL_USERNAME` and `MAIL_PASSWORD`
- Make sure Gmail 2FA is enabled and app password is correct
- Check Render logs for SMTP errors

**Database errors:**
- SQLite is the default (works fine for free tier)
- For production, upgrade to Starter plan and use PostgreSQL

## 🔄 Auto-Deploy with GitHub

Every time you push to `main` branch:
1. Render automatically redeploys
2. New code goes live in 2-5 minutes
3. Old version is kept as backup

## 📊 Cold Start Problem (Free Plan)

Free tier apps sleep after 15 minutes of inactivity.
- First request takes 30 seconds to wake up
- Solution: Upgrade to **Starter plan** ($7/month)

## 💾 Database Persistence

SQLite is stored in Render's ephemeral storage:
- Data persists between redeploys
- **But** resets every month on free plan
- **Solution for production:** Use PostgreSQL add-on

### Upgrade to PostgreSQL:

1. Render Dashboard → Select your service
2. Click **"Add-ons"**
3. Add **PostgreSQL**
4. Render automatically sets `DATABASE_URL`
5. Update `.env` if needed:
   ```
   DB_TYPE=postgresql
   DATABASE_URL=postgres://...
   ```

## 🔐 Security Best Practices

✓ Never commit `.env` to GitHub
✓ Always use Render's environment variable section
✓ Rotate API keys every 3 months
✓ Use strong `SECRET_KEY` (32+ characters)
✓ Keep dependencies updated

## 📞 Support

- Render Docs: https://render.com/docs
- Groq API Docs: https://console.groq.com/docs
- Flask Docs: https://flask.palletsprojects.com

## Next Steps

After successful deployment:

1. ✅ Test all features thoroughly
2. ✅ Set up custom domain (if purchased)
3. ✅ Configure email notifications
4. ✅ Monitor logs regularly
5. ✅ Plan database upgrade if needed

Your app is now **live and accessible worldwide!** 🌍🚀
