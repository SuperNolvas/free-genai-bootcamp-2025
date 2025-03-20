const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: './src/pages/Map.tsx',
  mode: 'production',
  output: {
    filename: 'map-bundle.js',
    path: path.resolve(__dirname, 'public/static/js'),
    clean: true,
    publicPath: 'auto'
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
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
        '@arcgis/core': {
          singleton: true,
          eager: true,
          requiredVersion: '^4.32.8'
        },
        'react': {
          singleton: true,
          requiredVersion: '^18.2.0'
        },
        'react-dom': {
          singleton: true,
          requiredVersion: '^18.2.0'
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