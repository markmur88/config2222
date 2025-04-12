import axios from 'axios';

const axiosClient = axios.create({
  baseURL: '/dashboard', // Cambia la URL base según tu configuración
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el token de autorización si está disponible
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken'); // Cambia según cómo almacenes el token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default axiosClient;
