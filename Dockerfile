# ==========================================
# STAGE 1: Build React Dashboard
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/dashboard

COPY dashboard/package*.json ./
RUN npm install

COPY dashboard/ ./
RUN npm run build

# ==========================================
# STAGE 2: Python Backend with FFmpeg
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies: FFmpeg and libass
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libass9 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, engines, tools, branding
COPY shorts_engine/ ./shorts_engine/
COPY tools/ ./tools/
COPY branding/ ./branding/
COPY server.py .
COPY video_mappings.json* usage_tracker.json* gemini_api_key.txt* ./

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/dashboard/dist ./dashboard/dist

# Expose Web Port
EXPOSE 8050

# Run FastAPI via Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8050"]
