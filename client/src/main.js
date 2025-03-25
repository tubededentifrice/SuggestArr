import { createApp } from 'vue';
import App from './App.vue';
import ToastPlugin from 'vue-toast-notification';
import 'vue-toast-notification/dist/theme-bootstrap.css';
import axios from 'axios';
import createAppRouter from './router';

// Get the SUBPATH from webpack define plugin or directly from the public path
// Vue CLI sets __webpack_public_path__ at runtime based on publicPath in vue.config.js
const subpath = window.__VUE_APP_SUBPATH__ || '';
console.log(`App initialized with SUBPATH: ${subpath || '/'}`);

// Create the app
const app = createApp(App);

// Create router with SUBPATH
const router = createAppRouter(subpath);
app.use(router);

// For debugging
app.config.globalProperties.$baseUrl = subpath;

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