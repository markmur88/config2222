//const API_BASE_URL = "https://tuapi.com/api"; 
const API_BASE_URL = "https://0.0.0.0:8000/dashboard/"; 

const axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`
    }
});

// Obtener lista de cuentas
async function getAccounts() {
    try {
        const response = await axiosInstance.get("/accounts");
        return response.data;
    } catch (error) {
        console.error("Error al obtener cuentas:", error);
        return null;
    }
}

// Obtener detalles de una cuenta por ID
async function getAccountById(accountId) {
    try {
        const response = await axiosInstance.get(`/accounts/${accountId}`);
        return response.data;
    } catch (error) {
        console.error("Error al obtener cuenta:", error);
        return null;
    }
}

// Login de usuario
async function loginUser(username, password) {
    try {
        const response = await axiosInstance.post("/auth/login", { username, password });
        if (response.data.token) {
            localStorage.setItem("token", response.data.token);
            window.location.href = "dashboard.html";
        }
    } catch (error) {
        alert("Usuario o contraseña incorrectos");
    }
}
