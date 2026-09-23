# MedNarrate Admin — Independent Deployment Guide

## Deployment Architecture
- **Frontend App**: Hosted on Vercel / Netlify / AWS Amplify (`admin.mednarrate.com`).
- **Backend API**: Hosted on AWS EC2 / GCP Cloud Run / Kubernetes (`api.mednarrate.com`).

## Frontend Environment Variables (Vercel)
```env
NEXT_PUBLIC_API_BASE_URL=https://api.mednarrate.com
```

## Backend CORS Production Configuration
In `mednarrate-backend/.env`:
```env
CORS_ORIGINS=["https://admin.mednarrate.com", "https://app.mednarrate.com"]
ENVIRONMENT=production
```

## Vercel Deployment Commands
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`
