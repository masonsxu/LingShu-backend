# -*- coding: utf-8 -*-
# @Time  : 2025/07/03 17:30
# @Author: masonsxu
# @File  : main.py
# @Desc  : Main application assembly

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import app as api_router

app = FastAPI(
    title="LingShu - Healthcare Data Integration Platform",
    description="A modern, visual platform for healthcare data integration.",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router)
