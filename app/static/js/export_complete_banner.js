document.body.addEventListener("htmx:afterSwap", function(evt) {
console.log("htmx:afterSwap event fired", evt.detail);
var banner = document.getElementById("export-complete-banner");
if (banner) {
  console.log("Banner exists, setting timeout");
  setTimeout(function(){
    banner.style.transition = "opacity 0.5s ease-out";
    banner.style.opacity = "0";
    setTimeout(function(){ banner.remove(); }, 500);
    console.log("Banner faded out");
  }, 1200);
}
});