/**
 * Created by red on 10/29/15.
 */
//for mobile layout..
function fullview() {
    console.log('html resize, header layout control.');
    $("html").css("min-width", "1200px");
    $("*[data-btn=gnb]").hide();
    $("#global-navigation h1").css("float", "left").css("padding-right", "15px").css("margin", "10px 10px 0 0").css("padding-bottom", "10px").css("padding-top", "0px").css("width", "auto");
    $("#global-navigation h2").css("margin-top", "25px").css("text-align", "left").css("width", "auto");
    $("ol.user").show();
}