from django.urls import reverse
from elecciones.tests.factories import (
    VotoMesaReportadoFactory,
    CategoriaFactory,
    MesaFactory,
    OpcionFactory,
    CircuitoFactory,
    CategoriaOpcionFactory,
    CargaFactory,
    IdentificacionFactory,
)
from elecciones.tests.test_resultados import fiscal_client, setup_groups # noqa
from elecciones.models import Mesa, VotoMesaReportado, Carga, MesaCategoria
from elecciones.tests.test_resultados import fiscal_client          # noqa
from http import HTTPStatus


def test_elegir_acta_sin_mesas(fiscal_client):
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    _assert_redireccion_sin_actas(response)


def test_elegir_acta_mesas_redirige(db, fiscal_client):

    assert Mesa.objects.count() == 0
    assert VotoMesaReportado.objects.count() == 0
    c = CircuitoFactory()
    e1 = CategoriaFactory()
    e2 = CategoriaFactory()

    m1 = IdentificacionFactory(
        mesa__categorias=[e1],
        mesa__lugar_votacion__circuito=c,
        status='identificada',
        consolidada=True,
    ).mesa
    e2 = CategoriaFactory()
    m2 = IdentificacionFactory(
        mesa__categorias=[e1, e2],
        mesa__lugar_votacion__circuito=c,
        status='identificada',
        consolidada=True,
    ).mesa
    assert m1.orden_de_carga == 1
    assert m2.orden_de_carga == 2

    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m1.numero])

    # como m1 queda en periodo de "taken" (aunque no se haya ocupado aun)
    # se pasa a la siguiente mesa
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m2.numero])

    # se carga esa categoria
    VotoMesaReportadoFactory(
        carga__mesa_categoria__mesa=m2,
        carga__mesa_categoria__categoria=e1,
        opcion=e1.opciones.first(),
        votos=1
    )

    # FIX ME . El periodo de taken deberia ser *por categoria*.
    # en este escenario donde esta lockeado la mesa para la categoria 1, pero no se está
    # cargando la mesa 2, un dataentry queda idle
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 200   # no hay actas

    m2.taken = None
    m2.save()
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse(
        'mesa-cargar-resultados', args=[e2.id, m2.numero]
    )

def test_elegir_acta_mesas_con_id_de_mesa_desde_ub(fiscal_client):
    circuito = CircuitoFactory()
    categoria_1 = CategoriaFactory()
    categoria_2 = CategoriaFactory()

    mesa1 = IdentificacionFactory(
        mesa__categorias=[categoria_1, categoria_2],
        mesa__lugar_votacion__circuito=circuito,
        status='identificada',
        consolidada=True,
    ).mesa

    response = fiscal_client.get(reverse('procesar-acta-mesa', kwargs={'mesa_id': mesa1.id}))

    assert response.status_code == HTTPStatus.FOUND
    #como es por id el order by del método que devuelve siguiente categoria, debería ser categoria_1
    assert response.url == reverse('mesa-cargar-resultados', args=[categoria_1.id, mesa1.numero])

def test_elegir_acta_mesas_con_id_inexistente_de_mesa_desde_ub(fiscal_client):
    mesa_id_inexistente = 673162312
    response = fiscal_client.get(reverse('procesar-acta-mesa', kwargs={'mesa_id': mesa_id_inexistente}))

    _assert_redireccion_sin_actas(response)

def _assert_redireccion_sin_actas(response):
    assert response.status_code == HTTPStatus.OK
    assert 'No hay actas para cargar por el momento' in response.content.decode('utf8')

def test_elegir_acta_prioriza_por_tamaño_circuito(db, fiscal_client):
    e1 = CategoriaFactory()

    m1 = IdentificacionFactory(
        mesa__categorias=[e1],
        status='identificada',
        consolidada=True,
    ).mesa
    m2 = IdentificacionFactory(
        mesa__categorias=[e1],
        status='identificada',
        consolidada=True,
    ).mesa
    m3 = IdentificacionFactory(
        mesa__categorias=[e1],
        status='identificada',
        consolidada=True,
    ).mesa
    # creo otras mesas asociadas a los circuitos
    c1 = m1.lugar_votacion.circuito
    c2 = m2.lugar_votacion.circuito
    c3 = m3.lugar_votacion.circuito

    MesaFactory.create_batch(
        3,
        categorias=[e1],
        lugar_votacion__circuito=c1
    )
    MesaFactory.create_batch(
        10,
        categorias=[e1],
        lugar_votacion__circuito=c2
    )
    MesaFactory.create_batch(
        5,
        categorias=[e1],
        lugar_votacion__circuito=c3
    )
    assert c1.electores == 400
    assert c2.electores == 1100
    assert c3.electores == 600
    assert m1.orden_de_carga == m2.orden_de_carga == m3.orden_de_carga == 1
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m2.numero])
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m3.numero])
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m1.numero])


def test_carga_mesa_redirige_a_siguiente(db, fiscal_client):
    o = OpcionFactory(es_contable=True)
    o2 = OpcionFactory(es_contable=False)
    e1 = CategoriaFactory(opciones=[o, o2])
    e2 = CategoriaFactory(opciones=[o])
    m1 = IdentificacionFactory(
        mesa__categorias=[e1, e2],
        status='identificada',
        consolidada=True,
    ).mesa
    response = fiscal_client.get(reverse('elegir-acta-a-cargar'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m1.numero])

    # formset para categoria e1 arranca en blanco
    url = response.url
    response = fiscal_client.get(response.url)
    formset = response.context['formset']
    assert len(formset) == 2
    assert formset[0].initial == {'opcion': o}
    assert formset[1].initial == {'opcion': o2}

    # response = fiscal_client.get(url)
    response = fiscal_client.post(url, {
        'form-0-opcion': str(o.id),
        'form-0-votos': str(m1.electores // 2),
        'form-1-opcion': str(o2.id),
        'form-1-votos': str(m1.electores // 2),
        'form-TOTAL_FORMS': '2',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '2',
        'form-MAX_NUM_FORMS': '1000',
    })
    carga = Carga.objects.get()  # sólo hay una carga
    assert carga.status == 'total'
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e2.id, m1.numero])

    # el form de la nueva categoria e2 está en blanco
    url = response.url
    response = fiscal_client.get(response.url)
    formset = response.context['formset']
    assert len(formset) == 1
    assert formset[0].initial == {'opcion': o}

    # si completamos y es valido, no quedan
    # categorias por cargar y pide otra acta
    response = fiscal_client.post(url, {
        'form-0-opcion': str(o.id),
        'form-0-votos': str(m1.electores),
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '1',
        'form-MAX_NUM_FORMS': '1000',
    })
    assert response.status_code == 302
    assert response.url == reverse('elegir-acta-a-cargar')


def test_formset_en_carga_parcial(db, fiscal_client):
    c = CategoriaFactory()
    o = CategoriaOpcionFactory(categoria=c, prioritaria=True).opcion
    o2 = CategoriaOpcionFactory(categoria=c, prioritaria=False).opcion
    m = MesaFactory(categorias=[c])
    parciales = reverse(
        'mesa-cargar-resultados-parciales', args=[c.id, m.numero]
    )
    response = fiscal_client.get(parciales)
    assert len(response.context['formset']) == 1
    response.context['formset'][0].fields['opcion'].choices == [
        (o.id, str(o))
    ]


def test_formset_en_carga_total(db, fiscal_client):
    c = CategoriaFactory(id=100, opciones=[])
    o = CategoriaOpcionFactory(categoria=c, opcion__orden=3, prioritaria=True).opcion
    o2 = CategoriaOpcionFactory(categoria=c, opcion__orden=1, prioritaria=False).opcion
    m = MesaFactory(categorias=[c])
    totales = reverse(
        'mesa-cargar-resultados', args=[c.id, m.numero]
    )
    response = fiscal_client.get(totales)
    assert len(response.context['formset']) == 2
    response.context['formset'][0].fields['opcion'].choices == [
        (o2.id, str(o2)),
        (o.id, str(o))
    ]


def test_detalle_mesa_categoria(db, fiscal_client):
    opcs = OpcionFactory.create_batch(3, es_contable=True)
    e1 = CategoriaFactory(opciones=opcs)
    e2 = CategoriaFactory(opciones=opcs)
    mesa = MesaFactory(categorias=[e1, e2])
    c = CargaFactory(
            mesa_categoria__mesa=mesa,
            mesa_categoria__categoria=e1,
    )
    mc = c.mesa_categoria
    votos1 = VotoMesaReportadoFactory(
        opcion=opcs[0],
        votos=1,
        carga=c,
    )
    votos2 = VotoMesaReportadoFactory(
        opcion=opcs[1],
        votos=2,
        carga=c,
    )
    votos3 = VotoMesaReportadoFactory(
        opcion=opcs[2],
        votos=1,
        carga=c,
    )

    # a otra carga
    VotoMesaReportadoFactory(
        opcion=opcs[2],
        votos=1
    )
    c.actualizar_firma()
    assert mc.carga_testigo == c
    url = reverse('detalle-mesa-categoria', args=[e1.id, mesa.numero])
    response = fiscal_client.get(url)

    assert list(response.context['reportados']) == [votos1, votos2, votos3]
