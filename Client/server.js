const express = require('express');
const path = require('path');
const app = express();

// 1. Serve static files from the build directory (usually 'dist' for Vite)
// If this file is INSIDE the 'client' folder, use:
app.use(express.static(path.join(__dirname, 'dist')));

// 2. The "Catch-all" handler: for any request that doesn't match 
// a static file, send back index.html.
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// 3. Use the dynamic Railway port
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend running on port ${PORT}`);
});