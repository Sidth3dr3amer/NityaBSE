const pool = require('../config/db');

exports.getAnnouncements = async (req, res) => {
  try {
    const { limit = 50, offset = 0, category, company } = req.query;
    
    let query = 'SELECT * FROM announcements WHERE 1=1';
    const params = [];
    let paramCount = 1;

    if (category) {
      query += ` AND category = $${paramCount}`;
      params.push(category);
      paramCount++;
    }

    if (company) {
      query += ` AND (company_name ILIKE $${paramCount} OR company_code ILIKE $${paramCount})`;
      params.push(`%${company}%`);
      paramCount++;
    }

    query += ` ORDER BY filed_at DESC LIMIT $${paramCount} OFFSET $${paramCount + 1}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);
    
    res.json({
      success: true,
      count: result.rows.length,
      data: result.rows
    });
  } catch (error) {
    console.error('Error fetching announcements:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch announcements'
    });
  }
};
