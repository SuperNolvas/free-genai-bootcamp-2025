import t,{useEffect as v,useState as I}from"react";import F from"@arcgis/core/Map";import D from"@arcgis/core/views/MapView";import n from"@arcgis/core/Graphic";import w from"@arcgis/core/geometry/Point";import C from"@arcgis/core/symbols/SimpleMarkerSymbol";import R from"@arcgis/core/symbols/SimpleFillSymbol";var h=class{constructor(){this.map=null;this.view=null;this.locationMarker=null;this.poiMarkers=new Map;this.regionPolygons=new Map;this.locationListeners=[];this.TOKYO_CENTER={latitude:35.6762,longitude:139.6503}}async initialize(a){this.map=new F({basemap:"streets-vector"}),this.view=new D({container:a,map:this.map,center:[this.TOKYO_CENTER.longitude,this.TOKYO_CENTER.latitude],zoom:12});let e=new C({color:"#2196f3",outline:{color:"#ffffff",width:2},size:12});return this.locationMarker=new n({symbol:e}),this.view.graphics.add(this.locationMarker),this.addRegionPolygon({id:"tokyo",name:"Tokyo",center_lat:this.TOKYO_CENTER.latitude,center_lon:this.TOKYO_CENTER.longitude,bounds:{north:35.8187,south:35.5311,east:139.9224,west:139.5804}}),this.view}onLocationChange(a){return this.locationListeners.push(a),()=>{this.locationListeners=this.locationListeners.filter(e=>e!==a)}}notifyLocationChange(a){this.locationListeners.forEach(e=>e(a))}updateLocation(a,e){this.view&&this.view.goTo({center:[e,a],zoom:15})}updateLocationMarker(a){if(!this.view||!a.latitude||!a.longitude)return;let e=new w({longitude:a.longitude,latitude:a.latitude,spatialReference:{wkid:4326}});if(this.locationMarker)this.locationMarker.geometry=e;else{let o=new C({color:"#2196f3",outline:{color:"#ffffff",width:2},size:12});this.locationMarker=new n({geometry:e,symbol:o}),this.view.graphics.add(this.locationMarker)}this.updateLocation(a.latitude,a.longitude),this.notifyLocationChange(a)}addPOI(a){if(!this.map||!this.view)return;let e=new w({longitude:a.lon,latitude:a.lat,spatialReference:{wkid:4326}}),o=new C({color:"#4caf50",outline:{color:"#ffffff",width:1},size:10}),d=new n({geometry:e,symbol:o,attributes:{id:a.id,name:a.name,type:a.type},popupTemplate:{title:a.local_name||a.name,content:[{type:"fields",fieldInfos:[{fieldName:"type",label:"Type"}]}]}});this.view.graphics.add(d),this.poiMarkers.set(a.id,d)}addRegionPolygon(a){if(!this.view)return;let e={type:"polygon",rings:[[[a.bounds?.west||a.center_lon-.1,a.bounds?.south||a.center_lat-.1],[a.bounds?.east||a.center_lon+.1,a.bounds?.south||a.center_lat-.1],[a.bounds?.east||a.center_lon+.1,a.bounds?.north||a.center_lat+.1],[a.bounds?.west||a.center_lon-.1,a.bounds?.north||a.center_lat+.1],[a.bounds?.west||a.center_lon-.1,a.bounds?.south||a.center_lat-.1]]],spatialReference:{wkid:4326}},o=new R({color:[51,51,204,.2],outline:{color:[51,51,204],width:1}}),d=new n({geometry:e,symbol:o,attributes:{id:a.id,name:a.name}});this.regionPolygons.set(a.id,d),this.view.graphics.add(d)}removePOI(a){let e=this.poiMarkers.get(a);e&&this.view&&(this.view.graphics.remove(e),this.poiMarkers.delete(a))}removeRegion(a){let e=this.regionPolygons.get(a);e&&this.view&&(this.view.graphics.remove(e),this.regionPolygons.delete(a))}clearAll(){this.view&&(this.view.graphics.removeAll(),this.poiMarkers.clear(),this.regionPolygons.clear(),this.locationMarker&&this.view.graphics.add(this.locationMarker))}refresh(){this.view&&this.view.goTo({center:[this.TOKYO_CENTER.longitude,this.TOKYO_CENTER.latitude],zoom:12})}destroy(){this.view&&this.view.destroy()}},T=new h,p=T;import{forwardRef as q,createElement as b}from"react";var P=u=>u.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),m=(...u)=>u.filter((a,e,o)=>!!a&&a.trim()!==""&&o.indexOf(a)===e).join(" ").trim();import{forwardRef as y,createElement as A}from"react";var k={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"};var B=y(({color:u="currentColor",size:a=24,strokeWidth:e=2,absoluteStrokeWidth:o,className:d="",children:l,iconNode:x,...c},g)=>A("svg",{ref:g,...k,width:a,height:a,stroke:u,strokeWidth:o?Number(e)*24/Number(a):e,className:m("lucide",d),...c},[...x.map(([r,f])=>A(r,f)),...Array.isArray(l)?l:[l]]));var L=(u,a)=>{let e=q(({className:o,...d},l)=>b(B,{ref:l,iconNode:a,className:m(`lucide-${P(u)}`,o),...d}));return e.displayName=`${u}`,e};var U=[["path",{d:"M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",key:"1r0f0z"}],["circle",{cx:"12",cy:"10",r:"3",key:"ilqhr7"}]],s=L("MapPin",U);var O=[["polygon",{points:"3 11 22 2 13 21 11 13 3 11",key:"1ltx0t"}]],i=L("Navigation",O);function H(){let[u,a]=I(!1),[e,o]=I(!1),[d,l]=I(null),[x,c]=I(!0);return v(()=>{let r=document.getElementById("map-container");if(!r){console.error("Map container not found");return}(async()=>{try{await p.initialize(r),c(!1)}catch(M){console.error("Failed to initialize map:",M),c(!1)}})();let S=()=>{p.refresh()};return window.addEventListener("map:refresh",S),()=>{window.removeEventListener("map:refresh",S)}},[]),t.createElement(t.Fragment,null,x&&t.createElement("div",{className:"absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-90 z-10"},t.createElement("div",{className:"w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"}),t.createElement("p",{className:"text-gray-700"},"Loading map...")),t.createElement("div",{className:"absolute bottom-4 right-4"},t.createElement("button",{onClick:()=>o(!e),className:"flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-lg hover:bg-gray-100"},t.createElement(s,{className:"h-4 w-4"})),e&&t.createElement("div",{className:"absolute bottom-12 right-0 w-64 rounded-lg bg-white p-4 shadow-lg"},t.createElement("div",{className:"mb-4"},t.createElement("h3",{className:"font-medium"},"Map Controls"),t.createElement("p",{className:"text-sm text-gray-600"},u?"Your location is being tracked":"Location tracking is disabled")),t.createElement("button",{onClick:()=>{if(u&&d!==null)navigator.geolocation.clearWatch(d),l(null),a(!1);else if("geolocation"in navigator){let r=navigator.geolocation.watchPosition(f=>{p.updateLocationMarker({latitude:f.coords.latitude,longitude:f.coords.longitude,accuracy:f.coords.accuracy})},f=>{console.error("Geolocation error:",f),a(!1)});l(r),a(!0)}},className:`w-full rounded-md px-4 py-2 text-sm font-medium text-white ${u?"bg-red-500 hover:bg-red-600":"bg-blue-500 hover:bg-blue-600"}`},t.createElement("span",{className:"flex items-center justify-center"},u?t.createElement(t.Fragment,null,t.createElement(s,{className:"mr-2 h-4 w-4"}),"Stop Tracking"):t.createElement(t.Fragment,null,t.createElement(i,{className:"mr-2 h-4 w-4"}),"Start Tracking"))))))}export{H as default};
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
