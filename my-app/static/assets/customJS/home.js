document.addEventListener('DOMContentLoaded', function() {

    // --- FUNCIONALIDAD DE MOSTRAR/OCULTAR CONTRASEÑA ---
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function () {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            const icon = this.querySelector('i');
            if (icon.classList.contains('bx-hide')) {
                icon.classList.remove('bx-hide');
                icon.classList.add('bx-show');
            } else {
                icon.classList.remove('bx-show');
                icon.classList.add('bx-hide');
            }
        });
    }

    // --- NOTIFICACIONES CON AUTO-DISMISS DESPUÉS DE 4 SEGUNDOS ---
    const toasts = document.querySelectorAll('.toast.custom-toast');

    toasts.forEach(function(toastElement) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const bsToast = new bootstrap.Toast(toastElement); 
            bsToast.show();

            setTimeout(function() {
                bsToast.hide();
            }, 4000); 
        } else {
            console.warn("Bootstrap JavaScript no está cargado o 'bootstrap.Toast' no está disponible.");
            setTimeout(function() {
                toastElement.style.display = 'none'; 
            }, 4000);
        }
    });

    // --- OCULTAR LOADER AL CARGAR PÁGINA ---
    const loader = document.getElementById('loader-out');
    if (loader) {
        window.addEventListener('load', () => {
            loader.style.display = 'none';
        });
    }

});
