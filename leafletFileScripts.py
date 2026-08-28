# -*- coding: utf-8 -*-

import re
import os
import shutil
import codecs
from qgis2web.utils import replaceInTemplate


LEAFLET_FONT_COLOR = "#1f4d3a"


def writeFoldersAndFiles(pluginDir, feedback, outputProjectFileName,
                         cluster_set, measure, matchCRS, layerSearch,
                         filterItems, useOFM, canvas, address, locate,
                         layersList, useLabelgun=False):
    feedback.showFeedback("Exporting libraries...")
    jsStore = os.path.join(outputProjectFileName, 'js')
    os.makedirs(jsStore)
    jsStore += os.sep
    jsDir = pluginDir + os.sep + 'leaflet' + os.sep + 'js' + os.sep
    dataStore = os.path.join(outputProjectFileName, 'data')
    os.makedirs(dataStore)
    imageDir = pluginDir + os.sep + 'leaflet' + os.sep + 'images' + os.sep
    iconDir = pluginDir + os.sep + 'icons' + os.sep
    imageStore = os.path.join(outputProjectFileName, 'images')
    legendStore = os.path.join(outputProjectFileName, 'legend')
    os.makedirs(legendStore)
    cssStore = os.path.join(outputProjectFileName, 'css')
    os.makedirs(cssStore)
    cssStore += os.sep
    cssDir = pluginDir + os.sep + 'leaflet' + os.sep + 'css' + os.sep
    fontDir = pluginDir + os.sep + 'webfonts' + os.sep
    fontStore = os.path.join(outputProjectFileName, 'webfonts')
    os.makedirs(fontStore)
    fontStore += os.sep
    markerStore = os.path.join(outputProjectFileName, 'markers')
    os.makedirs(markerStore)
    shutil.copyfile(jsDir + 'qgis2web_expressions.js',
                    jsStore + 'qgis2web_expressions.js')
    shutil.copyfile(jsDir + 'leaflet.wms.js',
                    jsStore + 'leaflet.wms.js')
    shutil.copyfile(jsDir + 'leaflet-tilelayer-wmts.js',
                    jsStore + 'leaflet-tilelayer-wmts.js')
    shutil.copyfile(jsDir + 'leaflet-svg-shape-markers.min.js',
                    jsStore + 'leaflet-svg-shape-markers.min.js')
    shutil.copyfile(jsDir + 'leaflet.pattern.js',
                    jsStore + 'leaflet.pattern.js')
    if useLabelgun:
        shutil.copyfile(jsDir + 'rbush.min.js',
                        jsStore + 'rbush.min.js')
        shutil.copyfile(jsDir + 'labelgun.min.js',
                        jsStore + 'labelgun.min.js')
        shutil.copyfile(jsDir + 'labels.js',
                        jsStore + 'labels.js')
    shutil.copyfile(jsDir + 'leaflet.js', jsStore + 'leaflet.js')
    shutil.copyfile(jsDir + 'leaflet.js.map', jsStore + 'leaflet.js.map')
    shutil.copyfile(cssDir + 'leaflet.css', cssStore + 'leaflet.css')
    if layersList != "None":
        shutil.copyfile(jsDir + 'L.Control.Layers.Tree.min.js',
                        jsStore + 'L.Control.Layers.Tree.min.js')
        shutil.copyfile(cssDir + 'L.Control.Layers.Tree.css',
                        cssStore + 'L.Control.Layers.Tree.css')
    if address:
        shutil.copyfile(jsDir + 'leaflet.photon.js',
                        jsStore + 'leaflet.photon.js')
        shutil.copyfile(cssDir + 'leaflet.photon.css',
                        cssStore + 'leaflet.photon.css')
    if locate:
        shutil.copyfile(jsDir + 'L.Control.Locate.min.js',
                        jsStore + 'L.Control.Locate.min.js')
        shutil.copyfile(cssDir + 'L.Control.Locate.min.css',
                        cssStore + 'L.Control.Locate.min.css')
    shutil.copyfile(jsDir + 'multi-style-layer.js',
                    jsStore + 'multi-style-layer.js')
    shutil.copyfile(jsDir + 'Autolinker.min.js',
                    jsStore + 'Autolinker.min.js')
    shutil.copyfile(jsDir + 'OSMBuildings-Leaflet.js',
                    jsStore + 'OSMBuildings-Leaflet.js')
    shutil.copyfile(jsDir + 'leaflet-heat.js',
                    jsStore + 'leaflet-heat.js')
    shutil.copyfile(jsDir + 'Leaflet.VectorGrid.js',
                    jsStore + 'Leaflet.VectorGrid.js')
    shutil.copyfile(jsDir + 'leaflet-hash.js', jsStore + 'leaflet-hash.js')
    shutil.copyfile(jsDir + 'leaflet.rotatedMarker.js',
                    jsStore + 'leaflet.rotatedMarker.js')

    # copy icons
    shutil.copyfile(cssDir + 'fontawesome-all.min.css',
                    cssStore + 'fontawesome-all.min.css')
    shutil.copyfile(fontDir + 'fa-solid-900.woff2',
                    fontStore + 'fa-solid-900.woff2')
    shutil.copyfile(fontDir + 'fa-solid-900.ttf',
                    fontStore + 'fa-solid-900.ttf')

    if len(cluster_set):
        shutil.copyfile(jsDir + 'leaflet.markercluster.js',
                        jsStore + 'leaflet.markercluster.js')
        shutil.copyfile(cssDir + 'MarkerCluster.css',
                        cssStore + 'MarkerCluster.css')
        shutil.copyfile(cssDir + 'MarkerCluster.Default.css',
                        cssStore + 'MarkerCluster.Default.css')
    if layerSearch != "None":
        shutil.copyfile(jsDir + 'leaflet-search.js',
                        jsStore + 'leaflet-search.js')
        shutil.copyfile(cssDir + 'leaflet-search.css',
                        cssStore + 'leaflet-search.css')
        shutil.copytree(imageDir, imageStore)
    else:
        os.makedirs(imageStore)
    shutil.copyfile(os.path.join(imageDir, 'kambium-logo.png'),
                    os.path.join(imageStore, 'kambium-logo.png'))
    if address:
        shutil.copyfile(os.path.join(iconDir, 'search_position_icon.png'),
                        os.path.join(imageStore,
                                     'search_position_icon.png'))
    if layerSearch != "None":
        shutil.copyfile(os.path.join(iconDir, 'search_trees_icon.png'),
                        os.path.join(imageStore, 'search_trees_icon.png'))
    if filterItems != []:
        # At this stage filterItems contains QListWidgetItem instances. The
        # normalized filter dictionaries are only available to
        # writeHTMLstart(), which decides whether tailDT.js is referenced.
        shutil.copyfile(jsDir + 'tailDT.js',
                        jsStore + 'tailDT.js')
        shutil.copyfile(cssDir + 'filter.css',
                        cssStore + 'filter.css')
        shutil.copyfile(jsDir + 'nouislider.min.js',
                        jsStore + 'nouislider.min.js')
        shutil.copyfile(jsDir + 'wNumb.js',
                        jsStore + 'wNumb.js')
        shutil.copyfile(cssDir + 'nouislider.min.css',
                        cssStore + 'nouislider.min.css')
    if measure != "None":
        shutil.copyfile(jsDir + 'leaflet-measure.js',
                        jsStore + 'leaflet-measure.js')
        shutil.copyfile(cssDir + 'leaflet-measure.css',
                        cssStore + 'leaflet-measure.css')
    shutil.copytree(cssDir + 'images', cssStore + 'images')
    if (matchCRS and
            canvas.mapSettings().destinationCrs().authid() != 'EPSG:4326'):
        shutil.copyfile(jsDir + 'proj4.js', jsStore + 'proj4.js')
        shutil.copyfile(jsDir + 'proj4leaflet.js', jsStore + 'proj4leaflet.js')
    if useOFM:
        shutil.copyfile(jsDir + 'maplibre-gl.js', jsStore + 'maplibre-gl.js')
        shutil.copyfile(jsDir + 'leaflet-maplibre-gl.js',
                        jsStore + 'leaflet-maplibre-gl.js')
        shutil.copyfile(cssDir + 'maplibre-gl.css', cssStore + 'maplibre-gl.css')
    feedback.completeStep()
    return dataStore, cssStore


def writeHTMLstart(outputIndex, webpage_name, cluster_set, address, measure,
                   matchCRS, layerSearch, filterItems, useOFM, canvas, locate,
                   qgis2webJS, template, feedback, useMultiStyle, useHeat,
                   useShapes, useOSMB, useWMS, useWMTS, useVT,
                   useLabelgun=False):
    useCluster = False
    for cluster in cluster_set:
        if cluster:
            useCluster = True
    feedback.showFeedback("Writing HTML...")
    cssAddress = '<link rel="stylesheet" href="css/leaflet.css">'
    jsAddress = '<script src="js/leaflet.js"></script>'
    cssAddress += """
        <link rel="stylesheet" href="css/L.Control.Layers.Tree.css">"""
    jsAddress += """
        <script src="js/L.Control.Layers.Tree.min.js"></script>"""
    if locate:
        cssAddress += """
        <link rel="stylesheet" href="css/L.Control.Locate.min.css">"""
        jsAddress += """
        <script src="js/L.Control.Locate.min.js"></script>"""
    if useMultiStyle:
        jsAddress += """
        <script src="js/multi-style-layer.js"></script>"""
    if useHeat:
        jsAddress += """
        <script src="js/leaflet-heat.js"></script>"""
    if useVT:
        jsAddress += """
        <script src="js/Leaflet.VectorGrid.js"></script>"""
    if useShapes:
        jsAddress += """
        <script src="js/leaflet-svg-shape-markers.min.js"></script>"""
    jsAddress += """
        <script src="js/leaflet.rotatedMarker.js"></script>
        <script src="js/leaflet.pattern.js"></script>"""
    if useOSMB:
        jsAddress += """
        <script src="js/OSMBuildings-Leaflet.js"></script>"""
    extracss = '<link rel="stylesheet" href="css/qgis2web.css">'
    extracss += """
        <link rel="stylesheet" href="css/fontawesome-all.min.css">"""
    if useCluster:
        clusterCSS = """<link rel="stylesheet" href="css/MarkerCluster.css">
        <link rel="stylesheet" href="css/MarkerCluster.Default.css">"""
        clusterJS = '<script src="js/leaflet.markercluster.js">'
        clusterJS += "</script>"
    else:
        clusterCSS = ""
        clusterJS = ""
    if layerSearch != "None":
        layerSearchCSS = '<link rel="stylesheet" '
        layerSearchCSS += 'href="css/leaflet-search.css">'
        layerSearchJS = '<script src="js/leaflet-search.js"></script>'
    else:
        layerSearchCSS = ""
        layerSearchJS = ""
    if filterItems != []:
        layerFilterCSS = '<link rel="stylesheet" '
        layerFilterCSS += 'href="css/filter.css">\n'
        layerFilterCSS += '<link rel="stylesheet" '
        layerFilterCSS += 'href="css/nouislider.min.css">'
        layerFilterJS = ''
        if any(item["type"] in ["date", "datetime", "time"]
               for item in filterItems):
            layerFilterJS += '<script src="js/tailDT.js"></script>\n'
        layerFilterJS += '<script src="js/nouislider.min.js"></script>\n'
        layerFilterJS += '<script src="js/wNumb.js"></script>'
    else:
        layerFilterCSS = ""
        layerFilterJS = ""
    if useOFM:
        mapLibreCSS = '<link rel="stylesheet" href="css/maplibre-gl.css">'
        maplibreJS = """
        <script src="js/maplibre-gl.js"></script>
        <script src="js/leaflet-maplibre-gl.js"></script>"""
    else:
        mapLibreCSS = ""
        maplibreJS = ""
    if address:
        addressCSS = """
        <link rel="stylesheet" href="css/"""
        addressCSS += """leaflet.photon.css">"""
        addressJS = """
        <script src="js/leaflet.photon.js"></script>"""
    else:
        addressCSS = ""
        addressJS = ""
    if measure != "None":
        measureCSS = """
        <link rel="stylesheet" href="css/leaflet-measure.css">"""
        measureJS = """
        <script src="js/leaflet-measure.js"></script>"""
    else:
        measureCSS = ""
        measureJS = ""
    extraJS = """<script src="js/leaflet-hash.js"></script>
        <script src="js/Autolinker.min.js"></script>"""
    if useLabelgun:
        extraJS += """
        <script src="js/rbush.min.js"></script>
        <script src="js/labelgun.min.js"></script>
        <script src="js/labels.js"></script>"""
    if useWMS:
        extraJS += """
        <script src="js/leaflet.wms.js"></script>"""
    if useWMTS:
        extraJS += """
        <script src="js/leaflet-tilelayer-wmts.js"></script>"""
    if (matchCRS and
            canvas.mapSettings().destinationCrs().authid() != 'EPSG:4326'):
        crsJS = """
        <script src="js/proj4.js"></script>
        <script src="js/proj4leaflet.js"></script>"""
    else:
        crsJS = ""
    exp_js = """
        <script src="js/qgis2web_expressions.js"></script>"""

    canvasSize = canvas.size()
    values = {"@PAGETITLE@": webpage_name,
              "@CSSADDRESS@": cssAddress,
              "@EXTRACSS@": extracss,
              "@JSADDRESS@": jsAddress,
              "@LEAFLET_CLUSTERCSS@": clusterCSS,
              "@LEAFLET_CLUSTERJS@": clusterJS,
              "@LEAFLET_LAYERSEARCHCSS@": layerSearchCSS,
              "@LEAFLET_LAYERSEARCHJS@": layerSearchJS,
              "@LEAFLET_LAYERFILTERCSS@": layerFilterCSS,
              "@LEAFLET_LAYERFILTERJS@": layerFilterJS,
              "@LEAFLET_MAPLIBRECSS@": mapLibreCSS,
              "@LEAFLET_MAPLIBREJS@": maplibreJS,
              "@LEAFLET_ADDRESSCSS@": addressCSS,
              "@LEAFLET_MEASURECSS@": measureCSS,
              "@LEAFLET_EXTRAJS@": extraJS,
              "@LEAFLET_ADDRESSJS@": addressJS,
              "@LEAFLET_MEASUREJS@": measureJS,
              "@LEAFLET_CRSJS@": crsJS,
              "@QGIS2WEBJS@": qgis2webJS,
              "@MAP_WIDTH@": str(canvasSize.width()) + "px",
              "@MAP_HEIGHT@": str(canvasSize.height()) + "px",
              "@MAP_ASPECT_RATIO@": str(
                  canvasSize.width() / max(canvasSize.height(), 1)),
              "@EXP_JS@": exp_js,
              "@OL3_BACKGROUNDCOLOR@": "",
              "@OL3_STYLEVARS@": "",
              "@OL3_POPUP@": "",
              "@OL3_GEOJSONVARS@": "",
              "@OL3_WFSVARS@": "",
              "@OL3_PROJ4@": "",
              "@OL3_PROJDEF@": "",
              "@OL3_GEOCODINGLINKS@": "",
              "@OL3_GEOCODINGJS@": "",
              "@OL_MAPBOX_STYLE_JS@": "",
              "@OL3_LAYERSWITCHER@": "",
              "@OL3_LAYERS@": "",
              "@OL3_MEASURESTYLE@": "",
              "@MBGLJS_MEASURE@": "",
              "@MBGLJS_LOCATE@": ""}

    with codecs.open(outputIndex, 'w', encoding='utf-8') as f:
        base = replaceInTemplate(template + ".html", values)
        base = re.sub(r'\n[\s_]+\n', '\n', base)
        f.write(base)
        f.close()
    feedback.completeStep()


def writeCSS(cssStore, backgroundColor, feedback, widgetAccent,
             widgetBackground, layersList, labelBufferCSS=None):
    feedback.showFeedback("Writing CSS...")
    fontColor = LEAFLET_FONT_COLOR
    with open(cssStore + 'qgis2web.css', 'w') as f_css:
        text = """
        #map {
            background-color: """ + backgroundColor + """
        }
        html, body, #map {
            overflow: hidden;
        }
        body.qgis2web-canvas-size:not(.qgis2web-has-filters) {
            overflow: auto;
        }
        .qgis2web-layout {
            position: relative;
            display: grid;
            grid-template-columns: minmax(0, 1fr) clamp(280px, 22vw, 340px);
            width: 100%;
            height: 100vh;
            height: 100dvh;
            min-height: 0;
            overflow: hidden;
        }
        .qgis2web-map-panel {
            min-width: 0;
            height: 100%;
            overflow: hidden;
        }
        .qgis2web-has-filters #map {
            width: 100% !important;
            height: 100% !important;
            max-width: none !important;
            max-height: none !important;
            aspect-ratio: auto;
        }
        .qgis2web-filter-panel#menu {
            box-sizing: border-box;
            width: auto;
            height: 100%;
            min-width: 0;
            padding-bottom: calc(12px + env(safe-area-inset-bottom));
            overflow-x: hidden;
            overflow-y: auto;
            overscroll-behavior: contain;
            scrollbar-gutter: stable;
            background-color: """ + widgetBackground + """;
        }
        .qgis2web-filter-toggle,
        .qgis2web-filter-close,
        .qgis2web-filter-backdrop {
            display: none;
        }
        @media (max-width: 899px) {
            .qgis2web-layout {
                display: block;
            }
            .qgis2web-map-panel {
                width: 100%;
                height: 100%;
            }
            .qgis2web-filter-panel#menu {
                position: fixed;
                top: 0;
                right: 0;
                z-index: 2200;
                width: min(88vw, 360px);
                max-width: calc(100vw - 44px);
                height: 100vh;
                height: 100dvh;
                padding-top: calc(54px + env(safe-area-inset-top));
                padding-right: env(safe-area-inset-right);
                transform: translateX(105%);
                visibility: hidden;
                box-shadow: -8px 0 28px rgba(0, 0, 0, 0.24);
                transition: transform 220ms ease, visibility 0s linear 220ms;
            }
            .qgis2web-filter-toggle {
                position: fixed;
                top: calc(10px + env(safe-area-inset-top));
                right: calc(10px + env(safe-area-inset-right));
                z-index: 1800;
                display: inline-flex;
                min-width: 44px;
                min-height: 44px;
                padding: 0 14px;
                align-items: center;
                justify-content: center;
                font: 600 14px/1 "Helvetica Neue", Arial, sans-serif;
                color: """ + fontColor + """;
                background: """ + widgetBackground + """;
                border: 1px solid rgba(31, 77, 58, 0.3);
                border-radius: 8px;
                box-shadow: 0 3px 14px rgba(0, 0, 0, 0.25);
                cursor: pointer;
            }
            .qgis2web-filter-close {
                position: absolute;
                top: calc(8px + env(safe-area-inset-top));
                right: calc(8px + env(safe-area-inset-right));
                z-index: 1;
                display: inline-flex;
                width: 44px;
                height: 44px;
                padding: 0;
                align-items: center;
                justify-content: center;
                font: 30px/1 Arial, sans-serif;
                color: """ + fontColor + """;
                background: transparent;
                border: 0;
                border-radius: 6px;
                cursor: pointer;
            }
            .qgis2web-filter-close:hover,
            .qgis2web-filter-close:focus-visible,
            .qgis2web-filter-toggle:hover,
            .qgis2web-filter-toggle:focus-visible {
                background-color: rgba(31, 77, 58, 0.12);
                outline: 2px solid rgba(31, 77, 58, 0.45);
                outline-offset: 2px;
            }
            .qgis2web-filter-backdrop {
                position: fixed;
                inset: 0;
                z-index: 2100;
                display: block;
                background: rgba(12, 30, 23, 0.38);
                opacity: 0;
                visibility: hidden;
                transition: opacity 220ms ease, visibility 0s linear 220ms;
            }
            .qgis2web-filter-open .qgis2web-filter-panel#menu {
                transform: translateX(0);
                visibility: visible;
                transition: transform 220ms ease;
            }
            .qgis2web-filter-open .qgis2web-filter-backdrop {
                opacity: 1;
                visibility: visible;
                transition: opacity 220ms ease;
            }
        }
        @media (max-width: 479px) {
            .qgis2web-filter-panel#menu {
                width: 94vw;
                max-width: none;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            .qgis2web-filter-panel#menu,
            .qgis2web-filter-backdrop {
                transition: none;
            }
        }
        .leaflet-control.info {
            position: relative;
            box-sizing: border-box;
            min-width: 220px;
            max-width: min(420px, calc(100vw - 40px));
            padding: 16px 20px 20px 20px;
            overflow: hidden;
            background-color:""" + widgetBackground + """ !important;
            background-image: linear-gradient(135deg,
                rgba(31, 77, 58, 0.16), rgba(111, 136, 124, 0.03));
            color: """ + fontColor + """ !important;
            border: 1px solid rgba(31, 77, 58, 0.2);
            border-top: 4px solid #2c6e4f;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(31, 77, 58, 0.22),
                        inset 0 1px 0 rgba(255, 255, 255, 0.75) !important;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
        }
        .leaflet-control.info::after {
            position: absolute;
            bottom: 11px;
            left: 20px;
            width: 52px;
            height: 2px;
            content: "";
            background: linear-gradient(90deg, #2c6e4f, transparent);
            border-radius: 2px;
            box-shadow: 0 1px 3px rgba(31, 77, 58, 0.25);
        }
        .leaflet-control.info h2 {
            margin: 0;
            overflow-wrap: anywhere;
            font-family: "Palatino Linotype", "Book Antiqua", Palatino,
                         Georgia, serif;
            font-size: clamp(22px, 2vw, 30px);
            font-weight: 700;
            line-height: 1.15;
            letter-spacing: 0.025em;
            color: """ + fontColor + """ !important;
            text-shadow: 0 1px 0 rgba(255, 255, 255, 0.9),
                         0 3px 8px rgba(31, 77, 58, 0.18);
        }
        .leaflet-container {
            background: #fff;
            padding-right: 0;
        }
        .leaflet-popup-scrolled {
            border-bottom: unset!important;
            border-top: unset!important;
        }
        .leaflet-popup-content{
            max-height: 70vh;
            max-height: 70dvh;
            max-width: 70vw;
            overflow: auto;
            overflow-wrap: anywhere;
        }
        .leaflet-popup-content.media{
            width: auto!important;
            height: auto!important;
            overflow: auto;
        }
        .leaflet-popup-content th {
            text-align: left;
            vertical-align: top;
            min-width: 75px;
        }
        .leaflet-popup-content td {
            min-width: 75px;
        }
        .leaflet-popup-content td img {
            max-height: 60vh;
            max-height: 60dvh;
            max-width: 60vw;
        }
        .leaflet-popup-content video.popup-media {
            width: 400px;
            max-height: 60vh;
            max-height: 60dvh;
            max-width: 60vw;
        }
        .leaflet-popup-content audio.popup-media {
            max-width: 60vw;
        }
        /* placeholder shown while a lazily loaded popup image is fetched */
        .leaflet-popup-content img.lazy-pending {
            display: block;
            min-width: 120px;
            min-height: 90px;
            background-color: #e9e9e9;
            background-image: linear-gradient(90deg, #e9e9e9 0%, #f5f5f5 50%,
                                              #e9e9e9 100%);
            background-size: 200% 100%;
            animation: qgis2webLazyPulse 1.2s ease-in-out infinite;
        }
        .leaflet-popup-content img.lazy-error {
            min-width: 0;
            min-height: 0;
            background: none;
            animation: none;
        }
        @keyframes qgis2webLazyPulse {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .leaflet-tooltip {
            background: none;
            box-shadow: none;
            border: none;
        }
        .leaflet-tooltip-left:before, .leaflet-tooltip-right:before {
            border: 0px;
        }
        .fa {
            color: """ + widgetAccent + """ !important;
        }
        .leaflet-container, a {
            color: """ + fontColor + """ !important;
        }
        .leaflet-control-zoom-in, .leaflet-control-zoom-out,
        .leaflet-control-locate a,
        .leaflet-touch .leaflet-control-geocoder-icon,
        .leaflet-control-search .search-button,
         .leaflet-control-measure {
            background-color: """ + widgetBackground + """ !important;
            border-radius: 0px !important;
            color: """ + fontColor + """ !important;
        }
        .abstract {
            font: bold 18px 'Lucida Console', Monaco, monospace;
            text-indent: 1px;
            background-color: """ + widgetBackground + """ !important;
            width: 30px !important;
            color: """ + fontColor + """ !important;
            height: 30px !important;
            text-align: center !important;
            line-height: 30px !important;
        }
        .abstractUncollapsed {
            padding: 14px 16px;
            font: 12px/1.5 "Helvetica Neue", Arial, Helvetica, sans-serif;
            background-color:""" + widgetBackground + """ !important;
            color: """ + fontColor + """ !important;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            border-radius: 8px;
            max-width: min(240px, calc(100vw - 40px));
        }
        .abstract-credit {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            min-width: 160px;
            text-align: center;
        }
        .abstract-credit-label {
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.03em;
        }
        .abstract-credit-logo {
            display: block;
            width: 150px;
            max-width: 100%;
            height: auto;
            object-fit: contain;
            border-radius: 6px;
        }
        .abstract-credit-year {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.08em;
        }
        .leaflet-control {
            box-shadow: 0 3px 14px rgba(0, 0, 0, 0.4)!important;
            border-radius: 4px;
        }
        .leaflet-touch .leaflet-control-layers,
        .leaflet-touch .leaflet-bar,
        .leaflet-control-search,
        .leaflet-control-measure {
            border: 3px solid rgba(255,255,255,.4) !important;
        }
        .leaflet-control-attribution a {
            color: """ + fontColor + """ !important;
        }
        .leaflet-control-scale-line {
            border: 2px solid """ + widgetBackground + """ !important;
            border-top: none !important;
            color: """ + fontColor + """ !important;
        }
        .leaflet-control-search .search-button {
            width: 30px !important;
            height: 30px !important;
            font-size: 13px !important;
            text-align: center !important;
            cursor: pointer;
        }
        .leaflet-control-search .qgis2web-search-position,
        .leaflet-control-search .qgis2web-search-trees {
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-size: 24px 24px !important;
        }
        .leaflet-control-search .qgis2web-search-position {
            background-image: url('../images/search_position_icon.png') !important;
        }
        .leaflet-control-search .qgis2web-search-trees {
            background-image: url('../images/search_trees_icon.png') !important;
        }
        .leaflet-control-measure .leaflet-control {
            width: 30px !important;
            height: 30px !important;
        }
        .leaflet-container .leaflet-control-search{
            background: none !important;
        }
        .leaflet-control-search .search-input {
            margin: 0px 0px 0px 0px !important;
            height: 30px !important;
            color: """ + fontColor + """ !important;
        }
        .leaflet-control-search .search-input::placeholder {
            color: """ + fontColor + """ !important;
            opacity: 0.75;
        }
        .leaflet-control-measure {
            background: none!important;
            border-radius: 4px !important;
        }
        .leaflet-control-measure .leaflet-control-measure-interaction {
            background-color: """ + widgetBackground + """ !important;
            color: """ + fontColor + """ !important;
        }
        .leaflet-touch .leaflet-control-measure
        .leaflet-control-measure-toggle,
        .leaflet-touch .leaflet-control-measure
        .leaflet-control-measure-toggle:hover {
            width: 30px !important;
            height: 30px !important;
            border-radius: 0px !important;
            background-color: """ + widgetBackground + """ !important;
            color: """ + fontColor + """ !important;
            font-size: 13px;
            line-height: 30px;
            text-align: center;
            text-indent: 0%;
        }
        .leaflet-control-layers {
			padding: 2px;
			display: flex;
			flex-direction: column;
			align-items: flex-end;
            background-color: """ + widgetBackground + """ !important;
            color: """ + fontColor + """ !important;

		}
        .leaflet-control-layers-expanded {
			padding-left: 6px;
			max-width: min(360px, calc(100vw - 80px));
		}
        .leaflet-control-layers-list,
        .leaflet-control-layers-scrollbar {
            max-height: calc(100vh - 140px) !important;
            max-height: calc(100dvh - 140px) !important;
            overflow-x: hidden;
            overflow-y: auto;
            overscroll-behavior: contain;
		}
        .leaflet-control-layers-expanded .leaflet-control-layers-toggle {
            display: block;
            background-image: none;
			text-decoration: none;
            margin-bottom: 3px;
        }
        .leaflet-control-layers-expanded .leaflet-control-layers-toggle::after {
            content: '»';
            font-size: x-large;
            color: """ + fontColor + """ !important;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            text-align: center;
        }
        .leaflet-overlay-pane {
            z-index: 550;
        }
        .leaflet-popup-pane {
            z-index: 700;
        }
        #gcd-button-control {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .leaflet-marker-icon{
            white-space: nowrap;
        }
        .leaflet-control-search .search-input,
        .leaflet-control-measure .leaflet-control-measure-interaction {
            box-sizing: border-box;
            max-width: calc(100vw - 80px);
        }
        @media (max-width: 899px) {
            .qgis2web-has-filters .leaflet-top.leaflet-right {
                top: 56px;
            }
            .leaflet-control.info {
                min-width: 0;
                max-width: calc(100vw - 92px);
                padding: 11px 14px 16px;
                border-top-width: 3px;
                border-radius: 9px;
            }
            .leaflet-control.info::after {
                bottom: 8px;
                left: 14px;
                width: 40px;
            }
            .leaflet-control.info h2 {
                font-size: clamp(18px, 5vw, 24px);
                line-height: 1.12;
            }
            .leaflet-control-layers-expanded {
                max-width: calc(100vw - 72px);
                padding-left: 4px;
            }
            .leaflet-control-layers-list,
            .leaflet-control-layers-scrollbar {
                max-height: 52vh !important;
                max-height: 52dvh !important;
            }
            .leaflet-control-layers label {
                line-height: 1.55;
            }
            .leaflet-touch .leaflet-bar a,
            .leaflet-touch .leaflet-control-layers-toggle,
            .leaflet-touch .leaflet-control-geocoder-icon,
            .leaflet-control-search .search-button,
            .leaflet-touch .leaflet-control-measure .leaflet-control-measure-toggle {
                box-sizing: border-box;
                width: 44px !important;
                height: 44px !important;
                min-width: 44px;
                min-height: 44px;
                font-size: 18px !important;
                line-height: 44px !important;
            }
            .leaflet-control-search .search-input {
                width: min(230px, calc(100vw - 100px)) !important;
                height: 44px !important;
            }
            .leaflet-control-search .qgis2web-search-position,
            .leaflet-control-search .qgis2web-search-trees {
                background-size: 32px 32px !important;
            }
            .leaflet-control-measure .leaflet-control-measure-interaction {
                width: min(280px, calc(100vw - 28px));
                max-height: 70vh;
                max-height: 70dvh;
                overflow: auto;
            }
            .abstractUncollapsed {
                max-width: min(190px, calc(100vw - 72px));
                padding: 10px 12px;
            }
            .abstract-credit {
                min-width: 0;
            }
            .abstract-credit-logo {
                width: 110px;
            }
            .leaflet-popup-content {
                width: auto !important;
                max-width: calc(100vw - 76px);
                max-height: 65vh;
                max-height: 65dvh;
                margin: 14px 18px;
            }
            .leaflet-popup-content table {
                max-width: 100%;
            }
            .leaflet-popup-content td img,
            .leaflet-popup-content video.popup-media,
            .leaflet-popup-content audio.popup-media {
                width: auto;
                max-width: 100%;
                height: auto;
            }
            .leaflet-bottom {
                bottom: env(safe-area-inset-bottom);
            }
            .leaflet-left {
                left: env(safe-area-inset-left);
            }
            .leaflet-right {
                right: env(safe-area-inset-right);
            }
        }
        @media (max-width: 479px) {
            .leaflet-control.info {
                max-width: calc(100vw - 76px);
            }
            .leaflet-popup-content {
                max-width: calc(100vw - 54px);
                margin-right: 12px;
                margin-left: 12px;
            }
        }
        """
        if (layersList == "Collapsed"):
            text +="""
        .leaflet-control-layers-expanded .leaflet-control-layers-toggle {
            display: none;
        }"""
        if labelBufferCSS:
            for safeLayerName, color, size in labelBufferCSS:
                size_int = int(round(size))
                shadows = []
                for dx in range(-size_int, size_int + 1):
                    for dy in range(-size_int, size_int + 1):
                        if dx == 0 and dy == 0:
                            continue
                        shadows.append(f"{dx}px {dy}px 0 {color}")
                shadow_text = ",\n                ".join(shadows)
                text += f"""
        .css_{safeLayerName} {{
            pointer-events: none!important;
            text-shadow: {shadow_text};
        }}"""
        f_css.write(text)
        f_css.close()
    feedback.completeStep()
