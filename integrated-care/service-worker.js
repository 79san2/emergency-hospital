const CACHE='care-seoul-pwa-v3';
const FILES=['./','./index.html','./data.json','./manifest.json','./icon.svg'];
self.addEventListener('install',event=>{
 event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(FILES);await self.skipWaiting()})());
});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{const keys=await caches.keys();await Promise.all(keys.filter(k=>k.startsWith('care-seoul-pwa-')&&k!==CACHE).map(k=>caches.delete(k)));await self.clients.claim()})());
});
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url);
 const inApp=url.pathname.includes('/integrated-care/');
 if(url.origin!==self.location.origin||!inApp)return;
 const isPage=event.request.mode==='navigate'||url.pathname.endsWith('/index.html')||url.pathname.endsWith('/integrated-care/');
 const isData=url.pathname.endsWith('/data.json');
 if(isPage||isData){
  event.respondWith((async()=>{
   try{
    const response=await fetch(event.request,{cache:'no-store'});
    if(response.ok){const cache=await caches.open(CACHE);await cache.put(event.request,response.clone())}
    return response;
   }catch(error){
    const cache=await caches.open(CACHE);
    return (await cache.match(event.request,{ignoreSearch:true}))||(await cache.match(isData?'./data.json':'./index.html'))||Response.error();
   }
  })());
  return;
 }
 event.respondWith((async()=>{
  const cached=await caches.match(event.request);
  if(cached)return cached;
  try{const response=await fetch(event.request);if(response.ok){const cache=await caches.open(CACHE);await cache.put(event.request,response.clone())}return response}
  catch(error){return Response.error()}
 })());
});