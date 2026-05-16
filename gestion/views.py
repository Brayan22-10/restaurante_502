from decimal import Decimal
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.core.validators import RegexValidator
from .models import Cliente, Empleado, Mesa, Plato, Orden, DetalleOrden, Factura

class EmpleadoForm(forms.ModelForm):
    telefono = forms.CharField(
        validators=[RegexValidator(regex=r'^\d+$', message="El número de teléfono solo debe contener números.")],
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Solo números'})
    )
    
    correo = forms.EmailField(
        required=False,
        error_messages={'invalid': 'Ingresa una dirección de correo electrónico válida.'},
        widget=forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'})
    )

    class Meta:
        model = Empleado
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo:
            existe = Empleado.objects.filter(correo=correo)
            if self.instance and self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                raise forms.ValidationError("Ya existe un empleado registrado con este correo electrónico.")
        return correo


class ClienteForm(forms.ModelForm):
    telefono = forms.CharField(
        validators=[RegexValidator(regex=r'^\d+$', message="El número de teléfono solo debe contener números.")],
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Solo números'})
    )
    
    correo = forms.EmailField(
        required=False,
        error_messages={'invalid': 'Ingresa una dirección de correo electrónico válida.'},
        widget=forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'})
    )

    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo:
            existe = Cliente.objects.filter(correo=correo)
            if self.instance and self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                raise forms.ValidationError("Ya existe un cliente registrado con este correo electrónico.")
        return correo


class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = '__all__'
        widgets = {
            'numero_mesa': forms.TextInput(attrs={'placeholder': 'Ej: 1, 2, 3'}),
            'capacidad': forms.NumberInput(attrs={'placeholder': 'Cantidad de personas', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})

    def clean_capacidad(self):
        capacidad = self.cleaned_data.get('capacidad')
        if capacidad is not None and capacidad <= 0:
            raise forms.ValidationError("La capacidad de la mesa debe ser un número mayor a cero.")
        return capacidad


class PlatoForm(forms.ModelForm):
    class Meta:
        model = Plato
        fields = '__all__'
        widgets = {
            'nombre_plato': forms.TextInput(attrs={'placeholder': 'Nombre del platillo'}),
            'precio': forms.NumberInput(attrs={'placeholder': 'Precio en $', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Breve descripción del plato', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio del plato debe ser un valor mayor a cero.")
        return precio


class OrdenForm(forms.ModelForm):
    class Meta:
        model = Orden
        fields = ['cliente', 'empleado', 'mesa']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})


class DetalleOrdenForm(forms.ModelForm):
    class Meta:
        model = DetalleOrden
        fields = ['plato', 'cantidad']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1', 'value': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['metodo_pago']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})

# Login

def vista_login(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect('inicio')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    else:
        form = AuthenticationForm()
    return render(request, 'gestion/login.html', {'form': form})


def vista_registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save() 
            messages.success(request, "Cuenta creada exitosamente. Ahora puedes iniciar sesión.")
            return redirect('login')
        else:
            messages.error(request, "Error en el registro. Verifica los datos.")
    else:
        form = UserCreationForm()
    return render(request, 'gestion/registro.html', {'form': form})


def vista_logout(request):
    logout(request)
    return redirect('login')


def inicio(request):
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_empleados': Empleado.objects.count(),
        'total_mesas': Mesa.objects.count(),
        'total_platos': Plato.objects.count(),
        'total_ordenes': Orden.objects.count(), 
        'total_facturas': Factura.objects.count(), 
    }
    return render(request, 'gestion/inicio.html', context)

# Empleados

def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'gestion/empleados.html', {'empleados': empleados})


def crear_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado agregado correctamente.")
            return redirect('lista_empleados')
    else:
        form = EmpleadoForm()
    return render(request, 'gestion/form_empleado.html', {'form': form, 'titulo': 'Agregar Empleado'})


def editar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id) 
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado actualizado correctamente.")
            return redirect('lista_empleados')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'gestion/form_empleado.html', {'form': form, 'titulo': 'Editar Empleado'})


def eliminar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)
    if request.method == 'POST':
        empleado.delete()
        messages.success(request, "Empleado eliminado.")
        return redirect('lista_empleados')
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': empleado, 
        'tipo': 'empleado',
        'url_cancelar': 'lista_empleados'
    })


#Clientes

def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'gestion/clientes.html', {'clientes': clientes})


def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente registrado exitosamente.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'gestion/form_cliente.html', {'form': form, 'titulo': 'Registrar Cliente'})


def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos del cliente actualizados.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'gestion/form_cliente.html', {'form': form, 'titulo': 'Editar Cliente'})


def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, "Cliente eliminado correctamente.")
        return redirect('lista_clientes')
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': cliente, 
        'tipo': 'cliente',
        'url_cancelar': 'lista_clientes'
    })

# Mesas

def lista_mesas(request):
    mesas = Mesa.objects.all().order_by('numero_mesa')
    return render(request, 'gestion/mesas.html', {'mesas': mesas})


def crear_mesa(request):
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mesa creada exitosamente.")
            return redirect('lista_mesas')
    else:
        form = MesaForm()
    return render(request, 'gestion/form_mesa.html', {'form': form, 'titulo': 'Agregar Mesa'})


def editar_mesa(request, id):
    mesa = get_object_or_404(Mesa, id=id)
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            messages.success(request, f"Mesa #{mesa.numero_mesa} actualizada.") 
            return redirect('lista_mesas')
    else:
        form = MesaForm(instance=mesa)
    return render(request, 'gestion/form_mesa.html', {'form': form, 'titulo': 'Editar Mesa'})


def eliminar_mesa(request, id):
    mesa = get_object_or_404(Mesa, id=id)
    if request.method == 'POST':
        num = mesa.numero_mesa
        mesa.delete()
        messages.success(request, f"Mesa #{num} eliminada.")
        return redirect('lista_mesas')
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': mesa, 
        'tipo': 'mesa', 
        'url_cancelar': 'lista_mesas'
    })

# Platos

def lista_platos(request):
    platos = Plato.objects.all().order_by('categoria', 'nombre_plato')
    return render(request, 'gestion/platos.html', {'platos': platos})


def crear_plato(request):
    if request.method == 'POST':
        form = PlatoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plato añadido al menú correctamente.")
            return redirect('lista_platos')
    else:
        form = PlatoForm()
    return render(request, 'gestion/form_plato.html', {'form': form, 'titulo': 'Nuevo Plato'})


def editar_plato(request, id):
    plato = get_object_or_404(Plato, id=id)
    if request.method == 'POST':
        form = PlatoForm(request.POST, instance=plato)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plato '{plato.nombre_plato}' actualizado.")
            return redirect('lista_platos')
    else:
        form = PlatoForm(instance=plato)
    return render(request, 'gestion/form_plato.html', {'form': form, 'titulo': 'Editar Plato'})


def eliminar_plato(request, id):
    plato = get_object_or_404(Plato, id=id)
    if request.method == 'POST':
        nombre = plato.nombre_plato
        plato.delete()
        messages.success(request, f"El plato '{nombre}' ha sido eliminado.")
        return redirect('lista_platos')
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': plato, 
        'tipo': 'plato', 
        'url_cancelar': 'lista_platos'
    })

# Ordenes

def lista_ordenes(request):
    ordenes = Orden.objects.all().order_by('-id')
    return render(request, 'gestion/ordenes.html', {'ordenes': ordenes})


def crear_orden(request):
    if request.method == 'POST':
        form = OrdenForm(request.POST)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.estado_orden = 'En Proceso'
            orden.save()
            return redirect('agregar_platos_orden', orden_id=orden.id)
    else:
        form = OrdenForm()
    return render(request, 'gestion/form_orden.html', {'form': form, 'titulo': 'Nueva Orden - Paso 1'})


def agregar_platos_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    
    if request.method == 'POST':
        form = DetalleOrdenForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.orden = orden
            detalle.servido = False 
            detalle.save() 
            
            if orden.estado_orden != 'En Proceso':
                orden.estado_orden = 'En Proceso'
                orden.save()
                
            return redirect('agregar_platos_orden', orden_id=orden.id)
    else:
        form = DetalleOrdenForm()
        
    detalles = orden.detalles.all()
    return render(request, 'gestion/agregar_platos.html', {
        'orden': orden, 
        'form': form, 
        'detalles': detalles
    })


def eliminar_plato_orden(request, detalle_id):
    detalle = get_object_or_404(DetalleOrden, id=detalle_id)
    orden_id = detalle.orden.id
    
    if detalle.orden.estado_orden == 'Facturada':
        messages.error(request, "No puedes remover platos de una comanda ya liquidada.")
        return redirect('lista_ordenes')
        
    detalle.delete()
    messages.success(request, "Plato removido con éxito de la comanda.")
    return redirect('agregar_platos_orden', orden_id=orden_id)


def confirmar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    if not orden.detalles.exists():
        messages.error(request, "La orden no contiene ningún platillo asignado.")
        return redirect('agregar_platos_orden', orden_id=orden.id)
        
    orden.estado_orden = 'Activa'
    orden.save()
    messages.success(request, f"Orden #{orden.id} confirmada y enviada a producción.")
    return redirect('lista_ordenes')


def editar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    if orden.estado_orden == 'Facturada':
        messages.error(request, "No se permite alterar la parametrización de una orden facturada.")
        return redirect('lista_ordenes')
        
    if request.method == 'POST':
        form = OrdenForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cabecera de Orden #{orden.id} reconfigurada.")
            return redirect('agregar_platos_orden', orden_id=orden.id)
    else:
        form = OrdenForm(instance=orden)
    return render(request, 'gestion/form_orden.html', {'form': form, 'titulo': f'Editar Orden #{orden.id}'})


def eliminar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    if orden.estado_orden == 'Facturada':
        messages.error(request, "Restricción de integridad: No se permite depurar órdenes facturadas.")
        return redirect('lista_ordenes')
        
    if request.method == 'POST':
        orden.delete()
        messages.success(request, "Orden anulada del sistema.")
        return redirect('lista_ordenes')
        
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': orden, 
        'tipo': 'orden', 
        'url_cancelar': 'lista_ordenes'
    })

def entregar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    orden.detalles.filter(servido=False).update(servido=True)
    orden.estado_orden = 'Activa' 
    orden.save()
    
    return redirect('lista_ordenes')

# Facturas

def lista_facturas(request):
    facturas = Factura.objects.all().order_by('-id')
    return render(request, 'gestion/facturas.html', {'facturas': facturas})


def crear_factura(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    
    if orden.estado_orden == 'Facturada':
        messages.error(request, "Esta comanda ya posee una factura vinculada.")
        return redirect('lista_ordenes')

    if request.method == 'POST':
        form = FacturaForm(request.POST)
        if form.is_valid():
            factura = form.save(commit=False)
            factura.orden = orden
            factura.subtotal = orden.subtotal
            factura.impuesto = orden.impuesto
            factura.total_factura = orden.total
            factura.save()
            orden.estado_orden = 'Facturada'
            orden.save()
            
            messages.success(request, f"Factura #{factura.id} procesada. Estado cerrado.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm()
        
    return render(request, 'gestion/facturar.html', {
        'form': form, 
        'orden': orden,
        'titulo': f'Facturar Orden #{orden.id}'
    })


def editar_factura(request, id):
    factura = get_object_or_404(Factura, id=id)
    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        if form.is_valid():
            form.save()
            messages.success(request, f"Método de pago de Factura #{factura.id} reajustado.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm(instance=factura)
    return render(request, 'gestion/form_factura.html', {'form': form, 'titulo': 'Editar Factura'})


def eliminar_factura(request, id):
    factura = get_object_or_404(Factura, id=id)
    if request.method == 'POST':
        orden = factura.orden
        orden.estado_orden = 'Activa'
        orden.save()
        
        factura.delete()
        messages.success(request, "Factura purgada. La orden asociada se ha reabierto.")
        return redirect('lista_facturas')
    
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': factura, 
        'tipo': 'factura',
        'url_cancelar': 'lista_facturas'
    })