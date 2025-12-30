const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT;
app.listen(PORT, '0.0.0.0', () => {
  console.log('Listening on', PORT);
});
