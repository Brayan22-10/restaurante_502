from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User  

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'Cliente'

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    CARGOS = [
        ('Mesero', 'Mesero'),
        ('Mesera', 'Mesera'),
        ('Cajero', 'Cajero'),
        ('Cajera', 'Cajera'),
        ('Administrador', 'Administrador'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empleado', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50, choices=CARGOS)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'Empleado'

    def __str__(self):
        return f"{self.nombre} - {self.cargo}"


class Mesa(models.Model):
    ESTADOS_MESA = [
        ('Disponible', 'Disponible'),
        ('Ocupada', 'Ocupada'),
        ('Reservada', 'Reservada'),
    ]

    numero_mesa = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField() 
    estado_mesa = models.CharField(max_length=20, choices=ESTADOS_MESA, default='Disponible')

    class Meta:
        db_table = 'Mesa'

    def __str__(self):
        return f"Mesa {self.numero_mesa}"


class Plato(models.Model):
    nombre_plato = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    disponible = models.BooleanField(default=True)

    class Meta:
        db_table = 'Plato'

    def __str__(self):
        return self.nombre_plato


class Orden(models.Model):
    ESTADOS_ORDEN = [
        ('En Proceso', 'En Proceso'), 
        ('Pendiente', 'Pendiente'),        
        ('Activa', 'Activa'),           
        ('En preparación', 'En preparación'),
        ('Entregada', 'Entregada'),       
        ('En Caja', 'En Caja'),          
        ('Facturada', 'Facturada'),        
        ('Cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estado_orden = models.CharField(max_length=20, choices=ESTADOS_ORDEN, default='En Proceso')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'OrdenRestaurante'

    def calcular_totales(self):
        detalles = self.detalles.all()
        subtotal_calculado = sum((d.subtotal for d in detalles), Decimal('0.00'))
        self.subtotal = subtotal_calculado
        self.impuesto = self.subtotal * Decimal('0.08')
        self.total = self.subtotal + self.impuesto
        self.save()

    def __str__(self):
        return f"Orden {self.id} - {self.cliente.nombre} (Mesa {self.mesa.numero_mesa})"

    def comanda_texto(self):
        detalles = self.detalles.all()
        if not detalles:
            return "Sin platos"
        
        lineas = []
        for d in detalles:
            estado = "(Entregado)" if d.servido else "(En preparación)"
            lineas.append(f"{d.cantidad}x {d.plato.nombre_plato} {estado}")
        return ", ".join(lineas)

    @property
    def boton_eliminar(self):
        if self.estado_orden in ['En Caja', 'Facturada', 'Cancelada']:
            return False
        return not self.detalles.filter(servido=True).exists()

    @property
    def boton_entregar(self):
        if self.estado_orden != 'Activa':
            return False
        return self.detalles.filter(servido=False).exists()

    @property
    def boton_facturar(self):
        if self.estado_orden in ['En Caja', 'Facturada', 'Cancelada']:
            return False
        if not self.detalles.exists():
            return False
        return not self.detalles.filter(servido=False).exists()


class DetalleOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles')
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField() 
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    servido = models.BooleanField(default=False)

    class Meta:
        db_table = 'Detail_Order'

    def save(self, *args, **kwargs):
        self.precio_unitario = self.plato.precio
        self.subtotal = Decimal(self.cantidad) * self.precio_unitario
        super().save(*args, **kwargs)
        self.orden.calcular_totales()

    def delete(self, *args, **kwargs):
        orden = self.orden
        super().delete(*args, **kwargs)
        orden.calcular_totales()

    def __str__(self):
        return f"Detalle {self.id} - Orden {self.orden.id}"
    
    @property
    def estado_texto(self):
        if self.servido:
            return "(Entregado)"
        return "(En preparación)"


class Factura(models.Model):
    METODOS_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('Transferencia', 'Transferencia'),
        ('Nequi', 'Nequi'),
        ('Daviplata', 'Daviplata'),
    ]

    orden = models.OneToOneField(Orden, on_delete=models.CASCADE)
    fecha_factura = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2)
    total_factura = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=30, choices=METODOS_PAGO)

    class Meta:
        db_table = 'Factura'

    def __str__(self):
        return f"Factura {self.id} - Orden {self.orden.id}"