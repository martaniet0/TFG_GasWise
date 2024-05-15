// Variable to store the reference to the layer of the route. It allows to remove the previous route when a new one is calculated
var currentRoute = null; 
var distributors = [];


//Inicialization of the map. The map is centered in Madrid, Spain
var mapa = L.map('map').setView([40.416775, -3.703790], 6); 
localStorage.setItem('map', mapa); // Guarda el valor en localStorage

// Add the OpenStreetMap tiles to the map 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(mapa);




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

function displayDistributor(data, tipo, w, h) {
    distributors.forEach(function(marker) {
        mapa.removeLayer(marker);
    });

    distributors = [];

    var iconoBase = L.Icon.extend({
        options: {
            iconSize:     [w, h]
            //iconAnchor:   [22, 94],
            //popupAnchor:  [-3, -76]
        }
    });

    //tipo = "E"

    var coloredIcon = new iconoBase({iconUrl: tipo == "E" ? greenIconUrl : orangeIconUrl});

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





