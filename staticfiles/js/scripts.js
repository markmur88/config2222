import apiService from './apiService.js';

document.addEventListener("DOMContentLoaded", async function() {
    console.log("Dashboard cargado correctamente.");

    // Ejemplo: Obtener todas las cuentas
    try {
        const accounts = await apiService.getAccounts();
        console.log("Cuentas obtenidas:", accounts.data);
    } catch (error) {
        console.error("Error al obtener cuentas:", error);
    }

    // Ejemplo: Crear una nueva cuenta
    try {
        const newAccount = { name: "Cuenta Nueva", balance: 1000 };
        const createdAccount = await apiService.createAccount(newAccount);
        console.log("Cuenta creada:", createdAccount.data);
    } catch (error) {
        console.error("Error al crear cuenta:", error);
    }

    // Ejemplo: Actualizar una cuenta
    try {
        const updatedAccount = { name: "Cuenta Actualizada", balance: 2000 };
        const response = await apiService.updateAccount(1, updatedAccount); // ID de ejemplo: 1
        console.log("Cuenta actualizada:", response.data);
    } catch (error) {
        console.error("Error al actualizar cuenta:", error);
    }

    // Ejemplo: Eliminar una cuenta
    try {
        await apiService.deleteAccount(1); // ID de ejemplo: 1
        console.log("Cuenta eliminada.");
    } catch (error) {
        console.error("Error al eliminar cuenta:", error);
    }
});
