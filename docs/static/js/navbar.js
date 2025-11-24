/**
 * Mobile Navigation Menu Handler
 */
(function() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (!hamburger || !navLinks) return;

    // Toggle menu on hamburger click
    hamburger.addEventListener('click', function() {
        const isExpanded = this.getAttribute('aria-expanded') === 'true';

        // Toggle active state
        this.classList.toggle('active');
        navLinks.classList.toggle('active');

        // Update ARIA attributes
        this.setAttribute('aria-expanded', !isExpanded);
    });

    // Close menu when clicking nav links
    const links = navLinks.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            hamburger.setAttribute('aria-expanded', 'false');
        });
    });

    // Close menu on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navLinks.classList.contains('active')) {
            hamburger.classList.remove('active');
            navLinks.classList.remove('active');
            hamburger.setAttribute('aria-expanded', 'false');
            hamburger.focus();
        }
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
            if (navLinks.classList.contains('active')) {
                hamburger.classList.remove('active');
                navLinks.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
            }
        }
    });
})();
