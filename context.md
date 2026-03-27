# Contexto del Proyecto: Agente WhatsApp para Generación de Pedidos

## Perfil del desarrollador

- Desarrollador independiente con más de 20 años de experiencia
- Lenguajes previos: VB6, ACUCobol, .NET, Python (Tkinter/PySide)
- Últimos 5 años: desarrollo web
- Stack actual: Python + Django + Bootstrap + JS + MySQL
- Tiene clientes propios y sitios en producción (incluyendo uno con gestión de ventas y stock)
- Hosting actual: PythonAnywhere

---

## El Proyecto

### Objetivo
Construir un agente SaaS que:
- Reciba mensajes de WhatsApp de compradores
- Interprete pedidos automáticamente usando IA
- Los convierta en pedidos estructurados
- Pida confirmación antes de guardar
- Sirva a múltiples negocios (clientes del desarrollador) desde una sola instalación

### Caso de uso principal
```
Comprador envía: "Hola, necesito 2 cocas grandes y 1 paquete de fideos"

Sistema responde:
"Te preparo:
- 2x Coca Cola 2.25L
- 1x Fideos Matarazzo 500g
¿Confirmo el pedido?"
```

---

## Arquitectura General

### Stack
- **Backend:** Django (Python)
- **DB:** MySQL
- **Hosting:** PythonAnywhere (plan pago ~$5-12/mes) — suficiente para MVP
- **WhatsApp API:** Meta Cloud API o Twilio (sandbox para desarrollo)
- **IA para parsing:** Claude Haiku 4.5 (recomendado) o GPT-4o mini

### Flujo completo
```
Meta POST /webhook/
    │
    ├─ Extraer phone_number_id
    ├─ Identificar Negocio por phone_number_id
    ├─ Extraer mensaje del comprador
    ├─ Verificar si hay ConversacionActiva (pendiente de confirmar)
    ├─ IA parsea el mensaje → JSON de items
    ├─ Buscar productos filtrando por negocio (alias + fuzzy matching)
    ├─ Armar pedido preliminar
    └─ Responder por WhatsApp usando token del negocio
```

---

## Multitenancy (cómo se gestiona cada cliente)

### Concepto
Un solo Django, una sola DB. Cada registro sabe a qué negocio pertenece mediante FK.
El routing entre negocios se hace automáticamente por el `phone_number_id` que Meta incluye en cada webhook.

### Modelos Django

```python
class Negocio(models.Model):
    nombre = models.CharField(max_length=200)
    whatsapp_phone_id = models.CharField(max_length=100, unique=True)  # clave del routing
    whatsapp_token = models.CharField(max_length=500)
    activo = models.BooleanField(default=True)

class Producto(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(...)
    stock = models.IntegerField()

class Alias(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)  # "coca", "coca grande", "coca 2.25"

class Pedido(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    cliente_telefono = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

class ConversacionActiva(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    cliente_telefono = models.CharField(max_length=50)
    pedido_preliminar = models.JSONField()  # JSON antes de confirmar
    fecha = models.DateTimeField(auto_now=True)
```

### Webhook base

```python
@csrf_exempt
def webhook(request):
    data = json.loads(request.body)
    phone_number_id = data['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']
    negocio = Negocio.objects.get(whatsapp_phone_id=phone_number_id)
    productos = Producto.objects.filter(negocio=negocio)
    # ... resto del flujo
```

---

## Búsqueda de Productos

### 3 niveles
1. **Alias** (obligatorio): cada producto tiene nombres alternativos
2. **icontains**: búsqueda parcial básica de Django
3. **Fuzzy matching** con `rapidfuzz`: tolera errores de escritura y variaciones

### Salida esperada de la IA
```json
[
  {"producto": "coca grande", "cantidad": 2},
  {"producto": "fideos", "cantidad": 1}
]
```

---

## Costos Operativos

### API de WhatsApp (Meta)
- Desde julio 2025 cobra por mensaje, no por conversación
- Si el comprador inicia la conversación → mensajes dentro de la ventana de 24hs son **gratuitos**
- Solo se paga si el negocio inicia la conversación fuera de esa ventana
- Costo aproximado para pedidos: **~$15/mes** para 50 pedidos/día

### API de IA (por modelo)

| Modelo | Costo/pedido | Costo mensual (50 pedidos/día) |
|---|---|---|
| GPT-4o mini | ~$0.000065 | ~$0.10 |
| Claude Haiku 4.5 | ~$0.00035 | ~$0.53 |
| Claude Sonnet 4.6 | ~$0.00105 | ~$1.58 |
| GPT-4o | ~$0.00095 | ~$1.43 |

**Recomendación:** Claude Haiku 4.5 — mejor calidad de parsing en español rioplatense, costo marginal.

### Resumen costo operativo total (por instalación)

| Componente | Costo mensual | ¿Quién paga? |
|---|---|---|
| PythonAnywhere | ~$5-12 | El desarrollador |
| API de IA (Claude) | ~$0.50-$5 según volumen | El desarrollador |
| API WhatsApp (Meta) | ~$0-15 | El cliente (negocio) |
| Número WhatsApp | Variable | El cliente (negocio) |

**Costo total del desarrollador: menos de $20/mes para varios clientes.**

---

## Modelo de Negocio

- **Setup inicial**: cobro único por configuración
- **Mensualidad**: $100-200 USD/mes por cliente es perfectamente justificable
- **Margen**: muy alto dado el bajo costo operativo

### Contratación de APIs
| API | Modelo de contratación |
|---|---|
| WhatsApp (Meta) | Un número por negocio, cada cliente gestiona el suyo o vos como ISV |
| IA (Claude/GPT) | Una sola API key para todos los clientes |
| Hosting | Un solo PythonAnywhere para todos |

### Límites de Meta
- Sin verificación: hasta 2 números
- Con verificación de negocio: hasta 20 números
- Más de 20: solicitar excepción por ticket

---

## PythonAnywhere: ¿sirve para este proyecto?

**Sí, perfectamente para el MVP.** El webhook es un endpoint Django estándar que recibe POST de Meta. No necesita always-on tasks ni configuración especial. Requisitos:
- Plan pago (Hacker ~$5/mes) para poder conectarse a APIs externas
- HTTPS incluido (Meta lo requiere)
- Timeout de 5 minutos (irrelevante, el proceso dura 2-3 segundos)

---

## Estrategia de Desarrollo

### Recomendación clave
**Empezar con simulador web, sin WhatsApp real.** Un endpoint que recibe texto manual y ejecuta todo el flujo. Cuando funcione bien, integrar WhatsApp.

### Estimación de tiempos

**Semana 1**
- Modelos Django: 1 día
- Endpoint webhook con simulador: 1 día
- Integración API de IA para parsing: 1-2 días
- Búsqueda con alias + fuzzy matching: 1-2 días

**Semana 2**
- Lógica de estado de conversación: 1-2 días
- Integración WhatsApp real (sandbox): 1-2 días
- Pruebas end-to-end: 1 día
- Ajustes y casos borde: 1-2 días

**Total real:** 3-4 semanas trabajando en paralelo con otros clientes.

### Atención
El registro en Meta Business puede tardar 2-5 días hábiles. Iniciarlo el primer día.

---

## MVP: qué incluye y qué no

### Incluye
- Recibir mensajes de WhatsApp
- Interpretar pedidos con IA
- Buscar productos (alias + fuzzy)
- Confirmar pedido con el comprador
- Guardar pedido en DB
- Soporte multicliente (multitenancy)

### No incluye (futuro)
- Portal de autoregistro para clientes
- Turnos y reservas
- CRM
- Automatización sin confirmación
- IA compleja o entrenamiento propio

---

## Próximos pasos acordados
1. Armar estructura de modelos Django
2. Implementar endpoint webhook con simulador
3. Integrar parsing con Claude Haiku
4. Implementar búsqueda de productos
5. Lógica de confirmación y estado de conversación
6. Integración WhatsApp real