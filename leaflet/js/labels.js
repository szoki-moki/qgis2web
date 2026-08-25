var hideLabel = function(label) {
    label.labelObject.style.opacity = 0;
    label.labelObject.style.transition = 'opacity 0s';
};
var showLabel = function(label) {
    label.labelObject.style.opacity = 1;
    label.labelObject.style.transition = 'opacity 1s';
};
labelEngine = new labelgun.default(hideLabel, showLabel);

var id = 0;
var labels = [];
var totalMarkers = 0;
var labelResetRequest = null;
var pendingLabelMarkers = null;

function scheduleLabelReset(markers) {
    pendingLabelMarkers = markers;
    if (labelResetRequest !== null) {
        return;
    }

    var scheduleFrame = window.requestAnimationFrame || function(callback) {
        return window.setTimeout(callback, 16);
    };
    labelResetRequest = scheduleFrame(function() {
        var markersToReset = pendingLabelMarkers;
        labelResetRequest = null;
        pendingLabelMarkers = null;
        if (markersToReset) {
            resetLabels(markersToReset);
        }
    });
}

function resetLabels(markers) {
    labelEngine.reset();
    var i = 0;
    var mapRect = map.getContainer().getBoundingClientRect();
    for (var j = 0; j < markers.length; j++) {
        markers[j].eachLayer(function(label){
            addLabel(label, ++i, mapRect);
        });
    }
    labelEngine.update();
}

function addLabel(layer, id, mapRect) {

    var label = null;
    var tooltip = layer.getTooltip && layer.getTooltip();

    // Try tooltip first
    if (tooltip && tooltip._container) {
        label = tooltip._container;
    }
    // Fall back to divIcon
    else if (layer._icon) {
        label = layer._icon;
    }

    var mapContainer = map.getContainer();
    if (!label || !mapContainer.contains(label)) {
        return;
    }

    // We need the bounding rectangle of the label itself
    var rect = label.getBoundingClientRect();
    if (!rect.width || !rect.height) {
        return;
    }

    mapRect = mapRect || mapContainer.getBoundingClientRect();
    if (rect.right < mapRect.left || rect.left > mapRect.right ||
            rect.bottom < mapRect.top || rect.top > mapRect.bottom) {
        return;
    }

    // We convert the container coordinates (screen space) to Lat/lng
    var bottomLeft = map.containerPointToLatLng([
        rect.left - mapRect.left,
        rect.bottom - mapRect.top
    ]);
    var topRight = map.containerPointToLatLng([
        rect.right - mapRect.left,
        rect.top - mapRect.top
    ]);
    var boundingBox = {
        bottomLeft: [bottomLeft.lng, bottomLeft.lat],
        topRight: [topRight.lng, topRight.lat]
    };

    // Label collision calculation must not add or remove map layers.
    labelEngine.ingestLabel(
        boundingBox,
        id,
        parseInt(Math.random() * (5 - 1) + 1), // Weight
        label,
        "Test " + id,
        false
    );
}
