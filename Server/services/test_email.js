require('dotenv').config({ path: __dirname + '/../.env' });

// Standalone email test script for Brevo / Sib API
// Usage: set BREVO_API_KEY and EMAIL_TO (comma-separated) in .env, then:
// node Server/services/test_email.js

(async () => {
    const toRaw = process.env.EMAIL_TO || process.env.TEST_EMAIL;
    if (!toRaw) {
        console.error('ERROR: EMAIL_TO or TEST_EMAIL not set in environment');
        process.exit(1);
    }

    const recipients = toRaw.split(',').map(s => s.trim()).filter(Boolean).map(email => ({ email }));

    let SibApiV3Sdk;
    try {
        SibApiV3Sdk = require('@getbrevo/brevo');
        console.log('[TEST] Using @getbrevo/brevo SDK');
    } catch (e1) {
        try {
            SibApiV3Sdk = require('sib-api-v3-sdk');
            console.log('[TEST] Using sib-api-v3-sdk');
        } catch (e2) {
            console.error('ERROR: No supported SDK found. Install @getbrevo/brevo or sib-api-v3-sdk');
            process.exit(1);
        }
    }

    try {
        const apiInstance = new SibApiV3Sdk.TransactionalEmailsApi();
        // set api key (works for both SDK shapes)
        if (apiInstance.authentications && apiInstance.authentications['apiKey']) {
            apiInstance.authentications['apiKey'].apiKey = process.env.BREVO_API_KEY || process.env.SIB_API_KEY;
        } else if (SibApiV3Sdk.ApiClient && SibApiV3Sdk.ApiClient.instance) {
            // fallback for some SDK variants
            SibApiV3Sdk.ApiClient.instance.authentications['apiKey'].apiKey = process.env.BREVO_API_KEY || process.env.SIB_API_KEY;
        }

        const sendSmtpEmail = new SibApiV3Sdk.SendSmtpEmail();
        sendSmtpEmail.sender = { name: process.env.EMAIL_FROM_NAME || 'BSE BANKEX', email: process.env.EMAIL_FROM || (process.env.BREVO_SENDER_EMAIL || 'no-reply@example.com') };
        sendSmtpEmail.to = recipients;
        sendSmtpEmail.subject = `Test Email from BSE BANKEX - ${new Date().toLocaleString()}`;
        sendSmtpEmail.htmlContent = `<p>This is a <strong>test</strong> email sent at ${new Date().toISOString()}.</p>`;

        console.log('[TEST] Sending email to:', recipients.map(r => r.email).join(', '));
        const resp = await apiInstance.sendTransacEmail(sendSmtpEmail);
        console.log('[TEST] Send response:', resp);
        process.exit(0);
    } catch (err) {
        console.error('[TEST] Error sending test email:', err && err.message ? err.message : err);
        if (err && err.response) {
            try { console.error('Response body:', err.response.body || err.response); } catch (e) {}
        }
        process.exit(2);
    }
})();
