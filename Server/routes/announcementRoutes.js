const express = require('express');
const router = express.Router();
const { getAnnouncements } = require('../controllers/announcementController');

router.get('/announcements', getAnnouncements);

module.exports = router;
