
//Inicialization of the map. The map is centered in Madrid, Spain
var mapa = L.map('map').setView([40.416775, -3.703790], 6); 

// Add the OpenStreetMap tiles to the map 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(mapa);

// Variable to store the reference to the layer of the route. It allows to remove the previous route when a new one is calculated
var currentRoute = null; 
var distributors = [];

function displayRoute(routeData) {
    if (currentRoute) {
        mapa.removeLayer(currentRoute);
    }

    currentRoute = L.geoJSON({
        "type": "LineString",
        "coordinates": routeData.routes[0].geometry.coordinates
    }).addTo(mapa);

    mapa.fitBounds(currentRoute.getBounds());
}

function moreInfo() {
    window.location.href = '/search/info_gas_station';
}

function displayDistributor(data) {
    distributors.forEach(function(marker) {
        mapa.removeLayer(marker);
    });

    distributors = [];

    var iconoBase = L.Icon.extend({
        options: {
            iconSize:     [25, 25]
            //iconAnchor:   [22, 94],
            //popupAnchor:  [-3, -76]
        }
    });

    tipo = "E"

    if (tipo == "E")
        var coloredIcon = new iconoBase({iconUrl: './static/img/green_icon.png'})
    else
        var coloredIcon = new iconoBase({iconUrl: './static/img/orange_icon.png'})

    data.coordinates.forEach(function(coord) {
        //var marker = L.marker([coord[0], coord[1]]).addTo(mapa);
        var marker = L.marker([coord[0], coord[1]], {icon: coloredIcon}).addTo(mapa);
        
        marker.on('click', function(e) {
            var lat= e.latlng.lat;
            var lon= e.latlng.lng;
            var url = '/search/get_distributor_info/' + lat + '/' + lon;

            //jQuery to make an AJAX request to the server
            $.get(url, function(response) {
                marker.bindPopup(response).openPopup();
            });
        });

        distributors.push(marker);
    });
}


function fetchAndDisplayRoute() {
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
                displayDistributor(data.distributors); 
            } else {
                alert('No se encontraron datos de ruta');
            }
        })
        .catch(error => {
            alert(error.message); 
        });
}


    