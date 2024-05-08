function enableDestinationInput() {
    const destinationInput = document.createElement("div");
    destinationInput.className = "form-group";
    destinationInput.innerHTML = `
        <label for="destination">Destino:</label>
        <input type="text" id="destination" class="form-control" placeholder="Introduce destino" required />
    `;

    document.querySelector(".input-group").appendChild(destinationInput);
    document.getElementById("routeButton").style.display = "none"; // Oculta el botón de ruta
    document.getElementById("nearestButton").style.display = "inline-block"; // Muestra el botón Nearest
    document.getElementById("searchButton").setAttribute("onclick", "fetchAndDisplayRoute(event)"); // Cambia la función que se llama al buscar
}

function resetToInitial() {
    document.getElementById("destination")?.parentNode.remove(); // Elimina el campo de destino
    document.getElementById("nearestButton").style.display = "none"; // Oculta el botón Nearest
    document.getElementById("routeButton").style.display = "inline-block"; // Muestra el botón de ruta
    document.getElementById("searchButton").setAttribute("onclick", "fetchAndDisplayNearest(event)"); // Restablece la acción original del botón de búsqueda
}