import t,{useEffect as M,useRef as O,useState as I}from"react";import F from"@arcgis/core/Map";import D from"@arcgis/core/views/MapView";import p from"@arcgis/core/Graphic";import w from"@arcgis/core/geometry/Point";import h from"@arcgis/core/symbols/SimpleMarkerSymbol";import R from"@arcgis/core/symbols/SimpleFillSymbol";var g=class{constructor(){this.map=null;this.view=null;this.locationMarker=null;this.poiMarkers=new Map;this.regionPolygons=new Map;this.locationListeners=[]}async initialize(a){this.map=new F({basemap:"streets-vector"}),this.view=new D({container:a,map:this.map,zoom:15});let e=new h({color:"#2196f3",outline:{color:"#ffffff",width:2},size:12});return this.locationMarker=new p({symbol:e}),this.view.graphics.add(this.locationMarker),this.view}onLocationChange(a){return this.locationListeners.push(a),()=>{this.locationListeners=this.locationListeners.filter(e=>e!==a)}}notifyLocationChange(a){this.locationListeners.forEach(e=>e(a))}updateLocation(a,e){this.view&&this.view.goTo({center:[e,a],zoom:15})}updateLocationMarker(a){if(!this.view||!a.latitude||!a.longitude)return;let e=new w({longitude:a.longitude,latitude:a.latitude,spatialReference:{wkid:4326}});if(this.locationMarker)this.locationMarker.geometry=e;else{let u=new h({color:"#2196f3",outline:{color:"#ffffff",width:2},size:12});this.locationMarker=new p({geometry:e,symbol:u}),this.view.graphics.add(this.locationMarker)}this.updateLocation(a.latitude,a.longitude),this.notifyLocationChange(a)}addPOI(a){if(!this.map||!this.view)return;let e=new w({longitude:a.lon,latitude:a.lat,spatialReference:{wkid:4326}}),u=new h({color:"#4caf50",outline:{color:"#ffffff",width:1},size:10}),d=new p({geometry:e,symbol:u,attributes:{id:a.id,name:a.name,type:a.type},popupTemplate:{title:a.local_name||a.name,content:[{type:"fields",fieldInfos:[{fieldName:"type",label:"Type"}]}]}});this.view.graphics.add(d),this.poiMarkers.set(a.id,d)}addRegionPolygon(a){if(!this.view)return;let e={type:"polygon",rings:[[[a.center_lon-.1,a.center_lat-.1],[a.center_lon+.1,a.center_lat-.1],[a.center_lon+.1,a.center_lat+.1],[a.center_lon-.1,a.center_lat+.1],[a.center_lon-.1,a.center_lat-.1]]],spatialReference:{wkid:4326}},u=new R({color:[51,51,204,.2],outline:{color:[51,51,204],width:1}}),d=new p({geometry:e,symbol:u,attributes:{id:a.id,name:a.name}});this.regionPolygons.set(a.id,d),this.view.graphics.add(d)}removePOI(a){let e=this.poiMarkers.get(a);e&&this.view&&(this.view.graphics.remove(e),this.poiMarkers.delete(a))}removeRegion(a){let e=this.regionPolygons.get(a);e&&this.view&&(this.view.graphics.remove(e),this.regionPolygons.delete(a))}clearAll(){this.view&&(this.view.graphics.removeAll(),this.poiMarkers.clear(),this.regionPolygons.clear(),this.locationMarker&&this.view.graphics.add(this.locationMarker))}destroy(){this.view&&this.view.destroy()}},T=new g,S=T;import{forwardRef as q,createElement as b}from"react";var P=o=>o.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),m=(...o)=>o.filter((a,e,u)=>!!a&&a.trim()!==""&&u.indexOf(a)===e).join(" ").trim();import{forwardRef as y,createElement as A}from"react";var k={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"};var B=y(({color:o="currentColor",size:a=24,strokeWidth:e=2,absoluteStrokeWidth:u,className:d="",children:l,iconNode:c,...x},n)=>A("svg",{ref:n,...k,width:a,height:a,stroke:o,strokeWidth:u?Number(e)*24/Number(a):e,className:m("lucide",d),...x},[...c.map(([C,r])=>A(C,r)),...Array.isArray(l)?l:[l]]));var L=(o,a)=>{let e=q(({className:u,...d},l)=>b(B,{ref:l,iconNode:a,className:m(`lucide-${P(o)}`,u),...d}));return e.displayName=`${o}`,e};var U=[["path",{d:"M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",key:"1r0f0z"}],["circle",{cx:"12",cy:"10",r:"3",key:"ilqhr7"}]],f=L("MapPin",U);var v=[["polygon",{points:"3 11 22 2 13 21 11 13 3 11",key:"1ltx0t"}]],i=L("Navigation",v);function H(){let o=O(null),[a,e]=I(!1),[u,d]=I(!1),[l,c]=I(null),[x,n]=I(!0);M(()=>{o.current&&S.initialize(o.current).then(()=>n(!1)).catch(r=>{console.error("Failed to initialize map:",r),n(!1)})},[]);let C=()=>{if(a&&l!==null)navigator.geolocation.clearWatch(l),c(null),e(!1);else if("geolocation"in navigator){let r=navigator.geolocation.watchPosition(s=>{S.updateLocationMarker({type:"location_update",status:"ok",latitude:s.coords.latitude,longitude:s.coords.longitude,accuracy:s.coords.accuracy,timestamp:new Date().toISOString()})},s=>{console.error("Error getting location:",s)},{enableHighAccuracy:!0,timeout:5e3,maximumAge:0});c(r),e(!0)}};return M(()=>()=>{l!==null&&navigator.geolocation.clearWatch(l)},[l]),t.createElement("div",{className:"relative h-full w-full"},x&&t.createElement("div",{className:"absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-75 z-10"},t.createElement("div",{className:"flex flex-col items-center space-y-4"},t.createElement("div",{className:"w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"}),t.createElement("p",{className:"text-gray-700"},"Loading map..."))),t.createElement("div",{ref:o,className:"h-full w-full"}),t.createElement("div",{className:"absolute bottom-4 right-4"},t.createElement("button",{onClick:()=>d(!u),className:"flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-lg hover:bg-gray-100"},t.createElement(f,{className:"h-4 w-4"})),u&&t.createElement("div",{className:"absolute bottom-12 right-0 w-64 rounded-lg bg-white p-4 shadow-lg"},t.createElement("div",{className:"mb-4"},t.createElement("h3",{className:"font-medium"},"Map Controls"),t.createElement("p",{className:"text-sm text-gray-600"},a?"Your location is being tracked":"Location tracking is disabled")),t.createElement("button",{onClick:C,className:`w-full rounded-md px-4 py-2 text-sm font-medium text-white ${a?"bg-red-500 hover:bg-red-600":"bg-blue-500 hover:bg-blue-600"}`},t.createElement("span",{className:"flex items-center justify-center"},a?t.createElement(t.Fragment,null,t.createElement(f,{className:"mr-2 h-4 w-4"}),"Stop Tracking"):t.createElement(t.Fragment,null,t.createElement(i,{className:"mr-2 h-4 w-4"}),"Start Tracking"))))))}export{H as default};
/*! Bundled license information:

lucide-react/dist/esm/shared/src/utils.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)

lucide-react/dist/esm/defaultAttributes.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)

lucide-react/dist/esm/Icon.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)

lucide-react/dist/esm/createLucideIcon.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)

lucide-react/dist/esm/icons/map-pin.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)

lucide-react/dist/esm/icons/navigation.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)

lucide-react/dist/esm/lucide-react.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)
*/
