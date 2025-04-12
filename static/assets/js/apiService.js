import axiosClient from './axiosClient.js';

// Servicios para interactuar con los endpoints
const apiService = {
    getAccounts: () => axiosClient.get('/accounts/accounts/'),
    getAccountById: (id) => axiosClient.get(`/accounts/accounts/${id}/`),
    createAccount: (data) => axiosClient.post('/accounts/accounts/', data), // Crear cuenta
    updateAccount: (id, data) => axiosClient.put(`/accounts/accounts/${id}/`, data), // Actualizar cuenta
    deleteAccount: (id) => axiosClient.delete(`/accounts/accounts/${id}/`), // Eliminar cuenta
    getTransactions: () => axiosClient.get('/transactions/'), // Obtener transacciones
    getTransfers: () => axiosClient.get('/transfers/'), // Obtener transferencias
    createTransfer: (data) => axiosClient.post('/transfers/', data), // Crear transferencia
};

export default apiService;
