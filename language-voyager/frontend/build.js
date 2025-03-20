const esbuild = require('esbuild');
const aliasPlugin = require('esbuild-plugin-alias');
const path = require('path');

// Build ArcGIS dependencies
esbuild.build({
  entryPoints: ['./src/services/arcgis.ts'],
  bundle: true,
  minify: true,
  sourcemap: false,
  target: ['es2020'],
  outfile: './public/static/js/arcgis-bundle.js',
  format: 'esm',
  logLevel: 'info',
  metafile: true,
  plugins: [
    aliasPlugin({
      '@': path.resolve(__dirname, 'src')
    })
  ],
  define: {
    'process.env.NODE_ENV': '"production"'
  },
  treeShaking: true
}).then((arcgisResult) => {
  // Build the map component bundle
  return esbuild.build({
    entryPoints: ['./src/pages/Map.tsx'],
    bundle: true,
    minify: true,
    sourcemap: false,
    target: ['es2020'],
    outfile: './public/static/js/map-bundle.js',
    external: ['react', 'react-dom', '@arcgis/core'],
    format: 'esm',
    logLevel: 'info',
    metafile: true,
    plugins: [
      aliasPlugin({
        '@': path.resolve(__dirname, 'src')
      })
    ],
    define: {
      'process.env.NODE_ENV': '"production"'
    },
    treeShaking: true,
    loader: {
      '.png': 'file',
      '.svg': 'file',
      '.jpg': 'file'
    }
  });
}).then((result) => {
  if (result.metafile) {
    const analysis = esbuild.analyzeMetafile(result.metafile);
    console.log(analysis);
  }
}).catch((error) => {
  console.error('Build failed:', error);
  process.exit(1);
});