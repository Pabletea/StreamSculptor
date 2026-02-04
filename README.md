# StreamSculptor — AI Multimodal Highlights & Content Studio

## Description
StreamSculptor is a platform that automatically detects the best moments from a VOD, generates short clips optimized for social media, creates SEO-friendly titles and descriptions, generates AI-stylized thumbnails, subtitles/translates clips, and provides a dashboard for review and publishing.


⚠️ NOTICE: Video processing times are currently longer than desired. Actively working to reduce them.</p>



## Local Setup

1. Clone the repository:

2. Start services with Docker Compose:
```bash
    docker-compose up --build
```
3.Access services
- Backend : ```http://localhost:8000```
- MinIO: ```http://localhost:9000```
- Redis: ```localhost:6379```
- Postgres: ```localhost:5432```
- Fronted / Web APP: ```localhost:`3000```
---

## Main Endpoints
### Ingest
- POST ```/ingest/upload/``` — Upload a VOD file or URL
- POST ```/ingest/download/``` — Download and enqueue a VOD


## Arquitecture Overview
```css
[VOD/File] --> [FastAPI ingest endpoint] --> [Celery Worker] --> 
[FFmpeg: extract audio/video] --> [MinIO storage] --> 
[ASR + Audio/Video Classification + Keypoint Detection] --> 
[Score fusion] --> [Ranked clips] --> 
[Text Generation + TTI for thumbnails] --> [Frontend review & publish]
```

## Roadmap & Future Features

- [ ] overlaying subtitles irl on generated clips
- [ ] Thumbnail generation
- [ ] Custom ML models trainable per content type (gaming, podcasts, tutorials, etc.)
- [ ] Reduce video processing times through pipeline optimization
- [ ] Cloud storage integrations (S3, Google Cloud, Azure)

## Contributing
We welcome contributions! Please check the roadmap above for features you'd like to help implement.
