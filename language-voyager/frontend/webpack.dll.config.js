const path = require('path');
const webpack = require('webpack');

module.exports = {
  mode: 'production',
  entry: {
    arcgis: ['@arcgis/core'],
  },
  output: {
    filename: '[name]-dll.js',
    path: path.resolve(__dirname, 'public/static/js'),
    library: '[name]_dll',
  },
  plugins: [
    new webpack.DllPlugin({
      name: '[name]_dll',
      path: path.resolve(__dirname, 'public/static/js/[name]-manifest.json'),
    }),
  ],
};