const BASE_URL = process.env.REACT_APP_BACKEND_URL;

export async function request(url_path, options = {}) {
    const url = `${BASE_URL}${url_path}`;

    const opts = {
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        ...options,
    };

    const res = await fetch(url, opts);

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || res.statusText);
    }

    return res.json();
}