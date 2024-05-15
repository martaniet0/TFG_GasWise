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
    document.getElementById("listButton").style.display = "none"; // Ocultar listButton cuando se activa routeButton
}

function resetToInitial() {
    document.getElementById("destination")?.parentNode.remove(); // Elimina el campo de destino
    document.getElementById("nearestButton").style.display = "none"; // Oculta el botón Nearest
    document.getElementById("routeButton").style.display = "inline-block"; // Muestra el botón de ruta
    document.getElementById("searchButton").setAttribute("onclick", "fetchAndDisplayNearest(event)"); // Restablece la acción original del botón de búsqueda
    document.getElementById("listButton").style.display = "none"; // Ocultar listButton en reset
}

function fetchAndDisplayRoute(event) {
    event.preventDefault();
    // Retrieve values from input fields
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    
    // Check if the input fields are not empty
    if (!origin || !destination) {
        alert('Origen y destino son necesarios');
        return;
    }

    // Append the parameters to the URL
    const url = new URL('/search/get_route_with_distributors', window.location.origin);
    url.searchParams.append('origin', origin);
    url.searchParams.append('destination', destination);
    //!!!Encodear

    // Fetch the route using the updated URL with query parameters
    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.json();
        })
        .then(data => {
            if (data.route && data.distributors) {
                displayRoute(data.route);
                displayDistributor(data.distributors, data.tipo, 35, 35); 
            } else {
                alert('No se encontraron datos de ruta');
            }
        })
        .catch(error => {
            alert(error.message); 
        });
}

function fetchAndDisplayNearest(event) {
    event.preventDefault();
    // Retrieve values from input fields
    const origin = document.getElementById('origin').value;
    document.getElementById("listButton").style.display = "inline-block"; // Mostrar listButton al hacer clic en searchButton
    
    
    // Check if the input fields are not empty
    if (!origin) {
        alert('Origen necesario');
        return;
    }

    // Append the parameters to the URL
    const url = new URL('/search/get_nearest_distributors', window.location.origin);
    url.searchParams.append('origin', origin);
    //!!!Encodear

    // Fetch the route using the updated URL with query parameters
    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.json();
        })
        .then(data => {
            if (data.distributors) {
                mapa.setView([data.origin[0], data.origin[1]], 12); 
                displayDistributor(data.distributors, data.tipo, 50, 50); 
            } else {
                alert('No se encontraron distribuidores cercanos');
            }
        })
        .catch(error => {
            alert(error.message); 
        });
}

//Seleccionar: Gasolinera o Estación de recarga
function checkDistributorType(selectedId) {
    var gasolineraCheckbox = document.getElementById('gasolinera');
    var estacionRecargaCheckbox = document.getElementById('estacion_recarga');
    
    if (selectedId === 'gasolinera' && gasolineraCheckbox.checked) {
        estacionRecargaCheckbox.checked = false;
    } else if (selectedId === 'estacion_recarga' && estacionRecargaCheckbox.checked) {
        gasolineraCheckbox.checked = false;
    }
}