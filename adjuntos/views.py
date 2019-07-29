import base64

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, FormView

from adjuntos.consolidacion import consolidar_identificaciones
from adjuntos.csv_import import CSVImporter
from problemas.models import Problema
from problemas.forms import IdentificacionDeProblemaForm

from .forms import AgregarAttachmentsForm, AgregarAttachmentsCSV, IdentificacionForm
from .models import Attachment, Identificacion


MENSAJE_NINGUN_ATTACHMENT_VALIDO = 'Ningún archivo es válido'
MENSAJE_SOLO_UN_ACTA = 'Se debe subir una sola acta'


class IdentificacionCreateView(CreateView):
    """
    Esta es la vista que permite clasificar un acta,
    asociándola a una mesa o reportando un problema

    Ver :class:`adjuntos.forms.IdentificacionForm`
    """
    form_class = IdentificacionForm
    template_name = "adjuntos/asignar-mesa.html"
    model = Identificacion

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        return response

    def get_success_url(self):
        return reverse('siguiente-accion')

    def identificacion(self):
        return self.object

    def get_operation_result(self):
        if self.identificacion().mesa is None:
            return {'decision': 'problema', 'contenido': self.identificacion().status.replace(" ", "_")}
        else:
            return {'decision': 'mesa', 'contenido': self.identificacion().mesa.numero}

    @cached_property
    def attachment(self):
        # solo el fiscal asignado al attachment puede identificar la carga
        attachment = get_object_or_404(Attachment, id=self.kwargs['attachment_id'])
        fiscal = self.request.user.fiscal
        if attachment.taken_by != fiscal:
            # TO DO: deberiamos loguear esta situación (o captura via sentry)
            # y quizas sumar puntos al score anti-trolling?
            raise PermissionDenied('no te toca identificar esta acta')
        return attachment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attachment'] = self.attachment
        context['recibir_problema'] = 'asignar-problema'
        context['dato_id'] = self.attachment.id
        context['form_problema'] = IdentificacionDeProblemaForm()
        return context

    def form_valid(self, form):
        identificacion = form.save(commit=False)
        identificacion.status = Attachment.STATUS.identificada
        identificacion.fiscal = self.request.user.fiscal
        identificacion.attachment = self.attachment
        identificacion.save()
        messages.info(
            self.request,
            f'Identificada mesa Nº {identificacion.mesa} - circuito {identificacion.mesa.circuito}',
        )
        return super().form_valid(form)


class IdentificacionCreateViewDesdeUnidadBasica(IdentificacionCreateView):
    template_name = "adjuntos/asignar-mesa-ub.html"

    def get_success_url(self):
        identificacion = self.object
        mesa_id = identificacion.mesa.id
        return reverse('procesar-acta-mesa', kwargs={'mesa_id': mesa_id})

    def form_valid(self, form):
        identificacion = form.save(commit=False)
        identificacion.source = Identificacion.SOURCES.csv
        identificacion.fiscal = self.request.user.fiscal
        super().form_valid(form)
        # Como viene desde una UB, consolidamos el attachment y ya le pasamos la mesa
        consolidar_identificaciones(identificacion.attachment)
        return redirect(self.get_success_url())


class ReporteDeProblemaCreateView(CreateView):
    http_method_names = ['post']
    form_class = IdentificacionDeProblemaForm
    template_name = "problemas/problema.html"

    @cached_property
    def attachment(self):
        return get_object_or_404(Attachment, id=self.kwargs['attachment_id'])

    def form_invalid(self, form):
        messages.info(
            self.request,
            f'No se registró el reporte. Corroborá haber elegido una opción.',
            extra_tags="problema"
        )
        return redirect('siguiente-accion')

    def form_valid(self, form):
        fiscal = self.request.user.fiscal
        identificacion = form.save(commit=False)
        identificacion.attachment = self.attachment
        identificacion.fiscal = fiscal
        identificacion.status = Identificacion.STATUS.problema
        # Lo falso grabo para quedarme con la data de sus campos.
        reporte_de_problema = form.save(commit=False)
        tipo_de_problema = reporte_de_problema.tipo_de_problema
        descripcion = reporte_de_problema.descripcion

        # Creo la identificación.
        identificacion = Identificacion.objects.create(
            status=Identificacion.STATUS.problema, fiscal=fiscal, mesa=None, attachment=self.attachment
        )

        # Creo el problema asociado.
        Problema.reportar_problema(fiscal, descripcion, tipo_de_problema, identificacion=identificacion)

        messages.info(
            self.request,
            f'Gracias por el reporte. Ahora pasamos a la siguiente acta.',
            extra_tags="problema"
        )
        return redirect('siguiente-accion')


@staff_member_required
@csrf_exempt
def editar_foto(request, attachment_id):
    """
    esta vista se invoca desde el plugin DarkRoom con el contenido
    de la imagen editada codificada en base64.

    Se decodifica y se guarda en el campo ``foto_edited``
    """
    attachment = get_object_or_404(Attachment, id=attachment_id)
    if request.method == 'POST' and request.POST['data']:
        data = request.POST['data']
        file_format, imgstr = data.split(';base64,')
        extension = file_format.split('/')[-1]
        attachment.foto_edited = ContentFile(
            base64.b64decode(imgstr), name=f'edited_{attachment_id}.{extension}'
        )
        attachment.save(update_fields=['foto_edited'])
        return JsonResponse({'message': 'Imagen guardada'})
    return JsonResponse({'message': 'No se pudo guardar la imagen'})


class AgregarAdjuntos(FormView):
    """
    Permite subir una o más imágenes, generando instancias de ``Attachment``
    Si una imagen ya existe en el sistema, se exluye con un mensaje de error
    via `messages` framework.
    """

    def __init__(self, types=('image/jpeg', 'image/png'), **kwargs):
        super().__init__(**kwargs)
        self.types = types

    form_class = AgregarAttachmentsForm
    template_name = 'adjuntos/agregar-adjuntos.html'
    url_to_post = 'agregar-adjuntos'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_to_post'] = reverse(self.url_to_post)
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            contador_fotos = 0
            for file in files:
                instance = self.procesar_adjunto(file)
                if instance is not None:
                    contador_fotos = contador_fotos + 1
            if contador_fotos:
                self.mostrar_mensaje_archivos_cargados(contador_fotos)
            return redirect(reverse(self.url_to_post))

        return self.form_invalid(form)

    def procesar_adjunto(self, adjunto):
        if adjunto.content_type not in self.types:
            self.mostrar_mensaje_tipo_archivo_invalido(adjunto.name)
            return None
        return self.cargar_informacion_adjunto(adjunto)

    def cargar_informacion_adjunto(self, adjunto):
        try:
            instance = Attachment(mimetype=adjunto.content_type)
            instance.foto.save(adjunto.name, adjunto, save=False)
            instance.save()
            return instance
        except IntegrityError:
            messages.warning(self.request, f'{adjunto.name} ya existe en el sistema')
        return None

    def mostrar_mensaje_archivos_cargados(self, contador):
        messages.success(self.request, f'Subiste {contador} imágenes de actas. Gracias!')

    def mostrar_mensaje_tipo_archivo_invalido(self, nombre_archivo):
        messages.warning(self.request, f'{nombre_archivo} ignorado. No es una imagen')


class AgregarAdjuntosDesdeUnidadBasica(AgregarAdjuntos):
    """
    Permite subir una imagen, genera la instancia de Attachment y debería redirigir al flujo de
    asignación de mesa -> carga de datos pp -> carga de datos secundarios , etc

    Si una imagen ya existe en el sistema, se exluye con un mensaje de error
    via `messages` framework.
    """

    form_class = AgregarAttachmentsForm
    url_to_post = 'agregar-adjuntos-ub'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')

        # No debería poder cargarse por UI más de una imagen, pero por las dudas lo chequeamos.
        if len(files) > 1:
            form.add_error('file_field', MENSAJE_SOLO_UN_ACTA)

        if form.is_valid():
            file = files[0]
            instance = self.procesar_adjunto(file)
            if instance is not None:
                messages.success(self.request, 'Subiste el acta correctamente.')
                return redirect(reverse('asignar-mesa-ub', kwargs={"attachment_id": instance.id}))

            form.add_error('file_field', MENSAJE_NINGUN_ATTACHMENT_VALIDO)
        return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'es_multiple': False})
        return kwargs


class AgregarAdjuntosCSV(AgregarAdjuntos):
    """
    Permite subir un archivo CSV, valida que posea todas las columnas necesarias y que los datos sean
    Válidos. Si las validaciones resultan OK, crear la información correspondiente en la base de datos:
    Cargas totales, parciales e instancias de votos.

    """
    form_class = AgregarAttachmentsCSV
    template_name = 'adjuntos/agregar-adjuntos-csv.html'
    url_to_post = 'agregar-adjuntos-csv'

    def __init__(self):
        super().__init__(types='text/csv')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.fiscal.esta_en_grupo('unidades basicas'):
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden()

    def cargar_informacion_adjunto(self, adjunto):
        # Valida la info del archivo.
        try:
            CSVImporter(adjunto, self.request.user).procesar()
            return 'success'
        except Exception as e:
            messages.error(self.request, f'{adjunto.name} ignorado. {str(e)}')
        return None

    def mostrar_mensaje_tipo_archivo_invalido(self, f):
        messages.warning(self.request, f'{f.name} ignorado. No es un archivo CSV')

    def mostrar_mensaje_archivos_cargados(self, c):
        messages.success(self.request, f'Subiste {c} archivos CSV. Gracias!')
