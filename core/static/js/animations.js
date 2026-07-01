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

// --- Mot du Ministre animations: photo entry + typing loop ---
document.addEventListener('DOMContentLoaded', function () {
    try {
        const photo = document.getElementById('min-photo');
        const typedTextEl = document.getElementById('typed-text');
        const typedCursor = document.getElementById('typed-cursor');

        if (photo && window.gsap) {
            gsap.from(photo, {
                duration: 1.05,
                x: -90,
                opacity: 0,
                scale: 0.98,
                ease: 'power3.out',
                scrollTrigger: {
                    trigger: photo,
                    start: 'top 90%',
                    // play when entering from either direction, and reverse when leaving
                    toggleActions: 'play reverse play reverse'
                },
                // remove transform after animation so the CSS slow-zoom animation can run
                onComplete: () => gsap.set(photo, { clearProps: 'transform' })
            });
        }

        if (typedTextEl && window.gsap) {
            // preserve original HTML (paragraph breaks) and type per paragraph
            const originalHTML = typedTextEl.innerHTML.trim();
            let typingRunning = false;

            async function typeParagraph(text) {
                for (let ch of Array.from(text)) {
                    typedTextEl.innerHTML += ch.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    await new Promise(r => setTimeout(r, 60)); // 60ms per char (slower)
                }
            }

            async function typeLoop() {
                typingRunning = true;
                typedTextEl.innerHTML = '';
                // split paragraphs by double <br> (allow optional slash)
                const parts = originalHTML.split(/<br\s*\/?>(?:\s*)<br\s*\/?/i);
                for (let i = 0; i < parts.length; i++) {
                    // decode any HTML entities in part by using a temporary element
                        const tmp = document.createElement('div');
                        tmp.innerHTML = parts[i];
                        let plain = tmp.textContent || tmp.innerText || '';
                        // remove leading markdown-style blockquote markers '>' at start of lines
                        plain = plain.replace(/^\s*>+\s?/gm, '');
                    await typeParagraph(plain);
                    if (i < parts.length - 1) {
                        typedTextEl.innerHTML += '<br><br>';
                    }
                }
                typingRunning = false;
                // wait 20s then restart typing if not already running
                setTimeout(() => { if (!typingRunning) typeLoop(); }, 20000);
            }

            const startTyping = () => { if (!typingRunning) setTimeout(typeLoop, 600); };

            ScrollTrigger.create({
                trigger: typedTextEl,
                start: 'top 90%',
                onEnter: () => startTyping(),
                onEnterBack: () => startTyping(),
                once: false
            });
        }
    } catch (e) {
        console.error('Mot du Ministre animations failed', e);
    }
});