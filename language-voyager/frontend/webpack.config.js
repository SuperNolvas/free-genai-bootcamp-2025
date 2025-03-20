const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: './src/pages/Map.tsx',
  mode: 'production',
  output: {
    filename: 'map-bundle.js',
    path: path.resolve(__dirname, 'public/static/js'),
    clean: true,
    publicPath: 'http://localhost:8000/'
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      'react': path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom')
    },
    fallback: {
      "path": false,
      "fs": false,
      "crypto": false
    }
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: {
          loader: 'ts-loader',
          options: {
            transpileOnly: true
          }
        },
        exclude: /node_modules/
      }
    ]
  },
  plugins: [
    new webpack.container.ModuleFederationPlugin({
      name: 'map',
      filename: 'map-bundle.js',
      exposes: {
        './Map': './src/pages/Map.tsx'
      },
      shared: {
        react: { 
          singleton: true,
          eager: true,
          requiredVersion: '^18.2.0',
          import: 'react', // Add explicit import
          shareKey: 'react', // Add explicit share key
          shareScope: 'default' // Add explicit share scope
        },
        'react-dom': {
          singleton: true,
          eager: true,
          requiredVersion: '^18.2.0',
          import: 'react-dom', // Add explicit import
          shareKey: 'react-dom', // Add explicit share key
          shareScope: 'default' // Add explicit share scope
        },
        '@arcgis/core': {
          singleton: true,
          eager: true,
          requiredVersion: '^4.32.8'
        }
      }
    })
  ],
  optimization: {
    minimize: true,
    moduleIds: 'deterministic',
    chunkIds: 'deterministic',
    mangleExports: true,
    concatenateModules: true
  }
};