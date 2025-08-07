# Setup Guide

## Environment Configuration

1. **Create `.env` file**

   Create a `.env` file in the `SEOAgent/backend/` directory:

   ```bash
   cd SEOAgent/backend
   touch .env
   ```

2. **Add your Google API key**

   Edit the `.env` file and add your Google API key:

   ```bash
   # Google API Configuration
   # Get your API key from: https://makersuite.google.com/app/apikey
   GOOGLE_API_KEY=your_actual_google_api_key_here

   # Environment Configuration
   ENV=development
   ```

3. **Get Google API Key**

   - Visit https://makersuite.google.com/app/apikey
   - Sign in to your Google account
   - Click "Create API Key"
   - Copy the generated API key
   - Paste it after `GOOGLE_API_KEY=` in the `.env` file

4. **Start the application**

   ```bash
   docker-compose up --build
   ```

## Security Notes

- The `.env` file has been added to `.gitignore` and will not be committed to version control
- Do not share your API key with others
- In production environments, use more secure methods to manage API keys
