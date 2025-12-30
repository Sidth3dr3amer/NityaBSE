# Email Notification Setup Guide

## Overview
The system automatically sends email notifications whenever a new BSE announcement is added to the database.

## Gmail SMTP Configuration

### Step 1: Enable 2-Step Verification
1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left menu
3. Under "How you sign in to Google", click **2-Step Verification**
4. Follow the setup process if not already enabled

### Step 2: Generate App Password
1. After enabling 2-Step Verification, go back to **Security**
2. Click **2-Step Verification** again
3. Scroll down to **App passwords** and click it
4. Select **Mail** as the app
5. Select **Windows Computer** (or your device)
6. Click **Generate**
7. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Configure .env File
Open `Server/.env` and update these values:

```env
# Replace with your Gmail address
EMAIL_USER=youremail@gmail.com

# Paste the 16-character app password (remove spaces)
EMAIL_PASS=abcdefghijklmnop

# Email address to receive notifications
EMAIL_TO=recipient@gmail.com
```

## Testing Email Notifications

### Option 1: Manual Test via API
```bash
curl -X POST http://localhost:5000/api/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "company_code": "TEST",
    "subject": "Test Announcement",
    "summary": "This is a test email notification",
    "category": "company_update",
    "filed_at": "2025-12-29T10:00:00Z",
    "pdf_url": "https://example.com/test.pdf"
  }'
```

### Option 2: Trigger Scraper
```bash
# The scraper will automatically send emails for new announcements
curl -X POST http://localhost:5000/api/scrape
```

## Email Template Features

The automated emails include:
- **Company name and code** with category badge
- **Subject** of the announcement
- **AI-generated summary** (if available)
- **Filing date and time** in Indian timezone
- **Direct link to PDF** disclosure document
- Professional corporate styling

## Troubleshooting

### "Invalid credentials" error
- Make sure you're using an **App Password**, not your regular Gmail password
- Remove any spaces from the app password in .env file
- Verify 2-Step Verification is enabled

### "Connection timeout" error
- Check your internet connection
- Verify Gmail SMTP is not blocked by firewall
- Try using port 465 (SSL) instead of 587 (TLS)

### No emails received
- Check spam/junk folder
- Verify `EMAIL_TO` address is correct in .env
- Check server logs for email errors
- Ensure nodemailer package is installed: `npm install nodemailer`

## Email Frequency

- Emails are sent **only for NEW announcements** (not duplicates)
- The scraper runs every **5 minutes** automatically
- Each new announcement triggers one email
- No emails during periods with no new announcements

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to version control
- Use App Passwords, never your main Gmail password
- Keep your app password secure
- Regularly rotate app passwords for security

## Disabling Email Notifications

To temporarily disable emails without removing the code:
1. Remove or comment out `EMAIL_TO` in .env file
2. The system will skip sending emails but continue scraping
