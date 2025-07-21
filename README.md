# TrackMyCalorie (Gym Edition)

## 🚀 Deployment Instructions (Render.com)

1. **Push your code to GitHub.**
2. **Sign up at [Render.com](https://render.com/)** and create a new Web Service.
3. **Connect your GitHub repo.**
4. **Set build command:**
   ```
   pip install -r requirements.txt
   ```
5. **Set start command:**
   ```
   gunicorn app:app
   ```
6. **Add environment variables** (in the Render dashboard):
   - `GEMINI_API_KEY` (your Gemini API key)
   - `EDAMAM_APP_ID` (if using Edamam)
   - `EDAMAM_APP_KEY` (if using Edamam)
   - Any other secrets you use
7. **Deploy!**

Your app will be live at a public URL you can share with anyone.

---

## 🏋️‍♂️ Features
- AI-powered calorie and macro estimation (Gemini Pro)
- Gym-inspired UI
- User registration, login, and profile
- Meal, supplement, and weight tracking
- Motivational dashboard

---

## 🛠️ Local Development
- `python app.py` to run locally
- `.env` file for local secrets (not committed to GitHub)

---

## 💡 Tips
- For production, always use environment variables for API keys and secrets.
- You can use [Railway.app](https://railway.app/) or [Fly.io](https://fly.io/) with similar steps.
