/* ============================================================
   SafeRoute — Leaflet / OpenStreetMap module
   CPU4106 Level 4 Computing Group Project

   Used by:
     home.html    -> initPreviewMap()   (hero snapshot)
     map.html     -> initSafetyMap()    (full community safety map)
     routes.html  -> initRouteMap()     (route corridor comparison)
   ============================================================ */

var SafeRouteMap = (function () {
    'use strict';

    var COLORS = {
        'Poor Lighting': '#F59E0B',
        'Pothole': '#B45309',
        'Flooding': '#2563EB',
        'Road Damage': '#EF4444',
        'Suspicious Activity': '#7C3AED',
        'Anti-Social Behaviour': '#BE185D',
        'Unsafe Crossing': '#0F766E'
    };

    var DEMO_REPORTS = [
        { type: 'Poor Lighting', location: 'Wembley Park Station', lat: 51.5634, lng: -0.2796, date: '18 Oct 2026' },
        { type: 'Flooding', location: 'High Road Wembley', lat: 51.5522, lng: -0.2952, date: '20 Oct 2026' },
        { type: 'Unsafe Crossing', location: 'North Circular Road', lat: 51.5481, lng: -0.2683, date: '11 Oct 2026' },
        { type: 'Suspicious Activity', location: 'College Road, Wembley', lat: 51.5576, lng: -0.2897, date: '14 Oct 2026' }
    ];

    function markerIcon(type) {
        var color = COLORS[type] || '#64748B';
        return L.divIcon({
            className: '',
            html: '<span style="display:block;width:18px;height:18px;border-radius:50% 50% 50% 0;' +
                  'transform:rotate(-45deg);background:' + color + ';border:2.5px solid #fff;' +
                  'box-shadow:0 2px 6px rgba(15,23,42,0.3);"></span>',
            iconSize: [18, 18],
            iconAnchor: [9, 18],
            popupAnchor: [0, -16]
        });
    }

    function popupHtml(report) {
        return '<div style="font-weight:700;color:#1E293B;">' + report.type + '</div>' +
               '<div style="color:#64748B;font-size:12px;">' + report.location + '</div>' +
               '<div style="color:#64748B;font-size:12px;">Reported ' + (report.date || '') + '</div>';
    }

    function baseMap(elementId, center, zoom) {
        var map = L.map(elementId, { scrollWheelZoom: true }).setView(center, zoom || 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        return map;
    }

    function addMarker(map, report, openPopup) {
        var marker = L.marker([report.lat, report.lng], { icon: markerIcon(report.type), title: report.location })
            .addTo(map)
            .bindPopup(popupHtml(report));
        if (openPopup) { marker.openPopup(); }
        return marker;
    }

    /* ---------------------------------------------------------- hero map */
    function initPreviewMap(elementId, center) {
        var host = document.getElementById(elementId);
        if (!host) { return; }
        var map = baseMap(elementId, center || [51.5565, -0.2865], 14);
        DEMO_REPORTS.forEach(function (report, index) {
            addMarker(map, report, index === 0);
        });
    }

    /* -------------------------------------------------- community safety map */
    function initSafetyMap(elementId, center) {
        var host = document.getElementById(elementId);
        if (!host) { return; }

        var data = [];
        var json = document.getElementById('sr-reports');
        if (json) {
            try { data = JSON.parse(json.textContent) || []; } catch (error) { data = []; }
        }

        var map = baseMap(elementId, center || [51.5565, -0.2865], 14);
        var markers = {};

        if (data.length === 0) {
            DEMO_REPORTS.forEach(function (report) { addMarker(map, report, false); });
        } else {
            data.forEach(function (row) {
                markers[row.location + '|' + row.id] = addMarker(
                    map,
                    { type: row.type, location: row.location, lat: row.lat, lng: row.lng, date: row.date },
                    false
                );
            });
            var points = data.map(function (row) { return [row.lat, row.lng]; });
            if (points.length > 1) { map.fitBounds(points, { padding: [50, 50] }); }
        }

        /* Sidebar selection zooms to the matching marker */
        var items = document.querySelectorAll('#recentHazards .sr-map-list-item');
        items.forEach(function (button) {
            button.addEventListener('click', function () {
                var location = button.getAttribute('data-location');
                Object.keys(markers).forEach(function (key) {
                    if (key.indexOf(location + '|') === 0) {
                        var marker = markers[key];
                        map.flyTo(marker.getLatLng(), 16, { duration: 0.6 });
                        marker.openPopup();
                    }
                });
            });
        });

        setTimeout(function () { map.invalidateSize(); }, 200);
    }

    /* --------------------------------------------------------- route map */
    function initRouteMap(elementId, options) {
        var host = document.getElementById(elementId);
        if (!host || !options) { return; }

        var map = baseMap(elementId, options.start, 14);

        L.polyline([options.start, options.end], {
            color: '#10B981', weight: 4, dashArray: '9 9', opacity: 0.9
        }).addTo(map);

        L.circleMarker(options.start, {
            radius: 8, color: '#fff', weight: 3, fillColor: '#2563EB', fillOpacity: 1
        }).addTo(map).bindPopup('<div style="font-weight:700;">Start</div>' + options.startLabel);

        L.circleMarker(options.end, {
            radius: 8, color: '#fff', weight: 3, fillColor: '#10B981', fillOpacity: 1
        }).addTo(map).bindPopup('<div style="font-weight:700;">Destination</div>' + options.endLabel);

        (options.incidents || []).forEach(function (row) {
            var coords = null;
            var point = (window.SR_LOCATIONS || {})[row.Location];
            if (point) { coords = point; }
            if (!coords) { coords = [51.5565, -0.2865]; }
            addMarker(map, {
                type: row.IncidentType, location: row.Location,
                lat: coords[0], lng: coords[1],
                date: row.DateReported
            }, false);
        });

        map.fitBounds([options.start, options.end], { padding: [60, 60] });
        setTimeout(function () { map.invalidateSize(); }, 200);
    }

    return {
        initPreviewMap: initPreviewMap,
        initSafetyMap: initSafetyMap,
        initRouteMap: initRouteMap
    };
})();
