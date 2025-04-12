document.addEventListener('DOMContentLoaded', () => {
    const deleteButtons = document.querySelectorAll('.btn-danger');
    const editButtons = document.querySelectorAll('.btn-warning');

    deleteButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            if (!confirm('¿Estás seguro de que deseas eliminar esta cuenta?')) {
                event.preventDefault();
            }
        });
    });

    editButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            if (!confirm('¿Estás seguro de que deseas editar esta cuenta?')) {
                event.preventDefault();
            }
        });
    });

    // Configuración dinámica de la tabla
    const accountsTable = document.querySelector('#accounts-table');
    const accounts = JSON.parse(document.getElementById('accounts-data').textContent);

    const tableHeaders = `
        <tr>
            <th>Nombre</th>
            <th>Estado</th>
            <th>Saldo</th>
            <th>Moneda</th>
            <th>IBAN</th>
            <th>Tipo</th>
            <th>Principal</th>
            <th>Acciones</th>
        </tr>
    `;
    const tableRows = accounts.map(account => `
        <tr>
            <td>${account.name}</td>
            <td>${account.status}</td>
            <td>${account.balance}</td>
            <td>${account.currency}</td>
            <td>${account.iban}</td>
            <td>${account.get_type_display}</td>
            <td>${account.is_main ? 'Sí' : 'No'}</td>
            <td>
                <a href="/accounts/${account.id}/update/" class="btn btn-warning btn-sm">Editar</a>
                <a href="/accounts/${account.id}/delete/" class="btn btn-danger btn-sm">Eliminar</a>
            </td>
        </tr>
    `).join('');

    accountsTable.querySelector('thead').innerHTML = tableHeaders;
    accountsTable.querySelector('tbody').innerHTML = tableRows;
});
