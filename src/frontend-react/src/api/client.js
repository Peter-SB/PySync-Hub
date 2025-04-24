import { backendUrl } from '../config';
const BASE_URL = backendUrl;

export async function request(url_path, options = {}) {
    const url = `${BASE_URL}${url_path}`;

    const opts = {
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        ...options,

        // stringify body if it's an object
        body: options.body && typeof options.body === 'object'
            ? JSON.stringify(options.body)
            : options.body,
    };

    const res = await fetch(url, opts);
    console.log('response: ', res.status, res.body);
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error('Error response:', err.message || res.statusText);
        throw new Error(err.message || res.statusText);
    }

    return res.json();
}