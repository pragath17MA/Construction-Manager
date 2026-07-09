# Production Deployment Guides: APEXBuild Platform

This guide outlines deployment instructions for Render, Railway, Vercel, and AWS target environments.

---

## 🚀 1. Render Deployment (Recommended for Quick Setup)

Render is ideal for hosting both the FastAPI backend service and the PostgreSQL database container.

### Step 1. Deploy PostgreSQL
1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click **New** -> **PostgreSQL**.
3. Set Name to `apexbuild-db` and click **Create Database**.
4. Copy the **Internal Database URL** (e.g. `postgresql://user:pass@host/db`).

### Step 2. Deploy FastAPI Backend Service
1. Click **New** -> **Web Service**.
2. Connect your GitHub repository.
3. Set Environment to `Python`.
4. Build Command: `pip install -r requirements.txt`.
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
6. Click **Advanced** and add these Environment Variables:
   - `DATABASE_URL`: (Paste the database URL from Step 1)
   - `SECRET_KEY`: (Generate a secure random string)
   - `GROQ_API_KEY`: (Your Groq API key)
   - `OPENWEATHER_API_KEY`: (Your Weather API key)
7. Click **Create Web Service**. Render will build and deploy the container.

---

## 🚃 2. Railway Deployment (Supports Multi-Container docker-compose)

Railway can deploy the entire stack directly from the existing `docker-compose.yml` config.

### Steps:
1. Install the Railway CLI or connect your GitHub account at [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Railway automatically detects `docker-compose.yml` and spins up individual services for the frontend, backend, PostgreSQL database, and ChromaDB.
4. Go to the `backend` service settings and configure variables: `GROQ_API_KEY`, `OPENWEATHER_API_KEY`, and `SECRET_KEY`.
5. Go to the `frontend` service settings, add `VITE_API_URL` pointing to the backend's public domain URL, and save.

---

## ⚡ 3. Vercel Deployment (Recommended for Frontend)

Vercel is optimized for blazing-fast static frontend web applications.

### Steps:
1. Log in to [Vercel](https://vercel.com) and click **Add New** -> **Project**.
2. Import your GitHub repository.
3. In **Framework Preset**, select **Vite**.
4. In **Root Directory**, set to `frontend`.
5. In **Environment Variables**, add:
   - `VITE_API_URL`: (Your backend's public API URL)
6. Click **Deploy**. Vercel will build the optimized production assets and assign a public URL.

---

## ☁️ 4. AWS Deployment (Production-Scale ECS)

For enterprise-scale setups, deploy backend containers to AWS ECS (Elastic Container Service) behind an ALB.

### ECS + Fargate Deployment Steps:
1. **ECR Registry:** Create ECR repositories for both backend and frontend images:
   ```bash
   aws ecr create-repository --repository-name apexbuild-backend
   aws ecr create-repository --repository-name apexbuild-frontend
   ```
2. **Build & Push:** Tag and push your Docker containers to ECR.
3. **Database:** Deploy an Amazon RDS Serverless PostgreSQL instance inside private subnets of your VPC.
4. **ECS Task Definitions:** Configure JSON task definitions specifying environment parameters and map files mounts.
5. **ALB Routing:** Configure Application Load Balancer path routing:
   - Path `/api/*` -> forwards requests to the target group of Fargate ECS Backend instances on port 8000.
   - Path `/*` -> forwards traffic to Fargate ECS Frontend instances on port 3000.
