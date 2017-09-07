$(document).ready(function() {
	
	/* ===== Affix Sidebar ===== */
	/* Ref: http://getbootstrap.com/javascript/#affix-examples */

    	
	$('#doc-nav > ul').affix({
        offset: {
            top: ($('#header').outerHeight(true) + $('#doc-header').outerHeight(true)) + 45,
            bottom: ($('#footer').outerHeight(true) + $('#promo-block').outerHeight(true)) + 75
        }
    });
    
    /* Hack related to: https://github.com/twbs/bootstrap/issues/10236 */
    $(window).on('load resize', function() {
        $(window).trigger('scroll'); 
    });

    $('#doc-nav  > ul').addClass('nav');

    /* Activate scrollspy menu */
    $('body').scrollspy({target: '#doc-nav', offset: 100});
    
    /* Smooth scrolling */
	$('a.internal, a.headerlink').on('click', function(e){
        //store hash
        if(this.pathname === window.location.pathname) {
            e.preventDefault();
            var target = this.hash || 0;
            $('body').scrollTo(target, 800, {offset: 0, 'axis': 'y'});
        }
		
	});
	
    
    /* ======= jQuery Responsive equal heights plugin ======= */
    /* Ref: https://github.com/liabru/jquery-match-height */
    
     $('#cards-wrapper .item-inner').matchHeight();
     $('#showcase .card').matchHeight();
     
    /* Bootstrap lightbox */
    /* Ref: http://ashleydw.github.io/lightbox/ */

    $('img')
        .not(".figure img")
        .not(".ekko-lightbox-container img")
        .on("click", function(e){
       e.preventDefault();
        $(this).ekkoLightbox({
            remote:$(this).attr('src'),
            width:'100%'
        });
    });

    // $(document).delegate('img', 'click', function(e) {
    //     e.preventDefault();
    //
    // });

    $("a.reference.external").on("click",function(e){
         window.open($(this).attr('href'),'_blank');
         e.preventDefault();
         return false;
     });


});