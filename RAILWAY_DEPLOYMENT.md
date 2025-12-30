# Railway Deployment Guide

## Deploying Backend (Server)

1. **Create a new Railway project** for the backend
2. **Connect your GitHub repository**
3. **Set Root Directory**: `Server`
4. **Add Environment Variables** in Railway dashboard:
   ```
   DATABASE_URL=your_neon_database_url
   EMAIL_USER=your_email
   EMAIL_PASS=your_app_password
   EMAIL_TO=recipient_email
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   PORT=5000
   ```
5. **Deploy** - Railway will automatically detect `nixpacks.toml` and deploy

## Deploying Frontend (Client)

1. **Create a new Railway service** in the same project
2. **Connect your GitHub repository**
3. **Set Root Directory**: `Client`
4. **Add Environment Variable**:
   ```
   VITE_API_URL=https://your-backend-service.up.railway.app/api
   ```
   (Replace with your actual backend Railway URL)
5. **Deploy** - Railway will use the Dockerfile or nixpacks.toml

## After Deployment

### Update Client API URL
Once both services are deployed, update the Client's `VITE_API_URL` environment variable with your backend's Railway URL.

### Enable CORS on Backend
Make sure your backend allows requests from your frontend domain. Check [Server/server.js](Server/server.js) CORS configuration.

### Test the Application
1. Visit your frontend Railway URL
2. Check if announcements load correctly
3. Test refresh and filtering functionality

## Troubleshooting

### Backend Issues
- Check logs: Railway dashboard → Your service → Logs
- Verify all environment variables are set correctly
- Test database connection
- Check Python dependencies installation

### Frontend Issues
- Verify `VITE_API_URL` points to correct backend
- Check browser console for errors
- Ensure CORS is properly configured on backend

### Common Errors
- `node: command not found` → nixpacks.toml configuration issue
- `playwright: command not found` → Use `npx playwright` in nixpacks.toml
- Empty announcements → Check API URL and CORS settings
