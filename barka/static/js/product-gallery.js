document.addEventListener("DOMContentLoaded", () => {
    const galleries = document.querySelectorAll("[data-product-gallery]");

    for (const gallery of galleries) {
        const mainImage = gallery.querySelector("[data-gallery-main]");
        const thumbnails = Array.from(gallery.querySelectorAll("[data-gallery-thumb]"));
        const dots = Array.from(gallery.querySelectorAll("[data-gallery-dot]"));
        const nextButton = gallery.querySelector("[data-gallery-next]");
        const prevButton = gallery.querySelector("[data-gallery-prev]");
        const autoplay = gallery.dataset.autoplay === "true";
        const interval = Number.parseInt(gallery.dataset.interval || "3800", 10);
        let activeIndex = Math.max(0, thumbnails.findIndex((thumb) => thumb.classList.contains("is-primary")));
        let timerId = null;

        if (!mainImage || thumbnails.length < 2) {
            continue;
        }

        const setActive = (index) => {
            activeIndex = (index + thumbnails.length) % thumbnails.length;
            const source = thumbnails[activeIndex];
            gallery.classList.add("is-transitioning");
            mainImage.src = source.dataset.imageUrl;
            mainImage.alt = source.dataset.imageAlt;

            thumbnails.forEach((thumb, thumbIndex) => {
                thumb.classList.toggle("is-primary", thumbIndex === activeIndex);
                thumb.setAttribute("aria-pressed", thumbIndex === activeIndex ? "true" : "false");
            });

            dots.forEach((dot, dotIndex) => {
                dot.classList.toggle("is-active", dotIndex === activeIndex);
                dot.setAttribute("aria-pressed", dotIndex === activeIndex ? "true" : "false");
            });

            gallery.classList.remove("restart-progress");
            void gallery.offsetWidth;
            gallery.classList.add("restart-progress");

            window.setTimeout(() => {
                gallery.classList.remove("is-transitioning");
            }, 260);
        };

        const stopAutoplay = () => {
            gallery.classList.add("is-paused");
            if (timerId) {
                window.clearInterval(timerId);
                timerId = null;
            }
        };

        const startAutoplay = () => {
            if (!autoplay || thumbnails.length < 2) {
                return;
            }
            stopAutoplay();
            gallery.classList.remove("is-paused");
            timerId = window.setInterval(() => {
                setActive(activeIndex + 1);
            }, interval);
        };

        thumbnails.forEach((thumb, index) => {
            thumb.addEventListener("click", () => {
                setActive(index);
                startAutoplay();
            });
        });

        dots.forEach((dot, index) => {
            dot.addEventListener("click", () => {
                setActive(index);
                startAutoplay();
            });
        });

        nextButton?.addEventListener("click", () => {
            setActive(activeIndex + 1);
            startAutoplay();
        });

        prevButton?.addEventListener("click", () => {
            setActive(activeIndex - 1);
            startAutoplay();
        });

        gallery.addEventListener("mouseenter", stopAutoplay);
        gallery.addEventListener("mouseleave", startAutoplay);

        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                stopAutoplay();
                return;
            }
            startAutoplay();
        });

        setActive(activeIndex);
        startAutoplay();
    }
});