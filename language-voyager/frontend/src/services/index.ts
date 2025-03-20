import arcgisService from './arcgis';

export const cleanup = () => {
  // Cleanup ArcGIS resources
  arcgisService.destroy();
};

export { arcgisService };