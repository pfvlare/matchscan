// Partículas de fundo
particlesJS.load('particles-js', '/static/js/particles.json');

// Tema escuro/claro
document.getElementById('toggle-theme').addEventListener('click', () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    html.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
});
