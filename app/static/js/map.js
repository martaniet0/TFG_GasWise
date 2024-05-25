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

// Add the geocoder to the map for autocomplete
//L.control.geocoder('pk.ba4ecf4dbb4d4cb89a54cb5d8d610e79').addTo(map);



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
        var marker = L.marker([coord[0], coord[1]], {icon: coloredIcon}).addTo(mapa);
        
        marker.on('click', function(e) {
            var lat= e.latlng.lat;
            var lon= e.latlng.lng;
            var url = '/search/get_distributor_info/' + lat + '/' + lon;

            $.get(url, function(response) {
                var content = "<b>Nombre:</b> " + response.Nombre + "<br>";

                if (response.Email) {
                    content += "<b>Email:</b> " + response.Email + "<br>";
                }
                if (response['Tipo_venta']) {
                    content += "<b>Tipo de venta:</b> " + response['Tipo_venta'] + "<br>";
                }
                if (response['Precio']){
                    content += "<b>Precio:</b> " + response['Precio'] + "<br>";
                }
                if (response.Horario) {
                    content += "<b>Horario:</b> " + response.Horario + "<br>";
                }
                if (response.Margen) {
                    content += "<b>Margen:</b> " + response.Margen + "<br>";
                }

                content += `<button class='btn btn-outline-secondary' onclick='moreInfo(${lat}, ${lon})'>Más información</button>`;
                marker.bindPopup(content).openPopup();
            });
        });

        distributors.push(marker);
    });
}





