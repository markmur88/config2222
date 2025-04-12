document.addEventListener("DOMContentLoaded", async function() {
    const accountsList = document.getElementById("accounts-list");

    // Obtener y mostrar las cuentas
    const accounts = await getAccounts();
    if (accounts) {
        accounts.forEach(account => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${account.id}</td>
                <td>${account.name}</td>
                <td>${account.balance}</td>
                <td><button class="btn btn-info" onclick="viewAccount(${account.id})">Ver</button></td>
            `;
            accountsList.appendChild(row);
        });
    }
});

// Mostrar detalles de una cuenta
async function viewAccount(accountId) {
    const account = await getAccountById(accountId);
    if (account) {
        alert(`Cuenta: ${account.name}\nSaldo: ${account.balance}`);
    }
}
