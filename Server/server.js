const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/api/announcements', (req, res) => {
  res.json({ success: true, data: [] });
});

const PORT = process.env.PORT;

if (!PORT) {
  console.error('❌ PORT is not set by Railway');
  process.exit(1);
}

app.listen(PORT, '0.0.0.0', () => {
  console.log('✅ Listening on', PORT);
});
