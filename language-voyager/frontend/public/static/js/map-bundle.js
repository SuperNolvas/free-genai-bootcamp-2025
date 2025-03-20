import l,{useEffect as A,useState as B}from"react";import s from"react";import{forwardRef as w,createElement as P}from"react";var i=a=>a.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),f=(...a)=>a.filter((e,t,u)=>!!e&&e.trim()!==""&&u.indexOf(e)===t).join(" ").trim();import{forwardRef as g,createElement as n}from"react";var c={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"};var p=g(({color:a="currentColor",size:e=24,strokeWidth:t=2,absoluteStrokeWidth:u,className:r="",children:o,iconNode:I,...x},C)=>n("svg",{ref:C,...c,width:e,height:e,stroke:a,strokeWidth:u?Number(t)*24/Number(e):t,className:f("lucide",r),...x},[...I.map(([S,h])=>n(S,h)),...Array.isArray(o)?o:[o]]));var L=(a,e)=>{let t=w(({className:u,...r},o)=>P(p,{ref:o,iconNode:e,className:f(`lucide-${i(a)}`,u),...r}));return t.displayName=`${a}`,t};var k=[["path",{d:"M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",key:"1r0f0z"}],["circle",{cx:"12",cy:"10",r:"3",key:"ilqhr7"}]],d=L("MapPin",k);function m({location:a}){return!a?.latitude||!a?.longitude?null:s.createElement("div",{className:"flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm shadow-lg"},s.createElement(d,{className:"h-5 w-5"}),s.createElement("span",null,"Location: ",a.latitude.toFixed(4),", ",a.longitude.toFixed(4),a.accuracy&&` (\xB1${Math.round(a.accuracy)}m)`))}function F(){let[a,e]=B(!0);return A(()=>{let t=()=>{e(!1)};return window.addEventListener("map:ready",t),window.MapManager?.view&&e(!1),()=>{window.removeEventListener("map:ready",t)}},[]),l.createElement("div",{className:"relative w-full h-full"},a&&l.createElement("div",{className:"absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-90 z-10"},l.createElement("div",{className:"w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"}),l.createElement("p",{className:"text-gray-700"},"Loading map...")),l.createElement(m,null))}export{F as default};
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

lucide-react/dist/esm/lucide-react.js:
  (**
   * @license lucide-react v0.483.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)
*/
