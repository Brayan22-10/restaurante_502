from django import forms
from django.contrib.auth.models import User, Group
from .models import Empleado

class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input-style'}), label="Contraseña")
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(usuario__isnull=True), 
        required=True, 
        label="Asociar a Empleado",
        empty_label="Seleccione un empleado disponible"
    )
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(), 
        required=True, 
        label="Asignar Rol"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Nombre de Usuario (Login)',
            'email': 'Correo Electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input-style'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  
        if commit:
            user.save()
            empleado = self.cleaned_data['empleado']
            empleado.usuario = user
            empleado.save()
            rol = self.cleaned_data['rol']
            user.groups.add(rol)
        return user