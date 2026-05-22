from decimal import Decimal
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.contrib import messages
from django.core.validators import RegexValidator
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group  
from .models import Cliente, Empleado, Mesa, Plato, Orden, DetalleOrden, Factura
from .forms import RegistroUsuarioForm

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
        fields = ['nombre', 'telefono', 'correo']

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

class AsignarRolForm(forms.Form):
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.all(),
        empty_label="Selecciona un empleado",
        widget=forms.Select()
    )
    
    ROL_CHOICES = [
        ('mesero', 'Mesero'),
        ('cajero', 'Cajero'),
        ('admin', 'Administrador'),
    ]
    rol = forms.ChoiceField(choices=ROL_CHOICES, widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-style'})

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
        request = kwargs.pop('request', None)
        super(OrdenForm, self).__init__(*args, **kwargs)
        
        if 'empleado' in self.fields:
            self.fields['empleado'].queryset = Empleado.objects.filter(
                Q(cargo='Mesero') | Q(cargo='Mesera')
            )
        
        if 'mesa' in self.fields:
            self.fields['mesa'].queryset = Mesa.objects.filter(
                estado_mesa='Disponible'
            ).order_by('numero_mesa')
            
        if request and hasattr(request, 'user'):
            empleado_perfil = getattr(request.user, 'empleado', None)
            if empleado_perfil and 'empleado' in self.fields:
                self.fields['empleado'].initial = empleado_perfil

class DetalleOrdenForm(forms.ModelForm):
    class Meta:
        model = DetalleOrden
        fields = ['plato', 'cantidad']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1', 'value': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'plato' in self.fields:
            self.fields['plato'].queryset = Plato.objects.filter(disponible=True).order_by('categoria', 'nombre_plato')
            
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

def verificar_si_mesero(user):
    return user.groups.filter(name='Mesero').exists() or (hasattr(user, 'empleado') and user.empleado.cargo in ['Mesero', 'Mesera'])

def es_administrador(user):
    return user.is_authenticated and user.groups.filter(name='Administrador').exists()


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


def vista_logout(request):
    logout(request)
    return redirect('login')


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

@login_required
def inicio(request):
    total_facturas_pendientes = Factura.objects.exclude(orden__estado_orden='Facturada').count()
    
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_empleados': Empleado.objects.count(),
        'total_mesas': Mesa.objects.count(),
        'total_platos': Plato.objects.count(),
        'total_ordenes': Orden.objects.count(), 
        'total_facturas': Factura.objects.count(), 
        'facturas_pendientes': total_facturas_pendientes,
    }
    return render(request, 'gestion/inicio.html', context)

@login_required
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'gestion/empleados.html', {'empleados': empleados})

@login_required
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

@login_required
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

@login_required
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

@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'gestion/clientes.html', {'clientes': clientes})

@login_required
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

@login_required
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

@login_required
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

@login_required
def lista_mesas(request):
    mesas = Mesa.objects.all().order_by('numero_mesa')
    return render(request, 'gestion/mesas.html', {'mesas': mesas})

@login_required
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

@login_required
def editar_mesa(request, id):
    mesa = get_object_or_404(Mesa, id=id)
    es_mesero = verificar_si_mesero(request.user)

    if request.method == 'POST':
        if es_mesero:
            datos_seguros = request.POST.copy()
            datos_seguros['numero_mesa'] = mesa.numero_mesa
            datos_seguros['capacidad'] = mesa.capacidad
            form = MesaForm(datos_seguros, instance=mesa)
        else:
            form = MesaForm(request.POST, instance=mesa)

        if form.is_valid():
            form.save()
            messages.success(request, f"Mesa #{mesa.numero_mesa} actualizada correctamente.") 
            return redirect('lista_mesas')
    else:
        form = MesaForm(instance=mesa)
    return render(request, 'gestion/form_mesa.html', {'form': form, 'titulo': 'Editar Mesa'})

@login_required
def eliminar_mesa(request, id):
    mesa = get_object_or_404(Mesa, id=id)
    if verificar_si_mesero(request.user):
        messages.error(request, "No posees los privilegios necesarios para eliminar esta mesa.")
        return redirect('lista_mesas')

    if request.method == 'POST':
        num = mesa.numero_mesa
        mesa.delete()
        messages.success(request, f"Mesa #{num} eliminada con éxito.")
        return redirect('lista_mesas')
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': mesa, 
        'tipo': 'mesa', 
        'url_cancelar': 'lista_mesas'
    })

@login_required
def lista_platos(request):
    platos = Plato.objects.all().order_by('categoria', 'nombre_plato')
    return render(request, 'gestion/platos.html', {'platos': platos})

@login_required
def crear_plato(request):
    if verificar_si_mesero(request.user):
        messages.error(request, "Acceso denegado: Los meseros no pueden agregar platos al menú.")
        return redirect('lista_platos') 
        
    if request.method == 'POST':
        form = PlatoForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            messages.success(request, "Plato agregado exitosamente.")
            return redirect('lista_platos')
    else:
        form = PlatoForm()
    return render(request, 'gestion/form_plato.html', {'form': form, 'titulo': 'Agregar Plato'})

@login_required
def editar_plato(request, id):
    plato = get_object_or_404(Plato, id=id)
    if verificar_si_mesero(request.user):
        messages.error(request, "Acceso denegado: Los meseros no tienen permisos para modificar el menú.")
        return redirect('lista_platos')

    if request.method == 'POST':
        form = PlatoForm(request.POST, request.FILES, instance=plato)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plato '{plato.nombre_plato}' actualizado correctamente.")
            return redirect('lista_platos')
    else:
        form = PlatoForm(instance=plato)
    return render(request, 'gestion/form_plato.html', {'form': form, 'titulo': 'Editar Plato'})

@login_required
def eliminar_plato(request, id):
    plato = get_object_or_404(Plato, id=id)
    if verificar_si_mesero(request.user):
        messages.error(request, "Acceso denegado: Los meseros no pueden eliminar platos del menú.")
        return redirect('lista_platos')

    if request.method == 'POST':
        nombre_plato = plato.nombre_plato
        plato.delete()
        messages.success(request, f"Plato '{nombre_plato}' eliminado correctamente.")
        return redirect('lista_platos')
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': plato, 
        'tipo': 'plato', 
        'url_cancelar': 'lista_platos'
    })

@login_required
def lista_ordenes(request):
    todas_las_ordenes = Orden.objects.all().order_by('-id')
    
    ordenes_activas = []
    ordenes_historial = []
    
    for orden in todas_las_ordenes:
        estado = orden.estado_orden.strip() if orden.estado_orden else ""
        
        if estado in ['Facturada', 'Cancelada']:
            ordenes_historial.append(orden)
        else:
            if estado == 'En Caja':
                orden.puede_modificar = False
                orden.puede_enviar_cocina = False
                orden.puede_servir = False
                orden.puede_facturar = False
            else:
                orden.puede_modificar = True 
                orden.puede_enviar_cocina = (estado == 'Pendiente')
                orden.puede_servir = (estado == 'Activa')
                orden.puede_facturar = (estado == 'Entregada')
            
            ordenes_activas.append(orden)
            
    context = {
        'ordenes_activas': ordenes_activas,
        'ordenes_historial': ordenes_historial,
    }
    return render(request, 'gestion/ordenes.html', context)

@login_required
def crear_orden(request):
    empleado_perfil = getattr(request.user, 'empleado', None)
    cargo = empleado_perfil.cargo if empleado_perfil else None

    if not request.user.is_superuser and cargo in ['Cajero', 'Cajera']:
        messages.error(request, "No tienes permisos para crear o modificar órdenes.")
        return redirect('inicio')

    if request.method == 'POST':
        form = OrdenForm(request.POST, request=request)
        
        if form.is_valid():
            orden = form.save(commit=False)
            
            if orden.mesa:
                mesa_ya_ocupada = Orden.objects.filter(
                    mesa=orden.mesa, 
                    estado_orden__in=['En Proceso', 'Activa', 'Entregada']
                ).exists()
                
                if mesa_ya_ocupada:
                    messages.error(request, f"¡Error! La Mesa N° {orden.mesa.numero_mesa} acaba de ser ocupada por otra comanda.")
                    return render(request, 'gestion/form_orden.html', {'form': form, 'titulo': 'Nueva Orden - Paso 1'})
            
            orden.estado_orden = 'En Proceso'
            orden.save()
            
            if orden.mesa:
                orden.mesa.estado_mesa = 'Ocupada'
                orden.mesa.save()
                
            return redirect('agregar_platos_orden', orden_id=orden.id)
    else:
        form = OrdenForm(request=request)
            
    return render(request, 'gestion/form_orden.html', {'form': form, 'titulo': 'Nueva Orden - Paso 1'})

def agregar_platos_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    
    if orden.estado_orden in ['Facturada', 'Cerrada', 'En Caja']:
        messages.error(request, "Esta orden ya se encuentra en proceso de pago y no puede ser modificada.")
        return redirect('lista_ordenes')
        
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'guardar_y_salir':
            detalles = orden.detalles.all()
            tiene_platos_pendientes = detalles.filter(servido=False).exists()
            
            if not tiene_platos_pendientes and detalles.exists():
                orden.estado_orden = 'Entregada'
            elif tiene_platos_pendientes:
                orden.estado_orden = 'Pendiente'
                
            orden.save()
            messages.success(request, f"Pedido de la Orden #{orden.id} actualizado.")
            return redirect('lista_ordenes')
            
        form = DetalleOrdenForm(request.POST)
        if form.is_valid():
            nuevo_detalle = form.save(commit=False)
            nuevo_detalle.orden = orden
            nuevo_detalle.precio_unitario = nuevo_detalle.plato.precio
            nuevo_detalle.subtotal = nuevo_detalle.precio_unitario * nuevo_detalle.cantidad
            nuevo_detalle.save()
            orden.estado_orden = 'Pendiente'
            detalles_actuales = orden.detalles.all()
            orden.calcular_totales()
            
            messages.success(request, f"Añadido: {nuevo_detalle.plato.nombre_plato}")
            return redirect('agregar_platos_orden', orden_id=orden.id)
            
    else:
        form = DetalleOrdenForm()
        
    detalles = orden.detalles.all()
    context = {
        'orden': orden,
        'form': form,
        'detalles': detalles,
    }
    return render(request, 'gestion/agregar_platos.html', context)

@login_required
def eliminar_plato_orden(request, detalle_id):
    detalle = get_object_or_404(DetalleOrden, id=detalle_id)
    orden = detalle.orden  
    orden_id = orden.id
    
    if orden.estado_orden == 'Facturada':
        messages.error(request, "No puedes remover platos de una comanda ya liquidada.")
        return redirect('lista_ordenes')
        
    if detalle.servido:
        messages.error(request, f"¡No es posible eliminar el platillo '{detalle.plato.nombre_plato}' porque ya fue entregado a la mesa!")
        return redirect('agregar_platos_orden', orden_id=orden_id)
        
    detalle.delete()
    
    if not orden.detalles.exists():
        orden.estado_orden = 'En Proceso'  
        orden.save()
        messages.warning(request, "El plato fue removido. La comanda está vacía, debes agregar un plato o cancelar la orden.")
    else:
        messages.success(request, "Plato removido con éxito de la comanda.")
        
    return redirect('agregar_platos_orden', orden_id=orden_id)

@login_required
def confirmar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    
    if not orden.detalles.exists():
        messages.error(request, "La orden no contiene ningún platillo asignado.")
        return redirect('agregar_platos_orden', orden_id=orden.id)
        
    tiene_platos_pendientes = orden.detalles.filter(servido=False).exists()
    
    if not tiene_platos_pendientes:
        orden.estado_orden = 'Entregada'
        orden.save()
        messages.info(request, f"Orden #{orden.id} actualizada. No se detectaron nuevos pedidos para cocina.")
    else:
        orden.estado_orden = 'Activa'
        orden.save()
        messages.success(request, f"Orden #{orden.id} confirmada y enviada a producción.")
        
    return redirect('lista_ordenes')

@login_required
def editar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    if orden.estado_orden == 'Facturada':
        messages.error(request, "No se permite alterar la parametrización de una orden cerrada.")
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

@login_required
def eliminar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    
    if orden.estado_orden == 'Facturada':
        messages.error(request, "No se pueden eliminar órdenes cerradas y facturadas.")
        return redirect('lista_ordenes')
        
    tiene_platos_entregados = orden.detalles.filter(servido=True).exists()
    
    if tiene_platos_entregados:
        messages.error(request, f"No se puede anular la Orden #{orden.id} porque ya se han entregado platos a la mesa.")
        return redirect('lista_ordenes')
        
    if request.method == 'POST':
        if orden.mesa:
            orden.mesa.estado_mesa = 'Disponible' 
            orden.mesa.save()
            
        orden.delete()
        messages.success(request, f"Orden #{id} anulada correctamente (no se habían entregado consumos).")
        return redirect('lista_ordenes')
        
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': orden, 
        'tipo': 'orden', 
        'url_cancelar': 'lista_ordenes'
    })

def cancelar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    
    if not orden.detalles.exists():
        if orden.mesa:
            mesa = orden.mesa
            mesa.estado_mesa = 'Disponible' 
            mesa.save() 
        
        orden.delete()
        messages.success(request, f"La orden #{orden_id} fue cancelada y la mesa ha sido liberada.")
    else:
        messages.warning(request, "No se puede eliminar la orden porque ya contiene platillos asignados.")
        
    return redirect('inicio')

@login_required
def entregar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    orden.detalles.filter(servido=False).update(servido=True)
    orden.estado_orden = 'Entregada'
    orden.save()
    messages.success(request, f"Todos los platos pendientes de la Orden #{orden.id} han sido servidos.")
    return redirect('lista_ordenes')

@login_required
def cargar_factura(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    
    if orden.estado_orden in ['En Caja', 'Facturada']:
        messages.warning(request, f"La orden #{orden.id} ya se encuentra en caja o ya fue pagada.")
        return redirect('lista_ordenes')
    
    orden.estado_orden = 'En Caja'
    orden.save()
    
    factura, created = Factura.objects.get_or_create(
        orden=orden,
        defaults={
            'subtotal': getattr(orden, 'subtotal', orden.total),
            'impuesto': getattr(orden, 'impuesto', 0),
            'total_factura': orden.total,
            'metodo_pago': 'Efectivo'  
        }
    )
    
    messages.success(request, f"Orden #{orden.id} enviada a Caja. El cajero ya puede proceder con el cobro.")
    return redirect('lista_ordenes')

@login_required
def lista_facturas(request):
    facturas = Factura.objects.all().select_related('orden', 'orden__mesa').order_by('-id')
    return render(request, 'gestion/facturas.html', {'facturas': facturas})

@login_required
def crear_factura(request, orden_id): 
    orden = get_object_or_404(Orden, id=orden_id)
    
    if verificar_si_mesero(request.user):
        messages.error(request, "No tienes permisos de Cajero para procesar pagos o facturar.")
        return redirect('lista_ordenes')

    if orden.estado_orden == 'Facturada':
        messages.error(request, "Esta comanda ya fue pagada y archivada.")
        return redirect('lista_ordenes')

    factura_existente = Factura.objects.filter(orden=orden).first()

    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura_existente)
        if form.is_valid():
            factura = form.save(commit=False)
            factura.orden = orden
            factura.subtotal = getattr(orden, 'subtotal', orden.total)
            factura.impuesto = getattr(orden, 'impuesto', 0)
            factura.total_factura = orden.total
            factura.save()
            orden.estado_orden = 'Facturada'
            orden.save()
            
            if orden.mesa:
                orden.mesa.estado_mesa = 'Disponible' 
                orden.mesa.save()
            
            messages.success(request, f"Factura #{factura.id} procesada y cobrada con éxito.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm(instance=factura_existente)
        
    return render(request, 'gestion/facturar.html', {
        'form': form, 
        'orden': orden,
        'titulo': f'Facturar Orden #{orden.id}'
    })

@login_required
def finalizar_pago_factura(request, factura_id):
    if verificar_si_mesero(request.user):
        messages.error(request, "Acceso denegado: Solo los cajeros pueden registrar la recepción de dinero.")
        return redirect('lista_facturas')

    factura = get_object_or_404(Factura, id=factura_id) 
    
    if request.method == 'POST':
        metodo = request.POST.get('metodo_pago', 'Efectivo')
        factura.metodo_pago = metodo
        factura.save()
        
        orden = factura.orden
        orden.estado_orden = 'Facturada' 
        orden.save()
        
        if orden.mesa:
            orden.mesa.estado_mesa = 'Disponible' 
            orden.mesa.save()
        
        messages.success(request, f"Pago de la Factura #{factura.id} recibido con éxito vía {metodo}. Mesa {orden.mesa.numero_mesa} liberada.")
        return redirect('lista_facturas')
        
    return redirect('lista_facturas')

@login_required
def editar_factura(request, id):
    if verificar_si_mesero(request.user):
        messages.error(request, "Acceso denegado.")
        return redirect('lista_facturas')

    factura = get_object_or_404(Factura, id=id)
    if factura.orden.estado_orden == 'Facturada':
        messages.error(request, "No se puede editar una factura que ya ha sido cerrada definitivamente.")
        return redirect('lista_facturas')

    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        if form.is_valid():
            form.save()
            messages.success(request, f"Método de pago de Factura #{factura.id} reajustado.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm(instance=factura)
    return render(request, 'gestion/form_factura.html', {'form': form, 'titulo': 'Editar Factura'})

@login_required
def eliminar_factura(request, id):
    if verificar_si_mesero(request.user):
        messages.error(request, "Acceso denegado.")
        return redirect('lista_facturas')

    factura = get_object_or_404(Factura, id=id)
    
    if factura.orden.estado_orden == 'Facturada':
        messages.error(request, "Restricción de caja: No se permite eliminar una factura pagada.")
        return redirect('lista_facturas')

    if request.method == 'POST':
        orden = factura.orden
        
        detalles = orden.detalles.all()
        tiene_platos_pendientes = detalles.filter(servido=False).exists()
        
        if tiene_platos_pendientes:
            orden.estado_orden = 'Pendiente' 
        else:
            orden.estado_orden = 'Entregada' 
            
        orden.save()
        
        factura.delete()
        messages.success(request, "Factura rechazada de caja. La orden asociada ha sido reactivada en el panel del mesero.")
        return redirect('lista_facturas')
    
    return render(request, 'gestion/confirmar_eliminar.html', {
        'objeto': factura, 
        'tipo': 'factura',
        'url_cancelar': 'lista_facturas'
    })

@login_required
def asignar_rol_view(request):
    if request.method == 'POST':
        form = AsignarRolForm(request.POST)
        if form.is_valid():
            empleado = form.cleaned_data['empleado']
            rol = form.cleaned_data['rol']
            
            if rol == 'mesero':
                username_general = "Mesero1"
                password_general = "Brayan2006@"
            elif rol == 'cajero':
                username_general = "Cajero1"
                password_general = "Brayan2006@"
            else:
                username_general = "admin"
                password_general = "Admin12345"

            user, created = User.objects.get_or_create(username=username_general) # type: ignore
            
            user.set_password(password_general)
            user.save()
            
            grupo, _ = Group.objects.get_or_create(name=rol.capitalize()) # type: ignore
            user.groups.add(grupo) # type: ignore

            if hasattr(empleado, 'cargo'):
                empleado.cargo = rol.capitalize()
            empleado.save()
            return render(request, 'gestion/credenciales_mostradas.html', {
                'empleado': empleado,
                'username': username_general,
                'password': password_general,
                'rol': rol.capitalize()
            })
    else:
        form = AsignarRolForm()
        
    return render(request, 'gestion/asignar_rol.html', {'form': form})

@login_required
@user_passes_test(es_administrador, login_url='inicio', redirect_field_name=None)
def crear_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Usuario creado, rol asignado y empleado vinculado con éxito!")
            return redirect('inicio') 
    else:
        form = RegistroUsuarioForm()
    return render(request, 'gestion/crear_usuario.html', {'form': form})