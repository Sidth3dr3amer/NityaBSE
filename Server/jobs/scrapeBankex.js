const cron = require('node-cron');
const { spawn } = require('child_process');
const path = require('path');
const { processUnsentAnnouncements } = require('../services/emailService');

const SCRAPER_PATH = path.join(__dirname, '..', 'services', 'finalscraper.py');
const PYTHON_CMD = 'python'; // Use 'python3' on Linux/Mac if needed

let isRunning = false;
let isJobRunning = false;

function runScraper() {
    return new Promise((resolve, reject) => {
        if (isRunning) {
            console.log('[Scraper] Previous job still running, skipping...');
            resolve();
            return;
        }

        isRunning = true;
        const startTime = new Date();
        console.log(`\n[Scraper] Starting at ${startTime.toLocaleString()}`);

        const process = spawn(PYTHON_CMD, [SCRAPER_PATH], {
            cwd: path.join(__dirname, '..', 'services')
        });

        process.stdout.on('data', (data) => {
            console.log(`[Scraper] ${data.toString().trim()}`);
        });

        process.stderr.on('data', (data) => {
            console.error(`[Scraper Error] ${data.toString().trim()}`);
        });

        process.on('close', (code) => {
            isRunning = false;
            const endTime = new Date();
            const duration = ((endTime - startTime) / 1000).toFixed(2);
            
            if (code === 0) {
                console.log(`[Scraper] Completed successfully in ${duration}s`);
                resolve();
            } else {
                console.error(`[Scraper] Exited with code ${code} after ${duration}s`);
                resolve(); // Still resolve to continue with email service
            }
        });

        process.on('error', (err) => {
            isRunning = false;
            console.error(`[Scraper] Failed to start: ${err.message}`);
            reject(err);
        });
    });
}

async function runScraperAndEmail() {
    if (isJobRunning) {
        console.log('[Job] Previous scraper+email job still running, skipping...');
        return;
    }
    
    isJobRunning = true;
    console.log('\n========== JOB START ==========');
    
    try {
        // Run scraper first
        await runScraper();
        
        // Small delay to ensure DB commits are complete
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Then run email service
        await processUnsentAnnouncements();
    } catch (error) {
        console.error('[Job] Error:', error.message);
    } finally {
        isJobRunning = false;
        console.log('========== JOB END ==========\n');
    }
}

function startScheduler() {
    // Run every 5 minutes: "*/5 * * * *"
    // Cron format: minute hour day month day-of-week
    const job = cron.schedule('*/5 * * * *', () => {
        runScraperAndEmail();
    }, {
        scheduled: true,
        timezone: "Asia/Kolkata" // IST timezone for BSE
    });

    console.log('[Scheduler] BSE Bankex scraper + email service scheduled to run every 5 minutes');
    console.log('[Scheduler] Timezone: Asia/Kolkata (IST)');
    console.log('[Scheduler] Next run in 5 minutes or less...\n');

    // Run immediately on startup
    console.log('[Scheduler] Running initial scrape and email check...');
    runScraperAndEmail();

    return job;
}

// Manual run function for testing
function manualRun() {
    console.log('[Manual] Triggering scraper and email service manually...');
    runScraperAndEmail();
}

module.exports = { startScheduler, manualRun, runScraper };
