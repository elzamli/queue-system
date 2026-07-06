// Service Worker מינימלי - נדרש כדי לאפשר registration.showNotification()
// (כרום באנדרואיד דוחה את new Notification() הרגיל ודורש Service Worker)

self.addEventListener('install', () => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        self.clients.matchAll({ type: 'window' }).then((clients) => {
            if (clients.length > 0) {
                return clients[0].focus();
            }
        })
    );
});
