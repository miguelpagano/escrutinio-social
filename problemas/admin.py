from django.contrib import admin
from django.shortcuts import reverse
from django.utils.html import format_html
from .models import Problema, ReporteDeProblema
from django import forms
from django_admin_row_actions import AdminRowActionsMixin

def marcar_resuelto(modeladmin, request, queryset):
    queryset.update(estado=Problema.ESTADOS.resuelto)


marcar_resuelto.short_description = "Marcar como resueltos"

class ProblemaForm(forms.ModelForm):

    class Meta:
        model = Problema
        exclude = []

class ConsolidatedInline(admin.StackedInline):
    model = ReporteDeProblema
    extra = 0

class ProblemaAdmin(AdminRowActionsMixin, admin.ModelAdmin):

    def mesa_(o):
        return format_html(f'<a href="/admin/elecciones/mesa/?id={o.mesa.id}">{o.mesa}</a>')
    mesa_.allow_tags = True
    mesa_.short_description = "Nro de mesa"

    def attachment_(o):
        return format_html(f'<a href="/admin/adjuntos/attachment/?id={o.attachment.id}">{o.attachment}</a>')
    attachment_.allow_tags = True
    attachment_.short_description = "Attachment"

    def descripciones(o):
        reportes = "<br>".join(o.reportes.all())
        return reportes

    def get_row_actions(self, obj):
        row_actions = []
        row_actions.append({
            'label': 'Confirmar',
            'url': reverse('confirmar-problema', args=[obj.id]),
            'enabled': True
        })
        row_actions.append({
            'label': 'Descartar',
            'url': reverse('descartar-problema', args=[obj.id]),
            'enabled': True
        })

        row_actions += super().get_row_actions(obj)
        return row_actions

    list_display = ('id', mesa_, attachment_, 'estado', descripciones, 'resuelto_por')
    list_filter = ('estado',)
    search_fields = (
        'mesa__numero',
    )
    inlines = [ConsolidatedInline]
    ordering = ['id']

admin.site.register(Problema, ProblemaAdmin)