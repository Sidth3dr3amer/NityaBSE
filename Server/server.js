require('dotenv').config();
const express = require('express');
const cors = require('cors');
const pool = require('./config/db');
const announcementRoutes = require('./routes/announcementRoutes');
const { startScheduler, manualRun } = require('./jobs/scrapeBankex');

const app = express();

// Global process-level handlers for debugging
process.on('unhandledRejection', (reason, p) => {
  console.error('[UNHANDLED REJECTION] Promise:', p, 'reason:', reason);
});
process.on('uncaughtException', (err) => {
  console.error('[UNCAUGHT EXCEPTION]', err);
});

app.use(cors());
app.use(express.json());

// Debug: environment summary
console.log('ENV DEBUG:', {
  PORT: process.env.PORT || 5000,
  NODE_ENV: process.env.NODE_ENV || 'undefined',
  HAS_DATABASE_URL: !!process.env.DATABASE_URL,
  EMAIL_USER_SET: !!process.env.EMAIL_USER,
  CLOUDINARY_CONFIGURED: !!(process.env.CLOUDINARY_API_KEY && process.env.CLOUDINARY_API_SECRET)
});

// Request logger (simple)
app.use((req, res, next) => {
  console.log(`[REQ] ${new Date().toISOString()} ${req.method} ${req.originalUrl} from ${req.ip}`);
  next();
});

app.get('/', (req, res) => {
  res.json({ status: 'ok', message: 'Server running' });
});

app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok', database: 'connected' });
  } catch (error) {
    console.error('[HEALTH] DB check failed:', error && error.message ? error.message : error);
    res.status(500).json({ status: 'error', database: 'disconnected' });
  }
});

// Manual trigger endpoint for scraper + email service
app.post('/api/scrape', (req, res) => {
  try {
    manualRun();
    res.json({ success: true, message: 'Scraper and email service triggered' });
  } catch (err) {
    console.error('[SCRAPE] manualRun error:', err);
    res.status(500).json({ success: false, message: 'Trigger failed' });
  }
});

app.use('/api', announcementRoutes);

// Express error handler to catch route errors
app.use((err, req, res, next) => {
  console.error('[EXPRESS ERROR]', err);
  res.status(500).json({ success: false, error: 'Internal server error' });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);

  // Delay heavy startup work
  setTimeout(() => {
    try {
      startScheduler();
      console.log('[SCHEDULER] Started successfully');
    } catch (err) {
      console.error('[SCHEDULER] Failed:', err);
    }
  }, 10000);
});

