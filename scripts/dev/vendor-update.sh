#!/usr/bin/env bash
set -euo pipefail

APP_DIR="core/static/vendor"

npm install

echo "==> jQuery"
cp node_modules/jquery/dist/jquery.min.js "$APP_DIR/"

echo "==> htmx"
cp node_modules/htmx.org/dist/htmx.min.js "$APP_DIR/"

echo "==> summernote"
mkdir -p "$APP_DIR/summernote/font" "$APP_DIR/summernote/lang"
cp node_modules/summernote/dist/summernote-lite.min.js "$APP_DIR/summernote/"
cp node_modules/summernote/dist/summernote-lite.min.css "$APP_DIR/summernote/"
cp node_modules/summernote/dist/font/summernote.* "$APP_DIR/summernote/font/"
cp node_modules/summernote/dist/lang/summernote-*.js "$APP_DIR/summernote/lang/"

echo "==> bulma"
cp node_modules/bulma/css/bulma.min.css "$APP_DIR/"

echo "==> mdi (Material Design Icons) - css + fonts ensemble (chemins relatifs)"
mkdir -p "$APP_DIR/mdi/css" "$APP_DIR/mdi/fonts"
cp node_modules/@mdi/font/css/materialdesignicons.min.css "$APP_DIR/mdi/css/"
cp node_modules/@mdi/font/fonts/materialdesignicons-webfont.* "$APP_DIR/mdi/fonts/"

echo "==> chart.js"
cp node_modules/chart.js/dist/chart.umd.min.js "$APP_DIR/"

echo "==> d3"
cp node_modules/d3/dist/d3.min.js "$APP_DIR/"

echo "==> family-chart"
cp node_modules/family-chart/dist/family-chart.min.js "$APP_DIR/"
cp node_modules/family-chart/dist/family-chart.min.css "$APP_DIR/"

echo "==> hyperscript"
cp node_modules/hyperscript.org/dist/_hyperscript.min.js "$APP_DIR/"

echo "==> select2"
cp node_modules/select2/dist/js/select2.full.min.js "$APP_DIR/"
cp node_modules/select2/dist/css/select2.min.css "$APP_DIR/"

echo "Vendoring terminé."
