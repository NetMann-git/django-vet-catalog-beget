(function () {
    'use strict';

    var form = document.getElementById('home-callback-form');
    if (!form || !window.fetch) {
        return;
    }

    var statusBox = document.getElementById('home-callback-status');
    var submitButton = form.querySelector('button[type="submit"]');

    function clearErrors() {
        form.querySelectorAll('.home-callback__field').forEach(function (field) {
            field.classList.remove('is-invalid');
            field.querySelector('[aria-invalid="true"]')?.removeAttribute('aria-invalid');
            var error = field.querySelector('.home-callback__error');
            if (error) {
                error.textContent = '';
            }
        });
    }

    function showStatus(message, type) {
        if (!statusBox) {
            return;
        }
        statusBox.textContent = message || '';
        statusBox.className = 'home-callback__status is-visible ' + (type === 'success' ? 'is-success' : 'is-error');
    }

    function showFieldErrors(errors) {
        Object.keys(errors || {}).forEach(function (name) {
            var field = form.querySelector('[data-field="' + name + '"]');
            if (!field) {
                return;
            }
            field.classList.add('is-invalid');
            field.querySelector('input, textarea')?.setAttribute('aria-invalid', 'true');
            var error = field.querySelector('.home-callback__error');
            if (error && errors[name] && errors[name].length) {
                error.textContent = errors[name][0];
            }
        });
        form.querySelector('[aria-invalid="true"]')?.focus();
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        clearErrors();

        var phone = form.querySelector('[name="phone"]');
        if (!phone || !phone.value.trim()) {
            showFieldErrors({ phone: ['Введите номер телефона.'] });
            showStatus('Проверьте заполнение формы.', 'error');
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
        }

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function (result) {
                if (!result.ok || !result.data.success) {
                    showFieldErrors(result.data.errors || {});
                    showStatus(result.data.message || 'Не удалось отправить заявку.', 'error');
                    return;
                }

                form.reset();
                showStatus(result.data.message, 'success');
            })
            .catch(function () {
                showStatus('Не удалось отправить заявку. Попробуйте ещё раз.', 'error');
            })
            .finally(function () {
                if (submitButton) {
                    submitButton.disabled = false;
                }
            });
    });
})();
