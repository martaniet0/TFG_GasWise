//PROBLEMAS: REVISAR IS ON WATER PARA ISLAS CANARIAS Y BALEARES


//Inicialization of the map. The map is centered in Madrid, Spain
var map = L.map('map').setView([40.416775, -3.703790], 6); 

// Add the OpenStreetMap tiles to the map 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

// Variable to store the reference to the layer of the route. It allows to remove the previous route when a new one is calculated
var currentRoute = null; 


//API: https://nominatim.org/release-docs/latest/api/Search/
//Get the coordinates of a place
function get_coordinates(place_name, callback) {
    var nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${place_name}`;

    fetch(nominatimUrl)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                var lat = data[0].lat;
                var lon = data[0].lon;
                callback(lat, lon);
            } else {
                alert('No se encontraron coordenadas para el lugar.');
            }
        })
        .catch(error => console.error('Error al obtener las coordenadas:', error));
}

//API: https://nominatim.org/release-docs/latest/api/Reverse/
//Get the country code of the coordinates
function get_country(lat, lon, callback) {
    var geocodingUrl = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`;

    fetch(geocodingUrl)
        .then(response => response.json())
        .then(data => {
            callback(data.address.country_code);
        })
        .catch(error => {
            console.error('Error fetching the country:', error);
        });
}

//API: https://nominatim.org/release-docs/latest/api/Reverse/
//Get the CCAA code of the coordinates
function get_CCAA_code(lat, lon, callback) {
    var reverseGeocodeUrl = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`;

    fetch(reverseGeocodeUrl)
        .then(response => response.json())
        .then(data => {
            if (data && data.address) {
                callback(data.address['ISO3166-2-lvl4']);
            } else {
                callback(null);
            }
        })
        .catch(error => {
            console.error('Error fetching region code:', error);
            callback(null);
        });
}


//Chech if the route is trying to connect to locations connected by water, in that case return true 
function check_route_on_water(origin_lat, origin_lon, destination_lat, destination_lon, callback) {
    get_CCAA_code(origin_lat, origin_lon, function(origin_region) {
        get_CCAA_code(destination_lat, destination_lon, function(destination_region) {
            const not_peninsular = ['ES-CN', 'ES-CE', 'ES-ML', 'ES-IB']; 

            console.info(origin_region)
            console.info(destination_region)

            const is_origin_not_peninsular = not_peninsular.includes(origin_region);
            const is_destination_not_peninsular = not_peninsular.includes(destination_region);

            if (is_origin_not_peninsular && is_destination_not_peninsular) {
                if (origin_region === destination_region) {
                    callback(false); 
                } else if ((origin_region === 'ES-CE' && destination_region === 'ES-ML') || (origin_region === 'ES-ML' && destination_region === 'ES-CE')) {
                    callback(false); 
                } else {
                    callback(true); 
                }
            } else if (is_origin_not_peninsular || is_destination_not_peninsular) {
                callback(true);
            } else {
                callback(false);
            }
        });
    });
}

//!!!
function add_icon_to_map(lat, lon) {
    var customIcon = L.icon({
        iconUrl: 'static/img/img1.png', 
        iconSize: [20, 20], 
    });

    var marker = L.marker([lat, lon], {icon: customIcon});

    marker.addTo(map);
}


//API: https://project-osrm.org/docs/v5.5.1/api/#general-options
//Get the route between two places
function get_route() {
    var origin = document.getElementById('origin').value;
    var destination = document.getElementById('destination').value;

    get_coordinates(origin, function (origin_lat, origin_lon) {
        get_country(origin_lat, origin_lon, function (origin_country_code) {
            if (origin_country_code !== 'es') {
                alert('Error: El origen no está en España');
                return;
            }
    
            get_coordinates(destination, function (destination_lat, destination_lon) {
                get_country(destination_lat, destination_lon, function (destination_country_code) {
                    if (destination_country_code !== 'es') {
                        alert('Error: El destino no está en España');
                        return;
                    }

                    check_route_on_water(origin_lat, origin_lon, destination_lat, destination_lon, function(water_route) {
                        if (water_route) {
                            alert('Error: La ruta debe ser para coche. No puede atravesar el mar.');
                            return;
                        }
    
                    var osrmRouteUrl = `https://router.project-osrm.org/route/v1/driving/${origin_lon},${origin_lat};${destination_lon},${destination_lat}?overview=full&geometries=geojson`;
    
                    fetch(osrmRouteUrl)
                        .then(response => response.json())
                        .then(data => {
                            if (currentRoute) {
                                map.removeLayer(currentRoute);
                            }
                            currentRoute = L.geoJSON(data.routes[0].geometry).addTo(map);
                            map.fitBounds(currentRoute.getBounds());
                        })
                        .catch(error => {
                            console.error('Error fetching the route:', error);
                        });
                    });
                });
            });
        });
    });
}


