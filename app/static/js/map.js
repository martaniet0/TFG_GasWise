//!!!PROBLEMAS: REVISAR IS ON WATER PARA ISLAS CANARIAS Y BALEARES

//Inicialization of the map. The map is centered in Madrid, Spain
var map = L.map('map').setView([40.416775, -3.703790], 6); 

// Add the OpenStreetMap tiles to the map 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

// Variable to store the reference to the layer of the route. It allows to remove the previous route when a new one is calculated
var currentRoute = null; 

function add_icon_to_map(lat, lon) {
    var customIcon = L.icon({
        iconUrl: 'static/img/img1.png', 
        iconSize: [20, 20], 
    });

    var marker = L.marker([lat, lon], {icon: customIcon});

    marker.addTo(map);
}


function displayRoute(routeData) {
    if (currentRoute) {
        map.removeLayer(currentRoute);
    }
    currentRoute = L.geoJSON(routeData.routes[0].geometry).addTo(map);
    map.fitBounds(currentRoute.getBounds());
}

function displayDistributor(data){
    data.coordinates.forEach(function(coord) {
        add_icon_to_map(coord[0], coord[1]);
    });
}
 
function fetchAndDisplayRoute() {
    fetch('/get_route_with_distributors')
        .then(response => response.json())
        .then(data => {
            if (data.route && data.distributors) {
                displayRoute(data.route);
                displayDistributor(data.distributors)
            } else {
                console.error('No se encontraron datos de ruta');
            }
        })
        .catch(error => {
            console.error('Error al obtener las rutas:', error);
        });
}
    

    