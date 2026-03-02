(function(){
    const toggle = document.getElementById('theme-toggle');
    if(!toggle) return;
    const current = localStorage.getItem('theme') || 'light';
    if(current === 'dark') document.body.classList.add('dark-mode');

    toggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
    });
})();