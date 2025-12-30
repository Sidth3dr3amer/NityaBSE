require('dotenv').config();
const express = require('express');
const cors = require('cors');
const pool = require('./config/db');
const announcementRoutes = require('./routes/announcementRoutes');
const { startScheduler, manualRun } = require('./jobs/scrapeBankex');

const app = express();

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.json({ status: 'ok', message: 'Server running' });
});

app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok', database: 'connected' });
  } catch (error) {
    res.status(500).json({ status: 'error', database: 'disconnected' });
  }
});

// Manual trigger endpoint for scraper + email service
app.post('/api/scrape', (req, res) => {
  manualRun();
  res.json({ success: true, message: 'Scraper and email service triggered' });
});

app.use('/api', announcementRoutes);

const PORT = process.env.PORT || 5000;
try {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    startScheduler();
  });
} catch (e) {
  console.error('Failed to start server:', e);
  process.exit(1);
}
