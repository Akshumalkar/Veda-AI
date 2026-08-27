# Deployment Guide: Veda AI Assessment

This repository is ready to be deployed across multiple platforms. Choose the method that best fits your workflow.

---

## Option 1: Render (Recommended - One-Click Blueprint)

Deploy both the backend and frontend services simultaneously using Render Blueprints:

1. Push your code to GitHub / GitLab.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** -> **Blueprint**.
4. Connect this repository. Render will automatically read [ender.yaml](./render.yaml).
5. In the environment variables prompt, provide:
   - GROQ_API_KEY: Your Groq API key (gsk_...)
6. Click **Apply**.
   - Render will build and deploy the **FastAPI Backend** as a Web Service and the **Vite React Frontend** as a Static Site.
   - The frontend's VITE_API_URL will automatically point to the backend service.

---

## Option 2: Vercel (Frontend) + Render / Railway (Backend)

### Step A: Deploy Backend (Render or Railway)
- **Root Directory**: ackend
- **Build Command**: pip install -r requirements.txt
- **Start Command**: uvicorn app.main:app --host 0.0.0.0 --port $PORT
- **Environment Variables**:
  - GROQ_API_KEY: Your Groq API Key
  - GROQ_MODEL: qwen/qwen3.6-27b (optional, defaults to qwen/qwen3.6-27b)
- Copy your deployed backend URL (e.g. https://veda-backend.onrender.com).

### Step B: Deploy Frontend (Vercel)
1. Go to [Vercel](https://vercel.com/) and click **Add New Project**.
2. Select your repository.
3. Configure the project:
   - **Root Directory**: rontend
   - **Framework Preset**: Vite
   - **Environment Variables**:
     - VITE_API_URL: https://your-backend-url.onrender.com (your backend URL without trailing slash)
4. Click **Deploy**.

---

## Option 3: Docker & Docker Compose (VPS / Self-Hosted / AWS / DigitalOcean)

Ensure Docker and Docker Compose are installed on your server.

1. Clone repository to server:
   `ash
   git clone <your-repo-url>
   cd veda-ai-assessment
   `
2. Create .env file at root with your credentials:
   `ash
   GROQ_API_KEY=your_groq_api_key_here
   VITE_API_URL=http://your-server-ip:8000
   `
3. Run with Docker Compose:
   `ash
   docker compose up -d --build
   `
   - Frontend will be accessible on http://<server-ip>:80
   - Backend will be accessible on http://<server-ip>:8000

---

## Environment Variables Reference

| Variable | Target | Description |
|---|---|---|
| GROQ_API_KEY | Backend | Required. Groq API secret key. |
| GROQ_MODEL | Backend | Optional. Default: qwen/qwen3.6-27b. |
| VITE_API_URL | Frontend | Backend API base URL (e.g., https://api.yourdomain.com). Default: http://127.0.0.1:8000. |
