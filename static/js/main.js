(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();
    
    // Initiate the wowjs
    new WOW().init();

    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 45) {
            $('.navbar').addClass('sticky-top shadow-sm');
        } else {
            $('.navbar').removeClass('sticky-top shadow-sm');
        }
    });
    
    // Dropdown on mouse hover
    const $dropdown = $(".dropdown");
    const $dropdownToggle = $(".dropdown-toggle");
    const $dropdownMenu = $(".dropdown-menu");
    const showClass = "show";
    
    $(window).on("load resize", function() {
        if (this.matchMedia("(min-width: 992px)").matches) {
            $dropdown.hover(
            function() {
                const $this = $(this);
                $this.addClass(showClass);
                $this.find($dropdownToggle).attr("aria-expanded", "true");
                $this.find($dropdownMenu).addClass(showClass);
            },
            function() {
                const $this = $(this);
                $this.removeClass(showClass);
                $this.find($dropdownToggle).attr("aria-expanded", "false");
                $this.find($dropdownMenu).removeClass(showClass);
            }
            );
        } else {
            $dropdown.off("mouseenter mouseleave");
        }
    });
    
    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });

    // Testimonials carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        center: true,
        margin: 24,
        dots: true,
        loop: true,
        nav : false,
        responsive: {
            0:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            }
        }
    });

    // START: Tempus Dominus Datepicker Initialization (NEW CODE FOR BOOKING FORMS)
    $(function () {
        // Initialize the main package booking date picker
        $('#date3').datetimepicker({
            format: 'YYYY-MM-DD', // Set the desired date format
            // Other useful options:
            minDate: moment().endOf('day'), // Prevents selecting past dates
            icons: {
                time: "fa fa-clock",
                date: "fa fa-calendar",
                up: "fa fa-arrow-up",
                down: "fa fa-arrow-down"
            }
        });

        // Initialize custom booking date pickers (if you use this form)
        $('#date_start').datetimepicker({
            format: 'YYYY-MM-DD',
            minDate: moment().endOf('day'), // Prevents selecting past dates
            icons: {
                time: "fa fa-clock", date: "fa fa-calendar",
                up: "fa fa-arrow-up", down: "fa fa-arrow-down"
            }
        });

        $('#date_end').datetimepicker({
            format: 'YYYY-MM-DD',
            useCurrent: false, // Important: allows end date to be before start date initially, adjusted by onchange
            minDate: moment().endOf('day'), // Prevents selecting past dates
            icons: {
                time: "fa fa-clock", date: "fa fa-calendar",
                up: "fa fa-arrow-up", down: "fa fa-arrow-down"
            }
        });

        // Link start and end dates for custom booking (optional but good UX)
        // Ensure that when start date changes, end date can't be before it, and vice versa.
        $("#date_start").on("change.datetimepicker", function (e) {
            $('#date_end').datetimepicker('minDate', e.date);
        });
        $("#date_end").on("change.datetimepicker", function (e) {
            $('#date_start').datetimepicker('maxDate', e.date);
        });
    });
    // END: Tempus Dominus Datepicker Initialization
    
})(jQuery);