var window_W = 0;

$(document).ready(function() {
	window_W = $(window).width();
	$(window).resize(resize);
/***
	$(".univ-more").on("click", function() {
		$(this).toggleClass('on');
		if(window_W>768) {
			$(".university-listing [data-hidden]").toggle();
		} else {
			$(".university-listing [data-hidden=true]").toggle();
		}
		return false;
	});
***/
	$(".community-container-wrap > a").on("click", function() {
		$(".community-container-wrap > a").removeClass("on");
		$(this).addClass("on");
		return false;
	});

	$(".faq-list dt > a").on("click", function() {
		$(".faq-list dt").removeClass("on");
		$(this).parent().addClass("on");
		return false;
	});

	$(".kmooc-tab a").on("click", function() {
		$(".kmooc-tab a").removeClass("on");
		$(this).addClass("on");
		$(".kmooc-box").hide();
		$($(this).attr("href")).show();
		return false;
	});


});


var univ_bx;
$(window).load(function() {

		if($(".slider-back").length>0) {
			$(".header-slider").bxSlider({
				pager : false,
				mode : "fade",
				auto : true,
				controls : false,
				speed : 1000
			});
		}

		if($(".university-listing").length>0) {
			univ_bx = $(".university-listing").bxSlider({
				pager : false,
				auto : false,
				controls : true,
				minSlides: 5,
    			maxSlides: 5,
			    slideMargin: 0,
			    slideWidth : 250
			});
		}
});

function resize() {
	window_W = $(window).width();
	if(window_W<=768) {
		univ_bx.reloadSlider({
				pager : false,
				auto : false,
				controls : true,
				minSlides: 3,
    			maxSlides: 3,
			    slideMargin: 0,
			    slideWidth : 250
			});
	} else if(window_W>768) {
		univ_bx.reloadSlider({
				pager : false,
				auto : false,
				controls : true,
				minSlides: 5,
    			maxSlides: 5,
			    slideMargin: 0,
			    slideWidth : 250
			});
	}
}