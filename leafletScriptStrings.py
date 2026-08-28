import re
import os
import traceback
from urllib.parse import parse_qs
from qgis.PyQt.QtCore import QSize, QDateTime
from qgis.core import (QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsMapLayer,
                       QgsSymbolLayerUtils,
                       QgsSvgMarkerSymbolLayer,
                       QgsMessageLog,
                       Qgis,
                       QgsWkbTypes)
from qgis2web.utils import scaleToZoom, safeName

def jsonScript(layer):
    json = """
        <script src="data/{layer}.js\"></script>""".format(layer=layer)
    return json


def scaleDependentLayerScript(layer, layerName, cluster):
    max = layer.minimumScale()
    min = layer.maximumScale()
    if cluster:
        layerType = "cluster"
    else:
        layerType = "layer"
    scaleDependentLayer = """
            if (map.getZoom() <= {min} && map.getZoom() >= {max}) {{
                map.addLayer({layerType}_{layerName});
            }} else if (map.getZoom() > {min} || map.getZoom() < {max}) {{
                map.removeLayer({layerType}_{layerName});
            }}""".format(min=scaleToZoom(min), max=scaleToZoom(max),
                         layerName=layerName, layerType=layerType)
    return scaleDependentLayer


def scaleDependentLabelScript(layer, layerName):
    if layer.labeling() is not None:
        labelling = layer.labeling().settings()
        sv = labelling.scaleVisibility
        if sv:
            min = scaleToZoom(labelling.minimumScale)
            max = scaleToZoom(labelling.maximumScale)
            scaleDependentLabel = """
                if (map.hasLayer(layer_%(layerName)s)) {
                    if (map.getZoom() <= %(min)d && map.getZoom() >= %(max)d) {
                        layer_%(layerName)s.eachLayer(function (layer) {
                            layer.openTooltip();
                        });
                    } else {
                        layer_%(layerName)s.eachLayer(function (layer) {
                            layer.closeTooltip();
                        });
                    }
                }""" % {"min": min, "max": max, "layerName": layerName}
            return scaleDependentLabel
        else:
            return ""
    else:
        return ""


def scaleDependentScript(layers):
    scaleDependent = """
        map.on("zoomend", function(e) {"""
    scaleDependent += layers
    scaleDependent += """
        });"""
    scaleDependent += layers
    return scaleDependent


def highlightScript(highlight, popupsOnHover, highlightFill):
    highlightScript = """
        var highlightLayer;
        function highlightFeature(e) {
            highlightLayer = e.target;"""
    if highlight:
        highlightScript += """

            if (e.target.feature.geometry.type === 'LineString' || e.target.feature.geometry.type === 'MultiLineString') {
              highlightLayer.setStyle({
                color: '""" + highlightFill + """',
              });
            } else {
              highlightLayer.setStyle({
                fillColor: '""" + highlightFill + """',
                fillOpacity: 1
              });
            }"""
    if popupsOnHover:
        highlightScript += """
            highlightLayer.openPopup();"""
    highlightScript += """
        }"""
    return highlightScript


def crsScript(crsAuthId, crsProj4):
    crs = """
        var crs = new L.Proj.CRS('{crsAuthId}', '{crsProj4}', {{
            resolutions: [2800, 1400, 700, 350, """.format(crsAuthId=crsAuthId,
                                                           crsProj4=crsProj4)
    crs += """175, 84, 42, 21, 11.2, 5.6, 2.8, 1.4, 0.7, 0.35, 0.14, 0.07],
        });"""
    return crs


def mapScript(extent, matchCRS, crsAuthId, maxZoom, minZoom, bounds):
    map = """
        var map = L.map('map', {"""
    if matchCRS and crsAuthId != 'EPSG:4326':
        map += """
            crs: crs,
            continuousWorld: false,
            worldCopyJump: false, """
    map += """
            zoomControl:false, maxZoom:""" + str(maxZoom)
    map += """, minZoom:""" + str(minZoom) + """
        })"""
    if extent == "Canvas extent":
        map += """.fitBounds(""" + bounds + """);"""
    map += """
        var hash = new L.Hash(map);"""
    map += """
        map.attributionControl.setPrefix('<a href="""
    map += """"https://github.com/qgis2web/qgis2web" target="_blank">"""
    map += """qgis2web</a> &middot; """
    map += """<a href="https://leafletjs.com" title="A JS library """
    map += """for interactive maps">Leaflet</a> &middot; """
    map += """<a href="https://qgis.org">QGIS</a>');"""
    map += """
        var autolinker = new Autolinker"""
    map += "({truncate: {length: 30, location: 'smart'}});"
    map += lazyPopupRuntime()

    return map


def lazyPopupRuntime():
    """Client-side runtime that defers all popup work until a popup is opened.

    Building popup HTML for every feature up-front (string building +
    autolinker + an innerHTML parse per feature) is what makes layers with a
    few thousand features unusable. Everything below is only executed for the
    feature whose popup is actually opened, and media inside that popup is
    only fetched once it scrolls into view.
    """
    runtime = """
        // ---- lazy popup runtime -------------------------------------------
        // Images/audio/video referenced by a popup are only requested once the
        // popup is open and the element is (close to) visible.
        var lazyMediaObserver = ('IntersectionObserver' in window) ?
            new IntersectionObserver(function(entries, observer) {
                for (var i = 0; i < entries.length; i++) {
                    if (entries[i].isIntersecting) {
                        observer.unobserve(entries[i].target);
                        loadLazyMedia(entries[i].target);
                    }
                }
            }, {rootMargin: '200px'}) : null;

        // Several images finishing at once should cause one relayout, not one
        // per image.
        var pendingPopupUpdates = [];
        function flushPopupUpdates() {
            var popups = pendingPopupUpdates;
            pendingPopupUpdates = [];
            for (var i = 0; i < popups.length; i++) {
                if (popups[i].isOpen()) {
                    popups[i].update();
                }
            }
        }

        function schedulePopupUpdate(popup) {
            if (!popup || !popup.isOpen || !popup.isOpen()) {
                return;
            }
            if (pendingPopupUpdates.indexOf(popup) !== -1) {
                return;
            }
            if (!pendingPopupUpdates.length) {
                window.requestAnimationFrame(flushPopupUpdates);
            }
            pendingPopupUpdates.push(popup);
        }

        function onLazyMediaSettled(e) {
            var el = e.currentTarget;
            el.removeEventListener('load', onLazyMediaSettled);
            el.removeEventListener('error', onLazyMediaSettled);
            el.classList.remove('lazy-pending');
            if (e.type === 'error') {
                el.classList.add('lazy-error');
            }
            schedulePopupUpdate(el._lazyPopup);
        }

        function loadLazyMedia(el) {
            var src = el.getAttribute('data-lazy-src');
            if (!src) {
                return;
            }
            el.removeAttribute('data-lazy-src');
            el.addEventListener('load', onLazyMediaSettled);
            el.addEventListener('error', onLazyMediaSettled);
            el.src = src;
        }

        // Turn <img data-lazy-src> placeholders into the right media element.
        // Nothing is fetched here - only the tag type is decided.
        function prepareLazyMedia(container) {
            var placeholders = container.querySelectorAll('img[data-lazy-src]');
            for (var i = placeholders.length - 1; i >= 0; i--) {
                var el = placeholders[i];
                var src = el.getAttribute('data-lazy-src');
                var media = null;
                if (/\\.(mp3|wav|aac|m4a|flac)$/i.test(src)) {
                    media = document.createElement('audio');
                } else if (/\\.(mp4|webm|ogg|ogv|mov)$/i.test(src)) {
                    media = document.createElement('video');
                }
                if (media) {
                    media.controls = true;
                    media.preload = 'none';
                    media.src = src;
                    media.className = 'popup-media';
                    el.parentNode.replaceChild(media, el);
                } else {
                    el.className = (el.className ? el.className + ' ' : '') +
                        'popup-media lazy-pending';
                    el.setAttribute('loading', 'lazy');
                    el.setAttribute('decoding', 'async');
                }
            }
        }

        // Build the popup DOM once, on demand. Returns a detached node, so no
        // network request is triggered until the node is attached and seen.
        function buildPopupNode(content, feature) {
            var container = document.createElement('div');
            container.innerHTML = content;
            // remove popup's row if "visible-with-data" and there is no data
            var rows = container.querySelectorAll('tr');
            for (var i = 0; i < rows.length; i++) {
                var td = rows[i].querySelector('td.visible-with-data');
                var key = td ? td.id : '';
                if (td && feature.properties[key] == null) {
                    rows[i].parentNode.removeChild(rows[i]);
                }
            }
            prepareLazyMedia(container);
            return container;
        }

        // Returned to bindPopup(): Leaflet calls it the first time the popup
        // is opened, and the built node is cached for subsequent openings.
        function lazyPopupContent(feature, contentBuilder) {
            var node = null;
            return function() {
                if (node === null) {
                    node = buildPopupNode(contentBuilder(feature), feature);
                }
                return node;
            };
        }

        // One global handler instead of a listener per feature.
        map.on('popupopen', function(e) {
            var node = e.popup._contentNode;
            if (!node) {
                return;
            }
            if (node.querySelector('.popup-media')) {
                node.classList.add('media');
            } else {
                node.classList.remove('media');
            }
            var pending = node.querySelectorAll('img[data-lazy-src]');
            for (var i = 0; i < pending.length; i++) {
                pending[i]._lazyPopup = e.popup;
                if (lazyMediaObserver) {
                    lazyMediaObserver.observe(pending[i]);
                } else {
                    loadLazyMedia(pending[i]);
                }
            }
        });

        // Kept for backwards compatibility with hand-edited exports.
        function removeEmptyRowsFromPopupContent(content, feature) {
            return buildPopupNode(content, feature).innerHTML;
        }
    """
    return runtime

def addZoomControl():
    zoomControlScript = """
        var zoomControl = L.control.zoom({
            position: 'topleft'
        }).addTo(map);
        """
    return zoomControlScript

def addLocateControl(locate):
    if not locate:
        return "" 
    locateScript = """
        L.control.locate({locateOptions: {maxZoom: 19}}).addTo(map);
        """
    return locateScript

def addMeasureControl(measure):
    if measure == "None":
        return ""    
    if measure == "Imperial":
        options = """{
            position: 'topleft',
            primaryLengthUnit: 'feet',
            secondaryLengthUnit: 'miles',
            primaryAreaUnit: 'sqfeet',
            secondaryAreaUnit: 'sqmiles'
        }"""
    else:
        options = """{
            position: 'topleft',
            primaryLengthUnit: 'meters',
            secondaryLengthUnit: 'kilometers',
            primaryAreaUnit: 'sqmeters',
            secondaryAreaUnit: 'hectares'
        }"""    
    measureScript = """
        var measureControl = new L.Control.Measure(%s);
        measureControl.addTo(map);
        document.getElementsByClassName('leaflet-control-measure-toggle')[0].innerHTML = '';
        document.getElementsByClassName('leaflet-control-measure-toggle')[0].className += ' fas fa-ruler';
        """ % options   
    return measureScript

def featureGroupsScript():
    featureGroups = """
        var bounds_group = new L.featureGroup([]);"""
    return featureGroups


def extentScript(extent, restrictToExtent):
    layerOrder = """
        function setBounds() {"""
    if extent == 'Fit to vector layers extent':
        layerOrder += """
            if (bounds_group.getLayers().length) {
                map.fitBounds(bounds_group.getBounds());
            }"""
    if restrictToExtent:
        layerOrder += """
            map.setMaxBounds(map.getBounds());
            map.setMinZoom(map.getZoom());"""
    layerOrder += """
        }"""
    return layerOrder


def popupContentScript(safeLayerName, table):
    """Emit the per-layer popup HTML builder.

    It is a plain function so it can stay uncalled until a popup is opened.
    """
    popupContent = """
        function getPopupContent_{safeLayerName}(feature) {{
            return {table};
        }}""".format(safeLayerName=safeLayerName, table=table)
    return popupContent


def popFuncsScript(safeLayerName):
    popFuncs = """
            layer.bindPopup(
                lazyPopupContent(feature, getPopupContent_{safeLayerName}),
                {{ maxHeight: 400 }});""".format(safeLayerName=safeLayerName)
    return popFuncs


def popupScript(safeLayerName, popFuncs, highlight, popupsOnHover):
    popup = """
        function pop_{safeLayerName}""".format(safeLayerName=safeLayerName)
    popup += "(feature, layer) {"
    if highlight or popupsOnHover:
        popup += """
            layer.on({
                mouseout: function(e) {"""
        if highlight:
            popup += """
                    for (var i in e.target._eventParents) {
                        if (typeof e.target._eventParents[i].resetStyle === 'function') {
                            e.target._eventParents[i].resetStyle(e.target);
                        }
                    }"""
        if popupsOnHover:
            popup += """
                    if (typeof layer.closePopup == 'function') {
                        layer.closePopup();
                    } else {
                        layer.eachLayer(function(feature){
                            feature.closePopup()
                        });
                    }"""
        popup += """
                },
                mouseover: highlightFeature,
            });"""
    if popFuncs:
        popup += """{popFuncs}
        """.format(popFuncs=popFuncs)
    popup += "}"
    return popup


def iconLegend(symbol, catr, outputProjectFileName, layerName, catLegend, cnt):
    if isinstance(symbol.symbolLayer(0), QgsSvgMarkerSymbolLayer):
            iconSize = int((symbol.size() * 4) + 5)
    else:
        iconSize = 16
    legendIcon = QgsSymbolLayerUtils.symbolPreviewPixmap(symbol,
                                                         QSize(iconSize,
                                                               iconSize))
    safeLabel = re.sub(r'[\W_]+', '', catr.label()) + str(cnt)
    legendIcon.save(os.path.join(outputProjectFileName, "legend",
                                 layerName + "_" + safeLabel + ".png"))
    catLegend += """<tr><td style="text-align: center;"><img src="legend/"""
    catLegend += layerName + "_" + safeLabel + """.png" /></td><td>"""
    catLegend += catr.label().replace("'", "\\'") + "</td></tr>"
    return catLegend


def pointToLayerFunction(safeLayerName, sl):
    try:
        if isinstance(sl, QgsSvgMarkerSymbolLayer):
            markerType = "marker"
        elif sl.shape() == 8:
            markerType = "circleMarker"
        else:
            markerType = "shapeMarker"
    except Exception:
        markerType = "circleMarker"

    pointToLayerFunction = """
        function pointToLayer_{safeLayerName}_{sl}(feature, latlng) {{
            var context = {{
                feature: feature,
                variables: {{}}
            }};
            return L.{markerType}(latlng, style_{safeLayerName}_{sl}""".format(
        safeLayerName=safeLayerName, sl=sl, markerType=markerType)
    pointToLayerFunction += """(feature));
        }"""
    return pointToLayerFunction


def wfsScript(scriptTag):
    wfs = """
        <script src='{scriptTag}'></script>""".format(scriptTag=scriptTag)
    return wfs


def clusterScript(safeLayerName):
    cluster = """
        var cluster_"""
    cluster += "{safeLayerName} = ".format(safeLayerName=safeLayerName)
    cluster += """new L.MarkerClusterGroup({{showCoverageOnHover: false,
            spiderfyDistanceMultiplier: 2}});
        cluster_{safeLayerName}""".format(safeLayerName=safeLayerName)
    cluster += """.addLayer(layer_{safeLayerName});
""".format(safeLayerName=safeLayerName)
    return cluster


def wmsScript(layer, safeLayerName, useWMS, useWMTS, identify, minZoom,
              maxZoom, count):
    d = parse_qs(layer.source())
    opacity = layer.renderer().opacity()
    attr = ""
    attrText = layer.attribution().replace('\n', ' ').replace('\r', ' ')
    attrUrl = layer.attributionUrl()
    zIndex = count + 400
    if attrText != "":
        attr = u'<a href="%s">%s</a>' % (attrUrl, attrText)
    wms = """
        map.createPane('pane_{safeLayerName}');
        map.getPane('pane_{safeLayerName}').style.zIndex = {zIndex};""".format(
        safeLayerName=safeLayerName, zIndex=zIndex)
    if 'type' in d and d['type'][0] == "xyz":
        url = d['url'][0]
        if 'tiles.openfreemap.org' in url:
            wms += """
        var layer_{safeLayerName} = new L.maplibreGL({{
            style: 'https://tiles.openfreemap.org/styles/liberty',
        }});""".format(safeLayerName=safeLayerName)
        else:
            if 'zmin' in d:
                zmin = "minNativeZoom: {zmin},".format(zmin=d['zmin'][0])
            else:
                zmin = ""
            if 'zmax' in d:
                zmax = "maxNativeZoom: {zmax}".format(zmax=d['zmax'][0])
            else:
                zmax = ""
            wms += """
        var layer_{safeLayerName} = L.tileLayer('{url}', {{
            pane: 'pane_{safeLayerName}',
            opacity: {opacity},
            attribution: '{attr}',
            minZoom: {minZoom},
            maxZoom: {maxZoom},
            {zmin}
            {zmax}
        }});
        layer_{safeLayerName};""".format(
                opacity=opacity, safeLayerName=safeLayerName, url=url,
                attr=attr, zmin=zmin, zmax=zmax,
                minZoom=minZoom, maxZoom=maxZoom)
    elif 'tileMatrixSet' in d:
        useWMTS = True
        wmts_url = d['url'][0]
        wmts_url = wmts_url[:wmts_url.find('?')]
        wmts_layer = d['layers'][0]
        wmts_format = d['format'][0]
        # wmts_crs = d['crs'][0]
        try:
            wmts_style = d['styles'][0]
        except:
            wmts_style = ""
        wmts_tileMatrixSet = d['tileMatrixSet'][0]
        wms += """
        var layer_{safeLayerName} = L.tileLayer.wmts('{wmts_url}', {{
            pane: 'pane_{safeLayerName}',
            layer: '{wmts_layer}',
            tilematrixSet: '{wmts_tileMatrixSet}',
            format: '{wmts_format}',
            style: '{wmts_style}',
            uppercase: true,
            transparent: true,
            continuousWorld : true,
            opacity: {opacity},
            attribution: '{attr}',
        }});""".format(safeLayerName=safeLayerName, wmts_url=wmts_url,
                       wmts_layer=wmts_layer, wmts_format=wmts_format,
                       wmts_tileMatrixSet=wmts_tileMatrixSet,
                       wmts_style=wmts_style, opacity=opacity, attr=attr)
    else:
        useWMS = True
        wms_url = d['url'][0]
        wms_layer = d['layers'][0]
        wms_format = d['format'][0]
        getFeatureInfo = ""
        if not identify:
            getFeatureInfo = """,
            identify: false"""
        wms += """
        var layer_%s = L.WMS.layer("%s", "%s", {
            pane: 'pane_%s',
            format: '%s',
            uppercase: true,
            transparent: true,
            continuousWorld : true,
            tiled: true,
            info_format: 'text/html',
            opacity: %d%s,
            attribution: '%s',
        });""" % (safeLayerName, wms_url, wms_layer, safeLayerName, wms_format,
                  opacity, getFeatureInfo, attr)
    return wms, useWMS, useWMTS


def rasterScript(layer, safeLayerName, zIndex):
    zIndex = zIndex + 400
    out_raster = 'data/' + safeLayerName + '.png'
    pt2 = layer.extent()
    crsSrc = layer.crs()
    crsDest = QgsCoordinateReferenceSystem(4326)
    try:
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
    except Exception:
        xform = QgsCoordinateTransform(crsSrc, crsDest)
    pt3 = xform.transformBoundingBox(pt2)
    bounds = '[[' + str(pt3.yMinimum()) + ','
    bounds += str(pt3.xMinimum()) + '],['
    bounds += str(pt3.yMaximum()) + ','
    bounds += str(pt3.xMaximum()) + ']]'
    raster = """
        map.createPane('pane_{safeLayerName}');
        map.getPane('pane_{safeLayerName}').style.zIndex = {zIndex};
        var img_{safeLayerName} = '{out_raster}';
        var img_bounds_{safeLayerName} = {bounds};
        var layer_{safeLayerName} = """.format(safeLayerName=safeLayerName,
                                               zIndex=zIndex,
                                               out_raster=out_raster,
                                               bounds=bounds)
    raster += "new L.imageOverlay(img_"
    raster += """{sln},
                                              img_bounds_{sln},
                                              {{pane: 'pane_{sln}'}});
        bounds_group.addLayer(layer_{sln});""".format(
        sln=safeLayerName)
    return raster

def titleSubScript(title, pos):
    if pos == "upper right":
        positionOpt = u"{'position':'topright'}"
    if pos == "lower right":
        positionOpt = u"{'position':'bottomright'}"
    if pos == "lower left":
        positionOpt = u"{'position':'bottomleft'}"
    if pos == "upper left":
        positionOpt = u"{'position':'topleft'}"
    titleSub = ""
    if pos != "None":
        titleSub = """
        var title = new L.Control(%s);
        title.onAdd = function (map) {
            this._div = L.DomUtil.create('div', 'info');
            this.update();
            return this._div;
        };
        title.update = function () {
            this._div.innerHTML = '<h2>""" % positionOpt
        titleSub += title.replace("'", "\\'") + """</h2>';
        };
        title.addTo(map);"""
    return titleSub

def abstractSubScript(abstract, pos):
    if pos == "upper right":
        positionOpt = u"{'position':'topright'}"
    if pos == "lower right":
        positionOpt = u"{'position':'bottomright'}"
    if pos == "lower left":
        positionOpt = u"{'position':'bottomleft'}"
    if pos == "upper left":
        positionOpt = u"{'position':'topleft'}"
    abstractSub = ""
    if pos != "None":
        expanded_on_desktop = ('abstract-credit-logo' in abstract or
                               len(abstract) <= 240)
        abstractSub += """
        var abstract = new L.Control(%s);
        abstract.onAdd = function (map) {
            this._div = L.DomUtil.create('div',
            'leaflet-control abstract');
            this._div.id = 'abstract'""" % positionOpt
        if not expanded_on_desktop:
            abstractSub += """
                this._div.setAttribute("onmouseenter",
                    "if (window.matchMedia('(min-width: 900px)').matches) abstract.show()");
                this._div.setAttribute("onmouseleave",
                    "if (window.matchMedia('(min-width: 900px)').matches) abstract.hide()");
                this.hide();
                return this._div;
            };
            abstract.hide = function () {
                this._div.classList.remove("abstractUncollapsed");
                this._div.classList.add("abstract");
                this._div.innerHTML = 'i';
                this._div.setAttribute('aria-expanded', 'false');
            }
            abstract.show = function () {
                this._div.classList.remove("abstract");
                this._div.classList.add("abstractUncollapsed");
                this._div.innerHTML = '"""
        else:
            abstractSub += """

                abstract.show();
                return this._div;
            };
            abstract.hide = function () {
                this._div.classList.remove("abstractUncollapsed");
                this._div.classList.add("abstract");
                this._div.innerHTML = 'i';
                this._div.setAttribute('aria-expanded', 'false');
            }
            abstract.show = function () {
                this._div.classList.remove("abstract");
                this._div.classList.add("abstractUncollapsed");
                this._div.innerHTML = '"""

        abstractSub += abstract.replace("'", "\\'").replace("\n", "<br />")
        abstractSub += """';
            var abstractYear = this._div.querySelector(
                '.abstract-credit-year');
            if (abstractYear) {
                abstractYear.textContent = new Date().getFullYear();
            }
            var abstractCreditLink = this._div.querySelector(
                '.abstract-credit-link');
            if (abstractCreditLink) {
                L.DomEvent.disableClickPropagation(abstractCreditLink);
            }
            this._div.setAttribute('aria-expanded', 'true');
        };
        abstract.addTo(map);"""
        abstractSub += """
        var abstractMediaQuery = window.matchMedia('(min-width: 900px)');
        var abstractExpandedOnDesktop = %s;
        var abstractControlElement = abstract.getContainer();
        abstractControlElement.setAttribute('role', 'button');
        abstractControlElement.setAttribute('tabindex', '0');
        abstractControlElement.setAttribute('aria-label', 'Információ');
        function toggleAbstractOnSmallScreen() {
            if (!abstractMediaQuery.matches) {
                if (abstractControlElement.classList.contains('abstract')) {
                    abstract.show();
                } else {
                    abstract.hide();
                }
            }
        }
        function syncAbstractMode() {
            if (abstractMediaQuery.matches && abstractExpandedOnDesktop) {
                abstract.show();
            } else {
                abstract.hide();
            }
        }
        abstractControlElement.addEventListener('click', function(event) {
            toggleAbstractOnSmallScreen();
            L.DomEvent.stopPropagation(event);
        });
        abstractControlElement.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                toggleAbstractOnSmallScreen();
            }
        });
        if (abstractMediaQuery.addEventListener) {
            abstractMediaQuery.addEventListener('change', syncAbstractMode);
        } else {
            abstractMediaQuery.addListener(syncAbstractMode);
        }
        syncAbstractMode();""" % ("true" if expanded_on_desktop else "false")

    return abstractSub


def addLayersList(baseMap, matchCRS, layer_list, groups, collapsedGroup, cluster, legends,
                  expanded):
    controlStart = """
        var overlaysTree = [
    """
        
    layersList = controlStart
    # Dizionario per tenere traccia dei gruppi creati
    created_groups = {}
    # Dizionario per tenere traccia dei gruppi per i quali abbiamo già aggiunto la chiusura
    closed_groups = {}
    
    # Crea una mappa tra nome gruppo e indice in collapsedGroup
    group_to_collapsed_index = {}
    for idx, group_name in enumerate(groups.keys()):
        group_to_collapsed_index[group_name] = idx

    lyrCount = len(layer_list) - 1
    baseMapCount = len(baseMap)
    for i, clustered in zip(reversed(layer_list), reversed(cluster)):
        try:
            rawLayerName = i.name()
            safeLayerName = safeName(rawLayerName) + "_" + str(lyrCount)
            lyrCount -= 1
            baseMapCount -= 1

            # Verifica se il layer fa parte di uno dei gruppi
            is_in_group = False
            for group_layers in groups.values():
                if i in group_layers:
                    is_in_group = True
                    break
            
            if is_in_group:
                for group_name, group_layers in groups.items():
                    if i in group_layers:
                        # Controlla se il gruppo è già stato creato
                        if group_name not in created_groups:
                            created_groups[group_name] = []  # Crea il gruppo vuoto
                            # Usa l'indice corretto del gruppo nella mappa
                            group_index = group_to_collapsed_index[group_name]
                            collapsed = "collapsed: true," if collapsedGroup[group_index] else ""
                            layersList += """
        {label: '<b>""" + group_name + "</b>', " + collapsed + " selectAllCheckbox: true, children: ["""
                        # Aggiunge il layer al gruppo
                        created_groups[group_name].append(i)
                            
            if i.type() == QgsMapLayer.VectorLayer:
                # testDump = i.renderer().dump()
                if clustered and i.geometryType() == QgsWkbTypes.PointGeometry:
                    layersList += """
            {label: '""" + legends[safeLayerName].replace("'", "\'")
                    layersList += "', layer: cluster_""" + safeLayerName + "},"
                else:
                    layersList += """
            {label: '""" + legends[safeLayerName].replace("'", "\'")
                    layersList += "', layer: layer_" + safeLayerName + "},"
            elif i.type() == QgsMapLayer.RasterLayer:
                layersList += '''
            {label: "''' + rawLayerName.replace("'", "\'") + '"'
                layersList += ", layer: layer_" + safeLayerName 
                if baseMap[baseMapCount]:
                    layersList += ", radioGroup: 'bm' },"
                else:
                    layersList += "},"

            # Controlla se tutti i layer del gruppo sono stati aggiunti
            for group_name in created_groups:
                if group_name not in closed_groups and len(created_groups[group_name]) == len(groups[group_name]):
                    layersList += "]},"  # Chiude il gruppo se tutti i layer sono stati aggiunti
                    # Aggiungi il gruppo alla lista dei gruppi chiusi
                    closed_groups[group_name] = True

        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc(), "qgis2web",
                                    level=Qgis.Critical)
            
    layersList += "]"

    layersList += """
        var lay = L.control.layers.tree(null, overlaysTree,{
            //namedToggle: true,
            //selectorBack: false,
            //closedSymbol: '&#8862; &#x1f5c0;',
            //openedSymbol: '&#8863; &#x1f5c1;',
            //collapseAll: 'Collapse all',
            //expandAll: 'Expand all',
        """
    if expanded:
        layersList += """
            collapsed: false, 
        });
        """
    else:
        layersList += """
            collapsed: true,
        });
        """  
    layersList += """
        lay.addTo(map);
        var layersControlList = lay.getContainer().querySelector(
            '.leaflet-control-layers-list');
        if (layersControlList) {
            var layersControlTitle = document.createElement('h2');
            layersControlTitle.className = 'qgis2web-layers-title';
            layersControlTitle.textContent = 'Rétegek';
            layersControlList.insertBefore(
                layersControlTitle, layersControlList.firstChild);
        }
        """
    if expanded:
        layersList += """
        document.addEventListener("DOMContentLoaded", function() {
            var controlLayersElement = document.querySelector('.leaflet-control-layers');
            var toggleLayerControl = document.querySelector('.leaflet-control-layers-toggle');
            if (!controlLayersElement || !toggleLayerControl) {
                return;
            }
            var layersMediaQuery = window.matchMedia('(min-width: 900px)');
            var isLayersListExpanded = layersMediaQuery.matches;
            function setLayersListExpanded(isExpanded) {
                isLayersListExpanded = isExpanded;
                controlLayersElement.classList.toggle(
                    'leaflet-control-layers-expanded', isExpanded);
                toggleLayerControl.setAttribute(
                    'aria-expanded', String(isExpanded));
                if (typeof qgis2webInvalidateMapSize === 'function') {
                    qgis2webInvalidateMapSize();
                }
            }
            toggleLayerControl.addEventListener('click', function() {
                setLayersListExpanded(!isLayersListExpanded);
            });
            function syncLayersListMode() {
                setLayersListExpanded(layersMediaQuery.matches);
            }
            if (layersMediaQuery.addEventListener) {
                layersMediaQuery.addEventListener('change', syncLayersListMode);
            } else {
                layersMediaQuery.addListener(syncLayersListMode);
            }
            syncLayersListMode();
        });
        """
    return layersList


def scaleBar():
    scaleBar = "L.control.scale({position: 'bottomleft', "
    scaleBar += "maxWidth: 100, metric: true, imperial: false, "
    scaleBar += "updateWhenIdle: false}).addTo(map);"
    return scaleBar


def addressSearchScript(method):
    addressSearch = f"""
        const url = {{"Nominatim OSM": "https://nominatim.openstreetmap.org/search?format=geojson&addressdetails=1&",
        "France BAN": "https://api-adresse.data.gouv.fr/search/?"}}
        var photonControl = L.control.photon({{
            url: url["{method}"],
            feedbackLabel: '',
            position: 'topleft',
            includePosition: true,
            initial: true,
            // resultsHandler: myHandler,
        }}).addTo(map);
        photonControl._container.childNodes[0].style.borderRadius="10px"
        // Create a variable to store the geoJSON data
        var x = null;
        // Create a variable to store the marker
        var marker = null;
        // Add an event listener to the Photon control to create a marker from the returned geoJSON data
        var z = null;
        photonControl.on('selected', function(e) {{
            console.log(photonControl.search.resultsContainer);
            if (x != null) {{
                map.removeLayer(obj3.marker);
                map.removeLayer(x);
            }}
            obj2.gcd = e.choice;
            x = L.geoJSON(obj2.gcd).addTo(map);
            var label = typeof obj2.gcd.properties.label === 'undefined' ? obj2.gcd.properties.display_name : obj2.gcd.properties.label;
            obj3.marker = L.marker(x.getLayers()[0].getLatLng()).bindPopup(label).addTo(map);
            map.setView(x.getLayers()[0].getLatLng(), 17);
            z = typeof e.choice.properties.label === 'undefined'? e.choice.properties.display_name : e.choice.properties.label;
            console.log(e);
            e.target.input.value = z;
        }});
        var search = document.getElementsByClassName("leaflet-photon leaflet-control")[0];
        search.classList.add("leaflet-control-search")
        search.style.display = "flex";
        search.style.backgroundColor="rgba(255,255,255,0.5)" 

        // Create the new button element
        var button = document.createElement("div");
        button.id = "gcd-button-control";
        button.className = "gcd-gl-btn search-button qgis2web-search-position";
        button.setAttribute("role", "button");
        button.setAttribute("tabindex", "0");
        button.setAttribute("aria-label", "Hely keresése");
        button.setAttribute("title", "Hely keresése");

        // Insert the button at the beginning of the search control
        search.insertBefore(button, search.firstChild);
        last = search.lastChild;
        last.style.display = "none";
        button.addEventListener("click", function (e) {{
            if (last.style.display === "none") {{
                last.style.display = "block";
            }} else {{
                last.style.display = "none";
            }}
        }});
        button.addEventListener("keydown", function (e) {{
            if (e.key === "Enter" || e.key === " ") {{
                e.preventDefault();
                button.click();
            }}
        }});
        """
    return addressSearch


def getVTStyles(vtStyles):
    vtStyleString = ""
    for (vts, lyrs) in vtStyles.items():
        vtStyleString += """
        style_%s = {""" % safeName(vts)
        for (lyr, styles) in lyrs.items():
            vtStyleString += """
            %s: [""" % lyr
            for style in styles:
                if style == "":
                    style = "{}"
                vtStyleString += "%s," % style
            vtStyleString += "],"
            vtStyleString = vtStyleString.replace(",]", "]")
        vtStyleString += "}"

    return vtStyleString


def getVTLabels(vtLabels):
    labels = []
    for k, v in vtLabels.items():
        labels.append("""
    function label_%s(feature, featureLayer, vtLayer, tileCoords) {
        var context = {
            feature: feature,
            variables: {}
        };
        %s
    }""" % (safeName(k), v))
    labelString = "".join(labels)
    return labelString


def endHTMLscript(wfsLayers, layerSearch, filterItems, labelCode, labels,
                  searchLayer, useHeat, useRaster, labelsList,
                  mapUnitLayers):
    if labels == "":
        endHTML = ""
    else:
        endHTML = """
        map.on("zoomend", function(){
%s
        });""" % labels
    if wfsLayers == "":
        endHTML += """
        setBounds();
        %s""" % labelCode
        endHTML += labels
    if len(mapUnitLayers) > 0:
        lyrs = []
        for layer in mapUnitLayers:
            lyrs.append("""
            layer_%s.setStyle(style_%s_0);""" % (layer, layer))
        lyrScripts = "".join(lyrs)
        endHTML += """
        newM2px();
%s
        map.on("zoomend", function(){
            newM2px();
%s
        });""" % (lyrScripts, lyrScripts)
    if layerSearch != "None":
        searchVals = layerSearch.split(": ")
        endHTML += """
        var layerSearchControl = new L.Control.Search({{
            layer: {searchLayer},
            initial: false,
            hideMarkerOnCollapse: true,
            propertyName: '{field}'}});
        map.addControl(layerSearchControl);
        var layerSearchButton = layerSearchControl._container.querySelector(
            '.search-button');
        if (layerSearchButton) {{
            layerSearchButton.classList.add('qgis2web-search-trees');
            layerSearchButton.setAttribute('aria-label', 'Fák keresése');
            layerSearchButton.setAttribute('title', 'Fák keresése');
        }}""".format(searchLayer=searchLayer,
                    field=searchVals[1])
    endHTML += """
        var qgis2webResizeFrame = null;
        function qgis2webInvalidateMapSize() {
          if (qgis2webResizeFrame !== null) {
            return;
          }
          var requestFrame = window.requestAnimationFrame || function(callback) {
            return window.setTimeout(callback, 16);
          };
          qgis2webResizeFrame = requestFrame(function() {
            qgis2webResizeFrame = null;
            if (typeof map !== 'undefined' && map.invalidateSize) {
              map.invalidateSize({pan: false, debounceMoveend: true});
            }
          });
        }
        window.addEventListener('resize', qgis2webInvalidateMapSize);
        window.addEventListener('orientationchange', qgis2webInvalidateMapSize);
        if (window.ResizeObserver) {
          var qgis2webMapResizeObserver = new ResizeObserver(
            qgis2webInvalidateMapSize);
          var qgis2webMapElement = document.getElementById('map');
          if (qgis2webMapElement) {
            qgis2webMapResizeObserver.observe(qgis2webMapElement);
          }
        }
        qgis2webInvalidateMapSize();
        """
    filterItems = sorted(filterItems, key=lambda k: k['type'])
    filterNum = len(filterItems)
    if filterNum != 0:
        endHTML += """
        var mapDiv = document.getElementById('map');
        document.body.classList.add('qgis2web-has-filters');
        var row = document.createElement('div');
        row.className = 'row qgis2web-layout';
        row.id = 'all';
        var col1 = document.createElement('div');
        col1.className = 'col9 qgis2web-map-panel';
        col1.id = "mapWindow";
        var col2 = document.createElement('div');
        col2.className = 'col3 qgis2web-filter-panel';
        col2.id = "menu";
        col2.setAttribute('role', 'complementary');
        col2.setAttribute('aria-label', 'Szűrők');
        var filterToggle = document.createElement('button');
        filterToggle.type = 'button';
        filterToggle.className = 'qgis2web-filter-toggle';
        filterToggle.setAttribute('aria-controls', 'menu');
        filterToggle.setAttribute('aria-expanded', 'false');
        filterToggle.textContent = 'Szűrők';
        var filterBackdrop = document.createElement('div');
        filterBackdrop.className = 'qgis2web-filter-backdrop';
        filterBackdrop.setAttribute('aria-hidden', 'true');
        var filterClose = document.createElement('button');
        filterClose.type = 'button';
        filterClose.className = 'qgis2web-filter-close';
        filterClose.setAttribute('aria-label', 'Szűrők bezárása');
        filterClose.innerHTML = '&times;';
        col2.appendChild(filterClose);
        var menuTitle = document.createElement('h2');
        menuTitle.className = "menu-title";
        menuTitle.textContent = "Leválogatás";
        col2.appendChild(menuTitle);
        var menuSubtitle = document.createElement('h3');
        menuSubtitle.className = "menu-subtitle";
        menuSubtitle.textContent = "Különböző szempontok szerint";
        col2.appendChild(menuSubtitle);
        mapDiv.parentNode.insertBefore(row, mapDiv);
        row.appendChild(col1);
        row.appendChild(filterToggle);
        row.appendChild(filterBackdrop);
        row.appendChild(col2);
        col1.appendChild(mapDiv);

        var filterMediaQuery = window.matchMedia('(min-width: 900px)');
        var filterReturnFocus = null;
        function setFilterPanelOpen(isOpen, restoreFocus) {
          document.body.classList.toggle('qgis2web-filter-open', isOpen);
          filterToggle.setAttribute('aria-expanded', String(isOpen));
          if (filterMediaQuery.matches) {
            col2.removeAttribute('aria-hidden');
          } else {
            col2.setAttribute('aria-hidden', String(!isOpen));
          }
          if (isOpen) {
            filterReturnFocus = document.activeElement;
            filterClose.focus();
          } else if (restoreFocus && filterReturnFocus) {
            filterReturnFocus.focus();
          }
          qgis2webInvalidateMapSize();
        }
        function syncFilterPanelMode() {
          if (filterMediaQuery.matches) {
            document.body.classList.remove('qgis2web-filter-open');
            filterToggle.setAttribute('aria-expanded', 'false');
            col2.removeAttribute('aria-hidden');
          } else {
            col2.setAttribute('aria-hidden', String(
              !document.body.classList.contains('qgis2web-filter-open')));
          }
          qgis2webInvalidateMapSize();
        }
        filterToggle.addEventListener('click', function() {
          setFilterPanelOpen(true, false);
        });
        filterClose.addEventListener('click', function() {
          setFilterPanelOpen(false, true);
        });
        filterBackdrop.addEventListener('click', function() {
          setFilterPanelOpen(false, true);
        });
        document.addEventListener('keydown', function(event) {
          if (event.key === 'Escape' &&
              document.body.classList.contains('qgis2web-filter-open')) {
            setFilterPanelOpen(false, true);
          }
        });
        if (filterMediaQuery.addEventListener) {
          filterMediaQuery.addEventListener('change', syncFilterPanelMode);
        } else {
          filterMediaQuery.addListener(syncFilterPanelMode);
        }
        col2.addEventListener('transitionend', qgis2webInvalidateMapSize);
        syncFilterPanelMode();
        var Filters = {"""
        filterList = []
        for item in range(0, filterNum):
            filterList.append('"' + filterItems[item]["name"] + '": "' +
                              filterItems[item]["type"] + '"')
        endHTML += ",".join(filterList) + "};"
        endHTML += r"""
        var filterTimeout = null;
        var filtersInitializing = true;
        var filterableLayers = [];
        bounds_group.eachLayer(function(lyr) {
          if (lyr.options && lyr.options.dataVar &&
              typeof lyr.clearLayers === "function" &&
              typeof lyr.addData === "function") {
            filterableLayers.push(lyr);
          }
        });

        function setFilteredFeatureCount(count) {
          var countElement = document.getElementById("filtered-feature-count");
          if (countElement) {
            countElement.textContent =
              "Leválogatott fák darabszáma: " + count;
          }
        }

        function readFilterState() {
          var state = [];
          Object.keys(Filters).forEach(function(key) {
            var type = Filters[key];
            var keyS = key.replace(/[^a-zA-Z0-9_]/g, "");
            var item = {key: key, type: type};
            if (type === "str" || type === "bool") {
              item.selection = [];
              var select = document.getElementById("sel_" + keyS);
              if (select) {
                for (var i = 0; i < select.options.length; i++) {
                  if (select.options[i].selected && select.options[i].value !== "") {
                    item.selection.push(select.options[i].value);
                  }
                }
              }
            } else if (type === "int" || type === "real") {
              var slider = document.getElementById("div_" + keyS);
              if (slider && slider.noUiSlider) {
                var sliderValues = slider.noUiSlider.get();
                item.min = parseFloat(sliderValues[0]);
                item.max = parseFloat(sliderValues[1]);
              }
            } else if (type === "date" || type === "datetime" ||
                       type === "time") {
              var HTMLkey = key.replace(/[&\\/\\#,+()$~%.'":*?<>{} ]/g, "");
              var startInput = document.getElementById(
                "dat_" + HTMLkey + "_date1");
              var endInput = document.getElementById(
                "dat_" + HTMLkey + "_date2");
              item.start = startInput ? startInput.value.replace(" ", "T") : "";
              item.end = endInput ? endInput.value.replace(" ", "T") : "";
            }
            state.push(item);
          });
          return state;
        }

        function featureMatchesFilters(feature, filterState) {
          var properties = feature.properties || {};
          for (var i = 0; i < filterState.length; i++) {
            var item = filterState[i];
            if (!(item.key in properties)) {
              continue;
            }
            var value = properties[item.key];
            if ((item.type === "str" || item.type === "bool") &&
                item.selection.length > 0 &&
                item.selection.indexOf(value) === -1) {
              return false;
            }
            if (item.type === "int" || item.type === "real") {
              var numericValue = parseFloat(value);
              if (!isNaN(numericValue) &&
                  (numericValue < item.min || numericValue > item.max)) {
                return false;
              }
            }
            if ((item.type === "date" || item.type === "datetime" ||
                 item.type === "time") && value !== null &&
                ((item.start && value < item.start) ||
                 (item.end && value > item.end))) {
              return false;
            }
          }
          return true;
        }

        function applyFilters() {
          filterTimeout = null;
          var filterState = readFilterState();
          var filteredFeatureCount = 0;
          filterableLayers.forEach(function(lyr) {
            var sourceData = window[lyr.options.dataVar];
            if (!sourceData || !Array.isArray(sourceData.features)) {
              return;
            }
            var features = sourceData.features.filter(function(feature) {
              return featureMatchesFilters(feature, filterState);
            });
            filteredFeatureCount += features.length;
            lyr.clearLayers();
            lyr.addData({type: "FeatureCollection", features: features});
          });
          setFilteredFeatureCount(filteredFeatureCount);
          if (typeof scheduleLabelReset === "function") {
            scheduleLabelReset(filterableLayers);
          }
        }

        function filterFunc() {
          if (filtersInitializing) {
            return;
          }
          if (filterTimeout !== null) {
            window.clearTimeout(filterTimeout);
          }
          filterTimeout = window.setTimeout(applyFilters, 120);
        }"""
        for item in range(0, filterNum):
            itemName = filterItems[item]["name"]
            if filterItems[item]["type"] in ["str", "bool"]:
                selSize = 2
                if filterItems[item]["type"] == "str":
                    if len(filterItems[item]["values"]) > 10:
                        selSize = 10
                    else:
                        selSize = len(filterItems[item]["values"])
                endHTML += """
            document.getElementById("menu").appendChild(
                document.createElement("div"));
            var lab_{nameS} = document.createElement('div');
            lab_{nameS}.innerHTML = '{name}';
            lab_{nameS}.className = 'filterlabel';
            document.getElementById("menu").appendChild(lab_{nameS});
            var div_{nameS} = document.createElement('div');
            div_{nameS}.id = "div_{nameS}";
            div_{nameS}.className= "filterselect";
            document.getElementById("menu").appendChild(div_{nameS});
            sel_{nameS} = document.createElement('select');
            sel_{nameS}.multiple = true;
            sel_{nameS}.size = {s};
            sel_{nameS}.id = "sel_{nameS}";
            var {nameS}_options_str = "<option value='' unselected></option>";
            sel_{nameS}.onchange = function(){{filterFunc()}};
            """.format(name=itemName, nameS=safeName(itemName), s=selSize)
                for entry in filterItems[item]["values"]:
                    try:
                        safeEntry = entry.replace("'", "&apos;")
                    except:
                        safeEntry = entry
                    endHTML += """
            {nameS}_options_str  += '<option value="{e}">{e}</option>';
                        """.format(e=safeEntry,
                                   name=itemName, nameS=safeName(itemName))
                endHTML += """
            sel_{nameS}.innerHTML = {nameS}_options_str;
            div_{nameS}.appendChild(sel_{nameS});
            var reset_{nameS} = document.createElement('div');
            reset_{nameS}.innerHTML = 'Szűrő törlése';
            reset_{nameS}.className = 'filterlabel filterreset';
            reset_{nameS}.onclick = function() {{
                var options = document.getElementById("sel_{nameS}").options;
                for (var i=0; i < options.length; i++) {{
                    options[i].selected = false;
                }}
                filterFunc();
            }};
            div_{nameS}.appendChild(reset_{nameS});
                """.format(name=itemName, nameS=safeName(itemName))
            if filterItems[item]["type"] in ["int", "real"]:
                filterName = itemName.strip().rstrip(":")
                filterUnit = {
                    "Átmérő": " cm",
                    "Becsült kor": " év",
                    "Becs. kor": " év",
                }.get(filterName, "")
                endHTML += """
            document.getElementById("menu").appendChild(
                document.createElement("div"));
            var lab_{nameS} = document.createElement('div');
            lab_{nameS}.innerHTML  = '{name}: <span id="val_{nameS}"></span>{unit}';
            lab_{nameS}.className = 'filterlabel';
            document.getElementById("menu").appendChild(lab_{nameS});
            var div_{nameS} = document.createElement("div");
            div_{nameS}.id = "div_{nameS}";
            div_{nameS}.className = "slider";
            document.getElementById("menu").appendChild(div_{nameS});
            var reset_{nameS} = document.createElement('div');
            reset_{nameS}.innerHTML = 'Szűrő törlése';
            reset_{nameS}.className = 'filterlabel filterreset';
            reset_{nameS}.onclick = function() {{
                sel_{nameS}.noUiSlider.reset();
            }};
            document.getElementById("menu").appendChild(reset_{nameS});
            var sel_{nameS} = document.getElementById('div_{nameS}');
            """ .format(name=itemName, nameS=safeName(itemName),
                         unit=filterUnit)
                if filterItems[item]["type"] == "int":
                    endHTML += """
            noUiSlider.create(sel_{nameS}, {{
                connect: true,
                start: [{min}, {max}],
                step: 1,
                format: wNumb({{
                    decimals: 0,
                    }}),
                range: {{
                min: {min},
                max: {max}
                }}
            }});
            sel_{nameS}.noUiSlider.on('update', function (values) {{
            filterVals =[];
            for (value in values){{
            filterVals.push(parseInt(value))
            }}
            val_{nameS} = document.getElementById('val_{nameS}');
            val_{nameS}.innerHTML = values.join(' - ');
                filterFunc()
            }});""".format(name=itemName, nameS=safeName(itemName),
                           min=filterItems[item]["values"][0],
                           max=filterItems[item]["values"][1])
                else:
                    endHTML += """
            noUiSlider.create(sel_{nameS}, {{
                connect: true,
                start: [{min}, {max}],
                range: {{
                min: {min},
                max: {max}
                }}
            }});
            sel_{nameS}.noUiSlider.on('update', function (values) {{
            val_{nameS} = document.getElementById('val_{nameS}');
            val_{nameS}.innerHTML = values.join(' - ');
                filterFunc()
            }});
            """.format(name=itemName, nameS=safeName(itemName),
                       min=filterItems[item]["values"][0],
                       max=filterItems[item]["values"][1])
            if filterItems[item]["type"] in ["date", "time", "datetime"]:
                startDate = filterItems[item]["values"][0]
                endDate = filterItems[item]["values"][1]
                d = "'YYYY-mm-dd'"
                t = "'HH:ii:ss'"
                Y1 = startDate.toString("yyyy")
                M1 = startDate.toString("M")
                D1 = startDate.toString("d")
                hh1 = startDate.toString("h")
                mm1 = startDate.toString("m")
                ss1 = startDate.toString("s")
                Y2 = endDate.toString("yyyy")
                M2 = endDate.toString("M")
                D2 = endDate.toString("d")
                hh2 = endDate.toString("h")
                mm2 = endDate.toString("m")
                ss2 = endDate.toString("s")
                if filterItems[item]["type"] == "date":
                    t = "false"
                    hh1 = 0
                    mm1 = 0
                    ss1 = 0
                    hh2 = 0
                    mm2 = 0
                    ss2 = 0
                    ds = QDateTime(startDate).toMSecsSinceEpoch()
                    de = QDateTime(endDate).toMSecsSinceEpoch()
                if filterItems[item]["type"] == "datetime":
                    ds = startDate.toMSecsSinceEpoch()
                    de = endDate.toMSecsSinceEpoch()
                if filterItems[item]["type"] == "time":
                    d = "false"
                    Y1 = 0
                    M1 = 1
                    D1 = 0
                    Y2 = 0
                    M2 = 1
                    D2 = 0
                    ds = "null"
                    de = "null"
                endHTML += """
            document.getElementById("menu").appendChild(
                document.createElement("div"));
            var lab_{nameS}_date1 = document.createElement('div');
            lab_{nameS}_date1.innerHTML  = '{name} from';
            lab_{nameS}_date1.className = 'filterlabel';
            document.getElementById("menu").appendChild(lab_{nameS}_date1);
            var div_{nameS}_date1 = document.createElement("div");
            div_{nameS}_date1.id = "div_{nameS}_date1";
            div_{nameS}_date1.className= "filterselect";
            document.getElementById("menu").appendChild(div_{nameS}_date1);
            dat_{nameS}_date1 = document.createElement('input');
            dat_{nameS}_date1.type = "text";
            dat_{nameS}_date1.id = "dat_{nameS}_date1";
            div_{nameS}_date1.appendChild(dat_{nameS}_date1);
            var reset_{nameS}_date1 = document.createElement('div');
            reset_{nameS}_date1.innerHTML = 'Törlés';
            reset_{nameS}_date1.className = 'filterlabel filterreset';
            reset_{nameS}_date1.onclick = function() {{
                tail.DateTime("#dat_{nameS}_date1", {{
                    dateStart: {ds},
                    dateEnd: {de},
                    dateFormat: {d},
                    timeFormat: {t},
                    today: false,
                    weekStart: 1,
                    position: "left",
                    closeButton: true,
                    timeStepMinutes:1,
                    timeStepSeconds: 1
                }}).selectDate({Y1},{M1}-1,{D1},{hh1},{mm1},{ss1});
                tail.DateTime("#dat_{nameS}_date1").reload()
            }}
            document.getElementById("div_{nameS}_date1").appendChild(
                reset_{nameS}_date1);
            document.addEventListener("DOMContentLoaded", function(){{
                tail.DateTime("#dat_{nameS}_date1", {{
                    dateStart: {ds},
                    dateEnd: {de},
                    dateFormat: {d},
                    timeFormat: {t},
                    today: false,
                    weekStart: 1,
                    position: "left",
                    closeButton: true,
                    timeStepMinutes:1,
                    timeStepSeconds: 1
                }}).selectDate({Y1},{M1}-1,{D1},{hh1},{mm1},{ss1});
                tail.DateTime("#dat_{nameS}_date1").reload()
                """.format(name=itemName, nameS=safeName(itemName), de=de,
                           ds=ds, d=d, t=t, Y1=Y1, M1=M1, D1=D1, hh1=hh1,
                           mm1=mm1, ss1=ss1)
                endHTML += """
                tail.DateTime("#dat_{nameS}_date2", {{
                    dateStart: {ds},
                    dateEnd: {de},
                    dateFormat: {d},
                    timeFormat: {t},
                    today: false,
                    weekStart: 1,
                    position: "left",
                    closeButton: true,
                    timeStepMinutes:1,
                    timeStepSeconds: 1
                }}).selectDate({Y2},{M2}-1,{D2},{hh2},{mm2},{ss2});
                tail.DateTime("#dat_{nameS}_date2").reload()
                filterFunc()
                dat_{nameS}_date1.onchange = function(){{filterFunc()}};
                dat_{nameS}_date2.onchange = function(){{filterFunc()}};
            }});
            """.format(name=itemName, nameS=safeName(itemName), de=de, ds=ds,
                       d=d, t=t, Y2=Y2, M2=M2, D2=D2, hh2=hh2, mm2=mm2,
                       ss2=ss2)
                endHTML += """
            var lab_{nameS}_date2 = document.createElement('div');
            lab_{nameS}_date2.innerHTML  = '{name} till';
            lab_{nameS}_date2.className = 'filterlabel';
            document.getElementById("menu").appendChild(lab_{nameS}_date2);
            var div_{nameS}_date2 = document.createElement("div");
            div_{nameS}_date2.id = "div_{nameS}_date2";
            div_{nameS}_date2.className= "filterselect";
            document.getElementById("menu").appendChild(div_{nameS}_date2);
            dat_{nameS}_date2 = document.createElement('input');
            dat_{nameS}_date2.type = "text";
            dat_{nameS}_date2.id = "dat_{nameS}_date2";
            div_{nameS}_date2.appendChild(dat_{nameS}_date2);
            var reset_{nameS}_date2 = document.createElement('div');
            reset_{nameS}_date2.innerHTML = 'Törlés';
            reset_{nameS}_date2.className = 'filterlabel filterreset';
            reset_{nameS}_date2.onclick = function() {{
                tail.DateTime("#dat_{nameS}_date2", {{
                    dateStart: {ds},
                    dateEnd: {de},
                    dateFormat: {d},
                    timeFormat: {t},
                    today: false,
                    weekStart: 1,
                    position: "left",
                    closeButton: true,
                    timeStepMinutes:1,
                    timeStepSeconds: 1
                }}).selectDate({Y2},{M2}-1,{D2},{hh2},{mm2},{ss2});
                tail.DateTime("#dat_{nameS}_date2").reload()
            }}
            document.getElementById("div_{nameS}_date2").appendChild(
                reset_{nameS}_date2);
            """.format(name=itemName, nameS=safeName(itemName), de=de, ds=ds,
                       d=d, t=t, Y2=Y2, M2=M2, D2=D2, hh2=hh2, mm2=mm2,
                       ss2=ss2)
        endHTML += """
        var filteredFeatureCountDiv = document.createElement('div');
        filteredFeatureCountDiv.id = 'filtered-feature-count';
        filteredFeatureCountDiv.className = 'filtercount';
        filteredFeatureCountDiv.setAttribute('aria-live', 'polite');
        filteredFeatureCountDiv.textContent =
          'Leválogatott fák darabszáma: 0';
        document.getElementById('menu').appendChild(filteredFeatureCountDiv);
        var initialFeatureCount = 0;
        filterableLayers.forEach(function(lyr) {
          var sourceData = window[lyr.options.dataVar];
          if (sourceData && Array.isArray(sourceData.features)) {
            initialFeatureCount += sourceData.features.length;
          }
        });
        setFilteredFeatureCount(initialFeatureCount);
        filtersInitializing = false;
        """
    if useHeat:
        endHTML += """
        function geoJson2heat(geojson, weight) {
          return geojson.features.map(function(feature) {
            return [
              feature.geometry.coordinates[1],
              feature.geometry.coordinates[0],
              feature.properties[weight]
            ];
          });
        }"""
    if useRaster:
        endHTML += """
        L.ImageOverlay.include({
            getBounds: function () {
                return this._bounds;
            }
        });"""
    if labelsList != "":
        endHTML += """
        scheduleLabelReset([%s]);
        map.on("zoomend", function(){
            scheduleLabelReset([%s]);
        });
        map.on("layeradd", function(){
            scheduleLabelReset([%s]);
        });
        map.on("layerremove", function(){
            scheduleLabelReset([%s]);
        });""" % (labelsList, labelsList, labelsList, labelsList)
    endHTML += """
        </script>%s""" % wfsLayers
    return endHTML
