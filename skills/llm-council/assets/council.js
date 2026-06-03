/* LLM Council debate behavior — scroll-reveal + confidence gauge.
   Inline this into <script> before </body> in a self-contained debate page.
   Respects prefers-reduced-motion: shows everything immediately, no animation. */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var reveal = document.querySelectorAll('.turn, .card, .evo');
  var gauges = document.querySelectorAll('.gauge');

  function fillGauge(g, value) {
    g.style.setProperty('--val', value);
    var v = g.querySelector('.val');
    if (v) v.textContent = value + '%';
  }

  if (reduce || !('IntersectionObserver' in window)) {
    reveal.forEach(function (el) { el.classList.add('in'); });
    gauges.forEach(function (g) { fillGauge(g, +g.dataset.confidence || 0); });
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  reveal.forEach(function (el) { io.observe(el); });

  gauges.forEach(function (g) {
    var target = +g.dataset.confidence || 0;
    var go = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return;
      go.unobserve(g);
      var start = null, dur = 1100;
      requestAnimationFrame(function step(ts) {
        if (start === null) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        fillGauge(g, Math.round(p * target));
        if (p < 1) requestAnimationFrame(step);
      });
    }, { threshold: 0.4 });
    go.observe(g);
  });
})();
