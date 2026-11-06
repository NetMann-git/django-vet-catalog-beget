"""Контекст главной клиники без унаследованных мебельных данных, шаг 4."""
from apps.appointments.forms import CallbackRequestForm


class VetHomeContextBuilder:
    @staticmethod
    def build(request):
        form = CallbackRequestForm()
        form.fields['phone'].widget.attrs.update({'placeholder': 'Ваш номер телефона'})
        form.fields['comment'].widget.attrs.update({
            'placeholder': 'Кто ваш питомец и когда вам удобно ответить на звонок',
            'rows': 4,
        })
        return {'callback_form': form}
