// Service Worker - נדרש גם ל-registration.showNotification() וגם לקבלת Web Push אמיתי מהשרת

self.addEventListener('install', () => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

// מגיע מהשרת (send_push_notification ב-app.py) - עובד גם כשהטאב/הדפדפן סגורים
self.addEventListener('push', (event) => {
    let data = {};
    try {
        data = event.data ? event.data.json() : {};
    } catch (e) {
        data = { title: 'התראה', body: event.data ? event.data.text() : '' };
    }

    const title = data.title || '🔔 תורך הגיע!';
    const options = {
        body: data.body || '',
        tag: data.tag || 'queue-status',
        icon: data.icon || '/static/icon.png',
        badge: data.icon || '/static/icon.png',
        data: { url: data.url || '/my-status' }
    };

    event.waitUntil(
        self.registration.showNotification(title, options).then(() => {
            // אישור מסירה - מדווח לשרת שההתראה אכן הוצגה בפועל על המכשיר
            if (data.subscription_id) {
                return fetch('/api/push-displayed', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ subscription_id: data.subscription_id })
                }).catch(() => {
                    // אין רשת כרגע - לא קריטי, זה רק אישור מסירה best-effort
                });
            }
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/my-status';
    event.waitUntil(
        self.clients.matchAll({ type: 'window' }).then((clients) => {
            for (const client of clients) {
                if ('focus' in client) {
                    return client.focus();
                }
            }
            if (self.clients.openWindow) {
                return self.clients.openWindow(url);
            }
        })
    );
});
