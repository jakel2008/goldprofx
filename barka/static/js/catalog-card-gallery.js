document.addEventListener("DOMContentLoaded", () => {
    const galleries = document.querySelectorAll("[data-card-gallery]");

    for (const gallery of galleries) {
        const images = Array.from(gallery.querySelectorAll("[data-card-image]"));
        const kicker = gallery.querySelector("[data-hero-kicker]");
        const title = gallery.querySelector("[data-hero-title]");
        const body = gallery.querySelector("[data-hero-body]");
        const price = gallery.querySelector("[data-hero-price]");
        const oldPrice = gallery.querySelector("[data-hero-old-price]");
        const cta = gallery.querySelector("[data-hero-cta]");
        const interval = Number.parseInt(gallery.dataset.interval || "3200", 10);
        let activeIndex = Math.max(0, images.findIndex((image) => image.classList.contains("is-active")));
        let timerId = null;

        if (images.length < 2) {
            continue;
        }

        const setActive = (index) => {
            activeIndex = (index + images.length) % images.length;
            const activeImage = images[activeIndex];
            images.forEach((image, imageIndex) => {
                image.classList.toggle("is-active", imageIndex === activeIndex);
            });

            if (kicker && title && body && price && oldPrice) {
                gallery.classList.add("hero-copy-swapping");
                kicker.textContent = activeImage.dataset.slideKicker || kicker.textContent;
                title.textContent = activeImage.dataset.slideTitle || title.textContent;
                body.textContent = activeImage.dataset.slideBody || body.textContent;
                price.textContent = activeImage.dataset.slidePrice || price.textContent;
                oldPrice.textContent = activeImage.dataset.slideOldPrice || oldPrice.textContent;
                if (cta) {
                    cta.textContent = activeImage.dataset.slideCtaLabel || cta.textContent;
                    cta.href = activeImage.dataset.slideCtaUrl || cta.href;
                }
                window.setTimeout(() => {
                    gallery.classList.remove("hero-copy-swapping");
                }, 240);
            }
        };

        const start = () => {
            if (timerId) {
                window.clearInterval(timerId);
            }
            timerId = window.setInterval(() => {
                setActive(activeIndex + 1);
            }, interval);
        };

        const stop = () => {
            if (!timerId) {
                return;
            }
            window.clearInterval(timerId);
            timerId = null;
        };

        gallery.addEventListener("mouseenter", stop);
        gallery.addEventListener("mouseleave", start);

        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                stop();
                return;
            }
            start();
        });

        setActive(activeIndex);
        start();
    }
});