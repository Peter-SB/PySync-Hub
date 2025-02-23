document.body.addEventListener("htmx:afterSwap", function(evt) {
var banner = document.getElementById("export-complete-banner");
if (banner) {
  setTimeout(function(){
    banner.style.transition = "opacity 0.5s ease-out";
    banner.style.opacity = "0";
    setTimeout(function(){ banner.remove(); }, 500);
  }, 1200);
}
});