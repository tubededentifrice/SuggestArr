import { createApp } from 'vue';
import App from './App.vue';
import ToastPlugin from 'vue-toast-notification';
import 'vue-toast-notification/dist/theme-bootstrap.css';
import axios from 'axios';
import createAppRouter from './router';

// Get the SUBPATH from webpack define plugin
const subpath = window.__VUE_APP_SUBPATH__ || '';

// Create the app
const app = createApp(App);

// Create router with SUBPATH
const router = createAppRouter(subpath);
app.use(router);

// Configure axios
if (process.env.NODE_ENV === 'development') {
    // For development, use localhost with port
    axios.defaults.baseURL = 'http://localhost:5000' + subpath;
} else {
    // For production, use relative URLs with subpath
    axios.defaults.baseURL = subpath;
}

// Make subpath available globally
app.config.globalProperties.$subpath = subpath;

// Configure toast notifications
const options = {
    position: 'top-right',
    timeout: 5000,
    closeOnClick: false,
    pauseOnHover: true,
    draggable: false,
    showCloseButtonOnHover: true,
    closeButton: 'button',
    icon: true,
    rtl: false,
};

app.use(ToastPlugin, options);
app.mount('#app');