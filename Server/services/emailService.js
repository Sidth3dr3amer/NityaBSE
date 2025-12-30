const { Resend } = require('resend');
const pool = require('../config/db');
require('dotenv').config();

// Create Resend client
const resend = new Resend(process.env.RESEND_API_KEY);

// Helper: format dates in IST (Asia/Kolkata)
function formatIST(date, options = {}) {
    try {
        const d = date ? new Date(date) : new Date();
        return new Intl.DateTimeFormat('en-IN', Object.assign({ timeZone: 'Asia/Kolkata' }, options)).format(d);
    } catch (e) {
        return String(date || '');
    }
}

// Helper: parse EMAIL_TO which can be a comma-separated list
function parseRecipients() {
    const raw = process.env.EMAIL_TO || '';
    const list = raw.split(',').map(s => s.trim()).filter(Boolean);
    return list.length ? list : null;
}

// Debug: Log email configuration (timestamps in IST)
console.log('\n' + '='.repeat(50));
console.log(`🚀 [DEPLOYMENT] Email Service Health Check at ${formatIST()}`);
console.log('='.repeat(50));
console.log(`  RESEND_API_KEY: ${process.env.RESEND_API_KEY ? '✓ Set (length: ' + process.env.RESEND_API_KEY.length + ')' : '✗ Missing'}`);
console.log(`  EMAIL_FROM: ${process.env.EMAIL_FROM ? '✓ Set (' + process.env.EMAIL_FROM + ')' : '✗ Missing'}`);
console.log(`  EMAIL_TO: ${process.env.EMAIL_TO ? '✓ Set (' + process.env.EMAIL_TO + ')' : '✗ Missing'}`);

// Verify Resend configuration on startup
(async () => {
    try {
        // Test the API key by making a simple request
        if (process.env.RESEND_API_KEY && process.env.EMAIL_FROM) {
            console.log('[HEALTH] ✓ Resend client initialized successfully');
        } else {
            console.log('[HEALTH] ✗ Missing required environment variables');
        }
    } catch (error) {
        console.error('[HEALTH] ✗ Resend initialization failed:', error.message);
    }
    console.log('='.repeat(50) + '\n');
})();

let isRunning = false;

// Send email for a single announcement
async function sendEmail(announcement) {
    const recipients = parseRecipients();
    const emailFrom = process.env.EMAIL_FROM || 'onboarding@resend.dev';

    if (!recipients) {
        return { success: false, error: 'No recipient configured (EMAIL_TO missing)' };
    }

    // Parse Cloudinary URLs or base64 images from JSON
    let imageUrls = [];
    let hasScreenshots = false;
    
    if (announcement.screenshot_url) {
        try {
            const screenshotData = JSON.parse(announcement.screenshot_url);
            
            if (screenshotData.images && Array.isArray(screenshotData.images)) {
                console.log(`   [IMAGES] Found ${screenshotData.images.length} image(s)`);
                
                if (screenshotData.images.length === 0) {
                    console.log(`   [WARNING] Images array is empty - screenshot capture may have failed during scraping`);
                }
                
                imageUrls = screenshotData.images.map((img, index) => ({
                    url: img.url || img.data,  // Support both Cloudinary URL and base64 data
                    filename: img.filename || `image_${index}.png`,
                    type: img.type || 'unknown',
                    page_number: img.page_number || null,
                    isBase64: !img.url && !!img.data
                }));
                
                hasScreenshots = imageUrls.length > 0;
                
                imageUrls.forEach((img, idx) => {
                    const source = img.isBase64 ? '(base64)' : `(Cloudinary)`;
                    console.log(`   [IMAGE] ${idx + 1}: ${img.filename} (${img.type}) ${source}`);
                });
            }
        } catch (err) {
            console.log(`   [WARNING] Failed to parse screenshot JSON: ${err.message}`);
        }
    } else {
        console.log(`   [INFO] No screenshots available (screenshot_url is null)`);
    }

    const subjectDateOpts = { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    const subjectDate = announcement.filed_at ? formatIST(announcement.filed_at, subjectDateOpts) : formatIST();

    const emailOptions = {
        from: emailFrom,
        to: recipients,
        subject: `BSE Announcement: ${announcement.company_name} - ${announcement.category || 'Update'} | ${subjectDate}`,

        html: `
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
                <h2 style="color: #1a2332; border-bottom: 3px solid #0a7b83; padding-bottom: 10px;">
                    New BSE BANKEX Announcement
                </h2>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #0a7b83; margin-top: 0;">${announcement.company_name}</h3>
                    <p style="color: #6c757d; font-size: 12px; margin: 5px 0;">
                        <strong>BSE Code:</strong> ${announcement.company_code || 'N/A'} | 
                        <strong>Category:</strong> ${announcement.category || 'Other'}
                    </p>
                    <p style="color: #6c757d; font-size: 12px; margin: 5px 0;">
                        <strong>Exchange:</strong> ${announcement.exchange || 'BSE'} | 
                        <strong>Index:</strong> ${announcement.index_name || 'BANKEX'}
                    </p>
                </div>

                <div style="margin: 20px 0;">
                    <h4 style="color: #2c3e50; margin-bottom: 10px;">Subject:</h4>
                    <p style="color: #343a40; line-height: 1.6;">${announcement.subject}</p>
                </div>

                ${announcement.summary && announcement.summary !== announcement.subject ? `
                <div style="background: #e0f2fe; border-left: 4px solid #0a7b83; padding: 15px; margin: 20px 0;">
                    <h4 style="color: #0a7b83; margin-top: 0;">🤖 AI Summary:</h4>
                    <p style="color: #343a40; line-height: 1.6; margin: 0;">${announcement.summary}</p>
                </div>
                ` : ''}

                ${announcement.title && announcement.title !== announcement.subject ? `
                <div style="margin: 20px 0; padding: 10px; background: #fff3cd; border-radius: 6px;">
                    <p style="color: #856404; margin: 0; font-size: 13px;">
                        <strong>Title:</strong> ${announcement.title}
                    </p>
                </div>
                ` : ''}

                <div style="margin: 20px 0; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <p style="color: #6c757d; font-size: 12px; margin: 5px 0;">
                        <strong>📅 Filing Date:</strong> ${formatIST(announcement.filed_at, { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true })}
                    </p>
                    <p style="color: #6c757d; font-size: 12px; margin: 5px 0;">
                        <strong>📝 Scraped:</strong> ${announcement.scraped_at ? formatIST(announcement.scraped_at) : 'Just now'}
                    </p>
                    ${announcement.source_page ? `
                    <p style="color: #6c757d; font-size: 12px; margin: 5px 0;">
                        <strong>🔗 Source:</strong> <a href="${announcement.source_page}" style="color: #0a7b83;">View on BSE</a>
                    </p>
                    ` : ''}
                </div>

                ${hasScreenshots ? `
                <div style="margin: 30px 0;">
                    <h4 style="color: #2c3e50; margin-bottom: 15px;">📄 Document Preview:</h4>
                    ${imageUrls.map((img, idx) => {
                        const isAnnouncement = img.type === 'announcement';
                        const isPdfPage = img.type === 'pdf_page';
                        const label = isAnnouncement ? 'Announcement Details' : 
                                     isPdfPage ? `PDF Page ${img.page_number}` : 
                                     `Image ${idx + 1}`;
                        
                        // Handle both URLs and base64 data
                        const imgSrc = img.isBase64 ? `data:image/png;base64,${img.url}` : img.url;
                        
                        return `
                        <div style="margin-bottom: 20px;">
                            <p style="color: #6c757d; font-size: 13px; font-weight: 600; margin-bottom: 8px;">
                                ${label}
                            </p>
                            <div style="border: 2px solid ${isAnnouncement ? '#0a7b83' : '#dee2e6'}; border-radius: 8px; overflow: hidden; background: white;">
                                <img src="${imgSrc}" 
                                     alt="${label}" 
                                     style="width: 100%; height: auto; display: block; max-height: 1000px; object-fit: contain;">
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
                ` : `
                <div style="margin: 30px 0; background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 6px;">
                    <p style="color: #856404; margin: 0; font-weight: 600;">
                        ⚠️ Document Preview Not Available
                    </p>
                    <p style="color: #856404; margin: 8px 0 0 0; font-size: 13px;">
                        Screenshots could not be captured during scraping. Please download the full PDF document using the button below.
                    </p>
                </div>
                `}

                ${announcement.pdf_url ? `
                <div style="margin: 30px 0; text-align: center;">
                    <a href="${announcement.pdf_url}" 
                       style="background: #0a7b83; color: white; padding: 14px 28px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;
                              font-weight: bold; font-size: 15px; box-shadow: 0 2px 4px rgba(10,123,131,0.3);">
                        📥 Download Full PDF Document
                    </a>
                    <p style="color: #6c757d; font-size: 11px; margin-top: 10px;">
                        Click above to view the complete disclosure document
                    </p>
                </div>
                ` : ''}

                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <div style="text-align: center; color: #6c757d; font-size: 11px;">
                    <p style="margin: 5px 0;">
                        <strong>BSE BANKEX Corporate Announcements Dashboard</strong>
                    </p>
                    <p style="margin: 5px 0;">
                        Automated notification system with AI-powered summaries
                    </p>
                    <p style="margin: 5px 0; opacity: 0.7;">
                        Announcement ID: ${announcement.id ? announcement.id.substring(0, 8) : 'N/A'}
                    </p>
                </div>
            </div>
        `
    };

    try {
        const { data, error } = await resend.emails.send(emailOptions);
        
        if (error) {
            console.error(`   [Email Error] ${error.message}`);
            return { success: false, error: error.message };
        }
        
        console.log(`   [Email] Message sent: ${data.id}`);
        return { success: true };
    } catch (error) {
        console.error(`   [Email Error] ${error.message}`);

        // Provide specific guidance based on error type
        if (error.message.includes('API key')) {
            console.error('   [Email Error] Invalid API key. Check RESEND_API_KEY');
        } else if (error.message.includes('from')) {
            console.error('   [Email Error] Invalid sender email. Check EMAIL_FROM');
        }

        return { success: false, error: error.message };
    }
}

// Main function to process unsent announcements
async function processUnsentAnnouncements() {
    if (isRunning) {
        console.log('[Email Service] Previous job still running, skipping...');
        return;
    }

    const recipients = parseRecipients();
    if (!recipients) {
        console.log('[Email Service] No recipient configured (EMAIL_TO not set), skipping...');
        return;
    }

    isRunning = true;
    const startTime = new Date();
    console.log(`\n[Email Service] Starting at ${startTime.toLocaleString()}`);

    try {
        // Get all unsent announcements
        const result = await pool.query(
            'SELECT * FROM announcements WHERE uploaded = false ORDER BY filed_at DESC'
        );

        const unsent = result.rows;
        
        if (unsent.length === 0) {
            console.log('[Email Service] No unsent announcements found');
            isRunning = false;
            return;
        }

        console.log(`[Email Service] Found ${unsent.length} unsent announcement(s)`);
        
        if (unsent.length > 0) {
            console.log('[Email Service] IDs to process:', unsent.map(a => a.id.substring(0, 8)).join(', '));
        }

        let sentCount = 0;
        let failedCount = 0;

        for (const announcement of unsent) {
            console.log(`[Email Service] Processing: ${announcement.company_name} - ${announcement.subject.substring(0, 50)}...`);
            
            // First, mark as uploaded to prevent duplicate sends
            try {
                const updateResult = await pool.query(
                    'UPDATE announcements SET uploaded = true WHERE id = $1 AND uploaded = false',
                    [announcement.id]
                );
                console.log(`   [DB] Marked as uploaded (rows affected: ${updateResult.rowCount})`);
            } catch (dbError) {
                console.error(`   [DB ERROR] Failed to mark as uploaded: ${dbError.message}`);
                failedCount++;
                continue;
            }
            
            // Then send the email
            const emailResult = await sendEmail(announcement);
            
            if (emailResult.success) {
                console.log(`   [OK] Email sent successfully`);
                sentCount++;
            } else {
                console.error(`   [FAILED] ${emailResult.error}`);
                // Even if email fails, we don't revert uploaded status to avoid infinite retry
                failedCount++;
            }

            // Small delay between emails to avoid rate limiting
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        const endTime = new Date();
        const duration = ((endTime - startTime) / 1000).toFixed(2);
        console.log(`[Email Service] Completed in ${duration}s - Sent: ${sentCount}, Failed: ${failedCount}`);

    } catch (error) {
        console.error(`[Email Service] Error: ${error.message}`);
    } finally {
        isRunning = false;
    }
}

module.exports = {
    processUnsentAnnouncements
};