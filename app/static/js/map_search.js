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
    document.getElementById("searchButton").setAttribute("onclick", "fetchAndDisplayRoute(event)"); 
    document.getElementById("filterSearchButton").setAttribute("onclick", "fetchAndDisplayRoute(event)");
    document.getElementById("listButton").style.display = "none"; 
}

function resetToInitial() {
    document.getElementById("destination")?.parentNode.remove(); // Elimina el campo de destino
    document.getElementById("nearestButton").style.display = "none"; // Oculta el botón Nearest
    document.getElementById("routeButton").style.display = "inline-block"; // Muestra el botón de ruta
    document.getElementById("searchButton").setAttribute("onclick", "fetchAndDisplayNearest(event)"); // Restablece la acción original del botón de búsqueda
    document.getElementById("filterSearchButton").setAttribute("onclick", "fetchAndDisplayNearest(event)");
    document.getElementById("listButton").style.display = "none"; // Ocultar listButton en reset
}

function toggleVisibility(isChecked, isGasolinera) {
    var servicios = document.getElementById('servicios');
    var marcas = document.getElementById('marcas');
    var combustibles = document.getElementById('combustibles');
    var conectores = document.getElementById('conectores');

    if (isGasolinera) {
        if (isChecked) {
            // Mostrar los divs relacionados con gasolineras
            servicios.style.display = 'block';
            marcas.style.display = 'block';
            combustibles.style.display = 'block';
            // Ocultar el div de conectores
            conectores.style.display = 'none';
        } else {
            // Si se desmarca gasolinera, ocultar estos divs
            servicios.style.display = 'none';
            marcas.style.display = 'none';
            combustibles.style.display = 'none';
        }
    } else {
        if (isChecked) {
            // Mostrar el div de conectores
            conectores.style.display = 'block';
            // Ocultar los divs relacionados con gasolineras
            servicios.style.display = 'none';
            marcas.style.display = 'none';
            combustibles.style.display = 'none';
        } else {
            // Si se desmarca estación de recarga, ocultar el div de conectores
            conectores.style.display = 'none';
        }
    }
}

function noChecked() {
    //tipo distribuidora
    document.getElementById('gasolinera').checked = false;
    document.getElementById('estacion_recarga').checked = false;
    //servicios
    document.getElementById('cafeteria').checked = false;
    document.getElementById('hospedaje').checked = false;
    document.getElementById('lavado_coches').checked = false;
    document.getElementById('lavado_camiones').checked = false;
    document.getElementById('parking_camiones').checked = false;
    document.getElementById('cambiapaniales').checked = false;
    document.getElementById('duchas').checked = false;
    document.getElementById('supermercado').checked = false;
    document.getElementById('amazon_locker').checked = false;
    document.getElementById('citypaq').checked = false;
    document.getElementById('vaciado_aguas_negras').checked = false;
    document.getElementById('estacion_accesible').checked = false;
    //tipo combustible
    document.getElementById('biodiesel').checked = false;
    document.getElementById('bioetanol').checked = false;
    document.getElementById('gas_comprimido').checked = false;
    document.getElementById('gas_licuado').checked = false;
    document.getElementById('gas_petroleo').checked = false;
    document.getElementById('gasoleoA').checked = false;
    document.getElementById('gasoleoB').checked = false;
    document.getElementById('gasoleo_premium').checked = false;
    document.getElementById('gasolina95_E10').checked = false;
    document.getElementById('gasolina95_E5').checked = false;
    document.getElementById('gasolina95_E5_premium').checked = false;
    document.getElementById('gasolina98_E10').checked = false;
    document.getElementById('gasolina98_E5').checked = false;
    document.getElementById('hidrogeno').checked = false;
    //tipo de conector
    document.getElementById('ccs1').checked = false;
    document.getElementById('ccs2').checked = false;
    document.getElementById('chademo').checked = false;
    document.getElementById('tipo2socket').checked = false;
    document.getElementById('tipo2thetered').checked = false;
    document.getElementById('3p').checked = false;
    document.getElementById('5p').checked = false;
    document.getElementById('7/4p').checked = false;
    document.getElementById('7p').checked = false;
    document.getElementById('teslaS/X').checked = false;
    document.getElementById('NACS').checked = false;
    document.getElementById('J1772').checked = false;
    document.getElementById('AS/NZS3112').checked = false;
    document.getElementById('60309').checked = false;
    document.getElementById('Europlug').checked = false;
    document.getElementById('Commando').checked = false;
    //marca gasolinera
    document.getElementById('repsol').checked = false;
    document.getElementById('cepsa').checked = false;
    document.getElementById('bp').checked = false;
    document.getElementById('shell').checked = false;
    document.getElementById('galp').checked = false;
};

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function fetchAndDisplayRoute(event) {
    event.preventDefault();

    showLoading();

    document.getElementById("selectButton").style.display = "inline-block";

    var checkedInputs = []; 
    document.querySelectorAll('.form-check-input').forEach(function(input) {
        if (input.checked) {
            checkedInputs.push(input.id); 
        }
    });

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

    // Usar un contador como clave
    if (checkedInputs.length != 0){
        let counter = 2;
        //El origen y el destino no se tienen en cuenta
        for (let i = 0; i < checkedInputs.length; i++) {
            url.searchParams.append('param' + counter, encodeURIComponent(checkedInputs[i]));
            counter++;
        }
    } 

    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.json();
        })
        .then(data => {
            if (data.route && data.distributors) {
                var filtersDiv = document.querySelector('.filters');
                filtersDiv.classList.remove('show');
                displayRoute(data.route);
                displayDistributor(data.distributors, data.tipo, 35, 42); 
                hideLoading();
                //marco como cheked en filtrados el tipo de distribuidora que se muestra para que salgan los filtros acordes
                if (data.tipo == "G"){                    
                    document.getElementById('conectores').style.display = "none";
                    document.getElementById('servicios').style.display = "block";
                    document.getElementById('marcas').style.display = "block";
                    document.getElementById('combustibles').style.display = "block";
                }else{
                    document.getElementById('conectores').style.display = "block";
                    document.getElementById('servicios').style.display = "none";
                    document.getElementById('marcas').style.display = "none";
                    document.getElementById('combustibles').style.display = "none";
                }
            } else {
                alert('No se encontraron datos de ruta');
            }
        })
        .catch(error => {
            alert(error.message); 
        });
}

function fetchAndDisplayNearest(event, additionalOrigin,  ...otherParams) {
    event.preventDefault();

    showLoading();

    document.getElementById("listButton").style.display = "inline-block";
    document.getElementById("selectButton").style.display = "inline-block";

    var checkedInputs = []; 
    document.querySelectorAll('.form-check-input').forEach(function(input) {
        if (input.checked) {
            checkedInputs.push(input.id); 
        }
    });

    origin = document.getElementById('origin').value;


    if (!origin) {
        alert('Origen necesario');
        return;
    }
    
    const url = new URL('/search/get_nearest_distributors', window.location.origin);
    url.searchParams.append('origin', origin);

    // Usar un contador como clave
    if (checkedInputs.length != 0){
        let counter = 1;
        //El origen no se tiene en cuenta
        for (let i = 0; i < checkedInputs.length; i++) {
            url.searchParams.append('param' + counter, encodeURIComponent(checkedInputs[i]));
            counter++;
        }
    } 

    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error); });
            }
            return response.json();
        })
        .then(data => {
            if (data.distributors) {
                var filtersDiv = document.querySelector('.filters');
                filtersDiv.classList.remove('show');
                mapa.setView([data.origin[0], data.origin[1]], 12);
                displayDistributor(data.distributors, data.tipo, 50, 60);
                hideLoading();
                //marco como cheked en filtrados el tipo de distribuidora que se muestra para que salgan los filtros acordes
                if (data.tipo == "G"){                    
                    document.getElementById('conectores').style.display = "none";
                    document.getElementById('servicios').style.display = "block";
                    document.getElementById('marcas').style.display = "block";
                    document.getElementById('combustibles').style.display = "block";
                }else{
                    document.getElementById('conectores').style.display = "block";
                    document.getElementById('servicios').style.display = "none";
                    document.getElementById('marcas').style.display = "none";
                    document.getElementById('combustibles').style.display = "none";
                }
            } else {
                alert('No se encontraron distribuidores cercanos');
            }
        })
        .catch(error => {
            alert(error.message);
        });
}

//Seleccionar: Gasolinera o Estación de recarga pero en nigún caso las dos opciones
function checkDistributorType(selectedId) {
    var gasolineraCheckbox = document.getElementById('gasolinera');
    var estacionRecargaCheckbox = document.getElementById('estacion_recarga');
    
    if (selectedId === 'gasolinera' && gasolineraCheckbox.checked) {
        estacionRecargaCheckbox.checked = false;
    } else if (selectedId === 'estacion_recarga' && estacionRecargaCheckbox.checked) {
        gasolineraCheckbox.checked = false;
    }
}

//Activar el botón de filtrado
function filtersSearch(origin_param) {
    // Llama a fetchAndDisplayNearest y pasa todos los inputs seleccionados
    var checkedInputs = []; // Aquí guardaremos los inputs seleccionados

    // Selecciona todos los checkbox y verifica cuáles están marcados
    document.querySelectorAll('.form-check-input').forEach(function(input) {
        if (input.checked) {
            checkedInputs.push(input.id); 
        }
    });

    console.log("Param" + origin_param)
    origin=origin_param;

    fetchAndDisplayNearest({preventDefault: () => {}}, origin, ...checkedInputs);

}

//Llama a la ruta que muestra la lista de distribuidores
function getDistributorsList(){
    window.location.href = '/search/get_distributors_list';
}

//Llama a la ruta que muestra más información de una gasolinera
function moreInfo() {
    window.location.href = '/search/info_distributor';
}