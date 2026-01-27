Database Cleanup Automator
What I have done
Immediate Cleanup: I ran a cleanup command that deleted 419 old log entries instantly, freeing up space.
Safety Logic: The system now only keeps logs for 48 hours. Anything older is safe to delete because we store daily summaries separately.
Automation Endpoint: I created a special URL that triggers this cleanup securely.
How to Automate (Free)
Since Render's "Free Tier" doesn't support Background Workers (Cron), you can use a free "Uptime Monitor" logic to trigger the cleanup every day.

Step 1: Get your Secret Key
In 
core/views.py
, the default key is configured as default-cleanup-key-123. You can change this in your environment variables as CLEANUP_SECRET_KEY.

Step 2: Set up the Trigger
Go to Cron-Job.org (Free) or UptimeRobot (Free).
Create a new HTTP Request / Monitor.
URL: https://your-app-name.onrender.com/system/cleanup/?key=default-cleanup-key-123
Schedule: Once every day (e.g., every 24 hours).
That's it! This external service will "ping" your website once a day, and your website will effectively scrub itself clean.