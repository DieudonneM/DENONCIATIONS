document.addEventListener('DOMContentLoaded', function () {
    if (!window.gsap || !window.ScrollTrigger) {
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    const autoRevealSelectors = [
        'section',
        '.card',
        '.management-card',
        '.detail-section',
        '.success-box',
        '.contact-card',
        '.step',
        '.admin-metric',
        '.incident-list-row',
        '.stat-card',
        '.feature-card'
    ];

    autoRevealSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(element => {
            if (!element.classList.contains('reveal')) {
                element.classList.add('reveal');
            }
        });
    });

    const revealedParents = new Set();

    document.querySelectorAll('.reveal').forEach(element => {
        const parent = element.parentElement;

        if (parent && !revealedParents.has(parent)) {
            const siblings = [...parent.children].filter(child => child.classList.contains('reveal'));

            if (siblings.length > 1) {
                revealedParents.add(parent);
                gsap.set(siblings, { opacity: 0, y: 28, willChange: 'transform, opacity' });

                gsap.to(siblings, {
                    opacity: 1,
                    y: 0,
                    duration: 0.8,
                    stagger: 0.12,
                    ease: 'power3.out',
                    clearProps: 'willChange',
                    scrollTrigger: {
                        trigger: parent,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse'
                    }
                });

                return;
            }
        }

        gsap.set(element, { opacity: 0, y: 28, willChange: 'transform, opacity' });
        gsap.to(element, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: 'power3.out',
            clearProps: 'willChange',
            scrollTrigger: {
                trigger: element,
                start: 'top 88%',
                toggleActions: 'play none none reverse'
            }
        });
    });
});