import { createRouter, createWebHistory } from 'vue-router';
import RequestsPage from '@/components/RequestsPage.vue';
import ConfigWizard from '@/components/ConfigWizard.vue';

// Define routes
const routes = [
    { path: '/requests', name: 'RequestsPage', component: RequestsPage },
    { path: '/', name: 'Home', component: ConfigWizard },
];

// Create and export the router
// The router will be initialized in main.js after the app is created and SUBPATH is known
export default function createAppRouter(subpath = '') {
    console.log(`Creating router with base path: ${subpath}`);
    return createRouter({
        history: createWebHistory(subpath),
        routes,
        // Make sure links are properly resolved with SUBPATH
        scrollBehavior(to, from, savedPosition) {
            if (savedPosition) {
                return savedPosition;
            } else {
                return { top: 0 };
            }
        }
    });
}
