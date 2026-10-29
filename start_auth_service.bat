@echo off
title YouTube Studio - NestJS Auth Service
cd /d "%~dp0\auth"
echo =======================================================
echo Starting YouTube Studio NestJS Auth Service...
echo Direct Port: http://localhost:8051/api/auth/health
echo =======================================================
if not exist node_modules (
    echo [*] Installing dependencies first...
    call npm install
)
call npm run start:dev
pause
