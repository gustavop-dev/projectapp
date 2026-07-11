"""Unit tests for the width-accurate PDF layout engine (pdf_utils).

Enforces the mechanical invariant that makes horizontal overflow
impossible by construction: every line produced by ``_wrap_by_width``
measures within the requested width, using the exact same measurement
the draw path (``_draw_line_with_links``) applies.
"""

import io

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from content.services.pdf_utils import (
    CONTENT_W,
    ESMERALD_80,
    ESMERALD_LIGHT,
    MARGIN_B,
    _break_token_by_width,
    _check_y_with_redraw,
    _draw_feature_row,
    _draw_kpi_tile_row,
    _draw_line_with_links,
    _draw_priority_pill,
    _draw_section_header,
    _draw_table,
    _fit_text_ellipsis,
    _font,
    _measure_inline_width,
    _register_fonts,
    _section_header_height,
    _split_lines_for_page,
    _string_width_mixed,
    _wrap_by_width,
)

# Adversarial corpus: wide glyphs, digits, URLs, bold spans, emoji,
# no-space enum tokens — everything the old char-count wrap misjudged.
CORPUS = [
    'Texto sencillo con palabras normales y acentuadas: implementación, '
    'diseño, María Fernández.',
    'URL larga: https://www.dominio-larguisimo-de-verdad.com/ruta/muy/'
    'profunda/con/segmentos?query=1234567890',
    '$1.490.000 + IVA — 1234567890 0987654321 999.999.999 $12.345.678',
    'MMMMWWWW MMMMMMWWWWW ANCHÍSIMAS MAYÚSCULAS SOSTENIDAS EN LA LÍNEA',
    'Con **negrita que abarca varias palabras seguidas** y *cursiva* y '
    '`codigo_inline` mezclados.',
    'Emoji mezclado 🚀 con texto ✅ y más 📊 contenido al final.',
    'recibido/en_revision/diagnostico/reparado/entregado/facturado',
    'PalabraSinEspaciosNiSeparadoresQueEsMuyLargaDeVerdadYSigueYSigue',
    'Mix: **negrita con projectapp.co dentro** y texto después.',
]

WIDTHS = [120, 200, 350, CONTENT_W]


@pytest.fixture(autouse=True)
def _fonts():
    _register_fonts()


@pytest.fixture()
def pdf_canvas():
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setFont(_font('regular'), 10)
    return c


def test_wrap_by_width_every_line_fits():
    fn = _font('regular')
    for text in CORPUS:
        for width in WIDTHS:
            for size in (8, 10):
                lines = _wrap_by_width(text, fn, size, width)
                assert lines, text
                for line in lines:
                    measured = _measure_inline_width(line, fn, size)
                    assert measured <= width + 0.5, (
                        f'line {line!r} measures {measured:.1f} > {width} '
                        f'(size {size}) for text {text!r}'
                    )


def test_wrap_by_width_preserves_characters():
    # ** markers may be closed/reopened at line boundaries (intentional,
    # zero visible width) — compare marker-insensitively.
    fn = _font('regular')
    for text in CORPUS:
        for width in WIDTHS:
            lines = _wrap_by_width(text, fn, 9, width)
            joined = ''.join(lines).replace(' ', '').replace('**', '')
            assert joined == text.replace(' ', '').replace('**', '')


def test_wrap_by_width_keeps_bold_spans_balanced():
    fn = _font('regular')
    text = ('Inicio **una negrita larga que ocupa muchas palabras y '
            'obliga a repartir en varias líneas** y cierre normal.')
    for width in (140, 220, 300):
        for line in _wrap_by_width(text, fn, 9, width):
            assert line.count('**') % 2 == 0, line


def test_wrap_by_width_empty_and_tiny():
    fn = _font('regular')
    assert _wrap_by_width('', fn, 9, 200) == ['']
    assert _wrap_by_width(None, fn, 9, 200) == ['']
    # Zero/negative width degrades to a single line, never crashes.
    assert _wrap_by_width('hola mundo', fn, 9, 0) == ['hola mundo']


def test_measure_matches_draw_advance(pdf_canvas):
    c = pdf_canvas
    fn = _font('regular')
    for text in CORPUS:
        for line in _wrap_by_width(text, fn, 9, 300):
            end_x = _draw_line_with_links(c, 50, 400, line, fn, 9,
                                          ESMERALD_80)
            measured = _measure_inline_width(line, fn, 9)
            assert abs((end_x - 50) - measured) < 0.6, line


def test_break_token_by_width_fits_and_preserves():
    fn = _font('regular')
    token = 'estado/en_revision/diagnostico-completo/reparado.facturado'
    pieces = _break_token_by_width(token, fn, 8, 90)
    assert len(pieces) > 1
    assert ''.join(pieces) == token
    for piece in pieces[:-1]:
        assert _measure_inline_width(piece, fn, 8) <= 90 + 0.5


def test_fit_text_ellipsis():
    fn = _font('bold')
    short = _fit_text_ellipsis('OK', fn, 10, 200)
    assert short == 'OK'
    long_text = 'Inversión total del proyecto completo con hosting'
    fitted = _fit_text_ellipsis(long_text, fn, 12, 120)
    assert fitted.endswith('…')
    assert _string_width_mixed(fitted, fn, 12) <= 120
    assert long_text.startswith(fitted[:-1].rstrip())


def test_split_lines_for_page():
    lines = [f'l{i}' for i in range(10)]
    head, tail = _split_lines_for_page(lines, 12, 50)
    assert head == lines[:4] and tail == lines[4:]
    # Always progresses even with no room.
    head, tail = _split_lines_for_page(lines, 12, 3)
    assert head == lines[:1]
    assert _split_lines_for_page([], 12, 100) == ([], [])


def test_check_y_with_redraw(pdf_canvas):
    c = pdf_canvas
    calls = []

    def redraw(c, y):
        calls.append(y)
        return y - 20

    ps = {'num': 3, 'client': 'Cliente', 'total': None}
    # No break: redraw not invoked, y unchanged.
    y = _check_y_with_redraw(c, 700, ps, need=40, redraw=redraw)
    assert y == 700 and not calls and ps['num'] == 3
    # Break: page advances and redraw runs on the fresh page.
    y = _check_y_with_redraw(c, MARGIN_B + 10, ps, need=40, redraw=redraw)
    assert ps['num'] == 4
    assert len(calls) == 1
    assert y == calls[0] - 20


def test_section_header_height_matches_draw(pdf_canvas):
    c = pdf_canvas
    titles = [
        'Inversión',
        'Un título de sección larguísimo que necesita envolverse en '
        'varias líneas para caber en el ancho útil de la página A4',
    ]
    for title in titles:
        for idx in ('05', ''):
            y0 = 700.0
            y1 = _draw_section_header(c, y0, idx, title)
            assert abs((y0 - y1) - _section_header_height(title, idx)) < 0.01


def test_draw_table_col_widths_aligns_and_pagination(pdf_canvas):
    c = pdf_canvas
    ps = {'num': 3, 'client': 'Cliente', 'total': None}
    headers = ['#', 'Módulo', 'Descripción', 'Precio']
    rows = [
        [str(i + 1), f'Módulo {i + 1}',
         'Descripción bastante larga que envuelve en varias líneas '
         'dentro de su columna sin invadir a las vecinas. ' * 2,
         '$1.490.000']
        for i in range(30)
    ]
    y = _draw_table(c, 700, headers, rows, ps=ps,
                    col_widths=[0.07, 0.25, 0.48, 0.20],
                    aligns=['center', 'left', 'left', 'right'])
    assert ps['num'] > 3  # paginated
    assert MARGIN_B - 1 <= y < 700  # never returns below the margin


def test_draw_table_giant_row_chunks_across_pages(pdf_canvas):
    c = pdf_canvas
    ps = {'num': 3, 'client': 'Cliente', 'total': None}
    giant = 'palabra ' * 900  # far taller than one page in a 60% column
    y = _draw_table(c, 400, ['Req', 'Detalle'], [['R1', giant]], ps=ps,
                    col_widths=[0.3, 0.7])
    assert ps['num'] > 3
    assert y >= MARGIN_B - 1


def test_kpi_tile_row_and_feature_row_smoke(pdf_canvas):
    c = pdf_canvas
    ps = {'num': 3, 'client': 'Cliente', 'total': None}
    tiles = [
        {'value': '$1.490.000.000.000', 'label': 'Inversión total con '
         'una etiqueta exageradamente larga', 'sub': '+ IVA'},
        {'value': '8 semanas', 'label': 'Duración'},
        {'value': '$890.000', 'label': 'Hosting anual'},
    ]
    y = _draw_kpi_tile_row(c, 700, tiles, ps=ps, accent_first=True)
    assert y < 700
    y2 = _draw_feature_row(
        c, y, 'Título de feature row largo que debe envolver sin pisar '
        'la pastilla derecha', description='Descripción del paso con '
        'texto suficiente para envolver en un par de líneas de cuerpo.',
        ps=ps, index=1, pill_text='Etapa actual',
        children=['Primera subtarea', 'Segunda subtarea más larga'])
    assert y2 < y
    # Empty tiles are a no-op.
    assert _draw_kpi_tile_row(c, 500, [], ps=ps) == 500


def test_priority_pill_semantics(pdf_canvas):
    c = pdf_canvas
    right, _ = _draw_priority_pill(c, 100, 500, 'critical')
    assert right > 100
    right, _ = _draw_priority_pill(c, 100, 480, 'HIGH', lang='en')
    assert right > 100
    # Unknown value renders a neutral pill with the raw text.
    right, _ = _draw_priority_pill(c, 100, 460, 'urgentísimo')
    assert right > 100
    # Empty is a no-op.
    assert _draw_priority_pill(c, 100, 440, '') == (100, 440)
    assert _draw_priority_pill(c, 100, 440, None) == (100, 440)
