"""Bounded archive reader, manifest contract and raster/SVG normalization."""
import io
from contextlib import contextmanager
from contextvars import ContextVar
import json
import re
import stat
import uuid
import warnings
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree

from defusedxml import ElementTree as SafeXML
from defusedxml.common import DefusedXmlException
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from content.storage import get_private_storage
from .syntax import TemplateError, check_css, issue, validate_sources
import tinycss2

_written_files = ContextVar('linktree_template_files', default=None)


@contextmanager
def asset_batch():
    paths = []
    token = _written_files.set(paths)
    try:
        yield
    except Exception:
        for path in paths:
            get_private_storage().delete(path)
        raise
    finally:
        _written_files.reset(token)


PACKAGE_LIMIT = 4 * 1024 * 1024
IMAGE_LIMIT = 800 * 1024
SOURCE_LIMIT = 200 * 1024
RASTER_BASE_WIDTH = 667
FONT = re.compile(r'^[A-Za-z][A-Za-z0-9 ]{0,79}(?::(?:ital,)?wght@(?:[01],)?[1-9]00(?:\.\.[1-9]00)?(?:;(?:[01],)?[1-9]00(?:\.\.[1-9]00)?)*)?$')
KEY = re.compile(r'^[a-z][a-z0-9_-]{0,39}$')
SVG_NS = 'http://www.w3.org/2000/svg'
SVG_TAGS = set('svg g path rect circle ellipse line polyline polygon text tspan defs symbol use clipPath mask linearGradient radialGradient stop pattern title desc filter feGaussianBlur feOffset feBlend feColorMatrix feComposite feFlood feMerge feMergeNode'.split())


def safe_path(value):
    if not isinstance(value, str) or '\\' in value or '\x00' in value:
        issue('Ruta de archivo inválida.', 'manifest.json')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or len(value) > 180:
        issue('No se permiten rutas absolutas ni relativas fuera del paquete.', 'manifest.json')
    return value


def read_package(files):
    """Accept pairs (relative path, UploadedFile); never extract an archive."""
    files = list(files)
    if not files or sum(f.size for _, f in files) > PACKAGE_LIMIT:
        issue('El paquete debe pesar como máximo 4 MB.', 'manifest.json')
    entries = {}

    def add(name, data):
        safe_path(name)
        if name in entries:
            issue(f'Archivo repetido: {name}.', 'manifest.json')
        if len(entries) >= 15 or sum(map(len, entries.values())) + len(data) > PACKAGE_LIMIT:
            issue('El paquete supera 4 MB o 15 archivos.', 'manifest.json')
        entries[name] = data
    if len(files) == 1 and files[0][1].name.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(files[0][1]) as archive:
                members = archive.infolist()
                if len(members) > 40:
                    issue('Demasiadas entradas en el ZIP.', 'manifest.json')
                total = 0
                for member in members:
                    safe_path(member.filename.rstrip('/'))
                    if stat.S_ISLNK(member.external_attr >> 16) or member.flag_bits & 1:
                        issue('El ZIP no admite enlaces simbólicos ni cifrado.', 'manifest.json')
                    if member.is_dir():
                        continue
                    total += member.file_size
                    if total > PACKAGE_LIMIT:
                        issue('El ZIP descomprimido supera 4 MB.', 'manifest.json')
                    add(member.filename, archive.read(member))
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as exc:
            raise TemplateError('ZIP inválido o no compatible.', 'manifest.json') from exc
    else:
        for name, uploaded in files:
            add(name, uploaded.read(PACKAGE_LIMIT + 1))
    # ZIPs/directory selections may contain a single enclosing directory.
    if 'manifest.json' not in entries and entries:
        roots = {name.split('/')[0] for name in entries}
        if len(roots) == 1 and all('/' in name for name in entries):
            entries = {name.split('/', 1)[1]: value for name, value in entries.items()}
    if not {'manifest.json', 'template.html'} <= entries.keys():
        issue('Faltan template.html o manifest.json.', 'manifest.json')
    for name in ('manifest.json', 'template.html', 'template.css'):
        if len(entries.get(name, b'')) > SOURCE_LIMIT:
            issue('El archivo de texto supera 200 KB.', name)
    try:
        manifest = json.loads(entries['manifest.json'].decode('utf-8-sig'))
        source = entries['template.html'].decode('utf-8-sig')
        css = entries.get('template.css', b'').decode('utf-8-sig')
    except (ValueError, UnicodeError) as exc:
        issue('JSON o texto UTF-8 inválido.', 'manifest.json', getattr(exc, 'lineno', 1))
    manifest = validate_manifest(manifest)
    declared = {a['file'] for a in manifest['assets']}
    extras = entries.keys() - declared - {'template.html', 'template.css', 'manifest.json'}
    if extras or declared - entries.keys():
        issue('Los archivos deben coincidir con los assets declarados en manifest.json.', 'manifest.json')
    notices = validate_sources(source, css, manifest)
    images = {}
    for asset in manifest['assets']:
        variants, metadata, changed = normalize_image(entries[asset['file']], asset['file'])
        images[asset['key']] = (variants, {**metadata, 'alt': asset['alt']})
        if changed:
            notices.append({'severity': 'warning', 'code': 'sanitized_svg', 'message': f'Se eliminaron elementos inseguros de {asset["file"]}.', 'file': asset['file'], 'line': 1})
    return manifest, source, css, images, notices


def validate_manifest(data):
    if not isinstance(data, dict) or data.get('spec') != '1.0':
        issue('El manifest debe declarar spec: "1.0".', 'manifest.json')
    allowed = {'spec', 'name', 'author', 'min_width', 'max_width', 'fonts', 'slots', 'assets', 'editable_assets', 'motion'}
    if data.keys() - allowed:
        issue('El manifest contiene campos desconocidos.', 'manifest.json')
    data = {'author': '', 'min_width': 320, 'max_width': 480, 'fonts': [], 'slots': {}, 'assets': [], 'editable_assets': [], 'motion': False, **data}
    for key, limit in [('name', 160), ('author', 160)]:
        if not isinstance(data.get(key), str) or len(data[key]) > limit or (key == 'name' and not data[key].strip()):
            issue(f'{key} debe ser texto de hasta {limit} caracteres.', 'manifest.json')
    if type(data['min_width']) is not int or type(data['max_width']) is not int or not 320 <= data['min_width'] <= data['max_width'] <= 2000:
        issue('Anchos inválidos: deben estar entre 320 y 2000 px.', 'manifest.json')
    if type(data['motion']) is not bool:
        issue('motion debe ser booleano.', 'manifest.json')
    if not isinstance(data['fonts'], list) or len(data['fonts']) > 8 or any(not isinstance(f, str) or not FONT.fullmatch(f) for f in data['fonts']):
        issue('Declara hasta 8 familias válidas de Google Fonts.', 'manifest.json')
    if not isinstance(data['slots'], dict) or data['slots'].keys() - {'photo', 'logo'}:
        issue('Los slots disponibles son photo y logo.', 'manifest.json')
    for slot in data['slots'].values():
        if not isinstance(slot, dict) or slot.keys() - {'required', 'aspect', 'min_px', 'format'} or type(slot.get('required', False)) is not bool:
            issue('Declaración de slot inválida.', 'manifest.json')
        if 'aspect' in slot and (not isinstance(slot['aspect'], str) or not re.fullmatch(r'[1-9]\d?:[1-9]\d?', slot['aspect'])):
            issue('aspect debe ser una proporción, por ejemplo 4:5.', 'manifest.json')
        if 'min_px' in slot and (type(slot['min_px']) is not int or not 1 <= slot['min_px'] <= 2000):
            issue('min_px debe estar entre 1 y 2000.', 'manifest.json')
        if 'format' in slot and (not isinstance(slot['format'], list) or not slot['format'] or any(not isinstance(f, str) or f not in {'svg', 'png', 'jpg', 'jpeg', 'webp'} for f in slot['format'])):
            issue('Formato de slot inválido.', 'manifest.json')
    if not isinstance(data['assets'], list) or len(data['assets']) > 12:
        issue('Se admiten hasta 12 imágenes decorativas.', 'manifest.json')
    keys, paths = set(), set()
    for asset in data['assets']:
        if not isinstance(asset, dict) or not {'key', 'file', 'alt'} <= asset.keys() or asset.keys() - {'key', 'file', 'alt', 'role'}:
            issue('Cada asset necesita key, file y alt.', 'manifest.json')
        if not isinstance(asset['key'], str) or not KEY.fullmatch(asset['key']) or asset['key'].startswith('slot-') or asset['key'] in keys:
            issue('La clave del asset es inválida o está repetida.', 'manifest.json')
        path = safe_path(asset['file'])
        if not path.startswith('assets/') or path in paths:
            issue('Los assets deben tener rutas únicas dentro de assets/.', 'manifest.json')
        if not isinstance(asset['alt'], str) or len(asset['alt']) > 500 or not isinstance(asset.get('role', ''), str) or asset.get('role', '') not in {'', 'background'}:
            issue('alt o role inválido.', 'manifest.json')
        keys.add(asset['key']); paths.add(path)
    if not isinstance(data['editable_assets'], list) or any(not isinstance(k, str) or k not in keys for k in data['editable_assets']) or len(set(data['editable_assets'])) != len(data['editable_assets']):
        issue('editable_assets sólo puede contener claves declaradas sin repetir.', 'manifest.json')
    return data


def sanitize_svg(raw):
    try:
        root = SafeXML.fromstring(raw)
    except (ValueError, ElementTree.ParseError, DefusedXmlException) as exc:
        raise TemplateError('SVG inválido.', 'assets/') from exc
    if root.tag != f'{{{SVG_NS}}}svg':
        issue('El SVG necesita su namespace estándar.', 'assets/')
    changed = False
    for parent in list(root.iter()):
        for child in list(parent):
            if child.tag not in {f'{{{SVG_NS}}}{t}' for t in SVG_TAGS}:
                parent.remove(child); changed = True
        for name, value in list(parent.attrib.items()):
            local = name.rsplit('}', 1)[-1].lower()
            if local == 'style':
                try:
                    check_css(value, set(), declarations=True)
                    declarations = tinycss2.parse_declaration_list(value, skip_comments=True, skip_whitespace=True)
                    safe = [item for item in declarations if not item.lower_name.startswith(('animation', 'transition', '-webkit-animation', '-webkit-transition'))]
                    parent.set(name, tinycss2.serialize(safe))
                    changed |= len(safe) != len(declarations)
                except TemplateError:
                    del parent.attrib[name]; changed = True
                continue
            if (local.startswith('on') or local == 'base' or '\\' in value or
                (local in {'href', 'src'} and not re.fullmatch(r'#[\w-]+', value)) or
                ('url' in value.lower() and not re.fullmatch(r'url\(\s*#[\w-]+\s*\)', value))):
                del parent.attrib[name]; changed = True
    try:
        box = [float(x) for x in re.split(r'[ ,]+', root.get('viewBox', '').strip())]
        if len(box) == 4:
            width, height = box[2:]
        else:
            width, height = [float(root.get(k, '').removesuffix('px')) for k in ('width', 'height')]
        if not (0 < width <= 100000 and 0 < height <= 100000):
            raise ValueError
    except ValueError:
        issue('El SVG necesita dimensiones o viewBox válidos.', 'assets/')
    scale = min(1, 2000 / max(width, height))
    if len(box) != 4:
        root.set('viewBox', f'0 0 {width} {height}')
    root.set('width', str(round(width * scale, 3)))
    root.set('height', str(round(height * scale, 3)))
    ElementTree.register_namespace('', SVG_NS)
    return ElementTree.tostring(root, encoding='utf-8'), round(width * scale), round(height * scale), changed


def normalize_image(raw, filename, limit=IMAGE_LIMIT):
    ext = PurePosixPath(filename).suffix.lower()
    if len(raw) > limit or ext not in {'.png', '.webp', '.svg', '.jpg', '.jpeg'}:
        issue('Usa PNG, WebP, SVG o JPG de hasta 800 KB.', filename)
    if ext == '.svg':
        data, width, height, changed = sanitize_svg(raw)
        return {1: data, 2: data, 3: data}, {'format': 'svg', 'mime': 'image/svg+xml', 'width': width, 'height': height}, changed
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as original:
                if original.format not in {'PNG', 'WEBP', 'JPEG'} or getattr(original, 'n_frames', 1) != 1:
                    issue('La imagen debe ser estática en PNG, WebP o JPG.', filename)
                original.load()
                img = ImageOps.exif_transpose(original).convert('RGBA' if original.mode in {'RGBA', 'LA', 'P'} else 'RGB')
                img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise TemplateError('No se pudo leer la imagen.', filename) from exc
    variants = {}
    for density in (1, 2, 3):
        variant = img.copy()
        target = min(img.width, RASTER_BASE_WIDTH * density)
        variant.thumbnail((target, max(1, round(img.height * target / img.width))), Image.Resampling.LANCZOS)
        stream = io.BytesIO(); variant.save(stream, 'WEBP', quality=85)
        variants[density] = stream.getvalue()
    return variants, {'format': ext.lstrip('.'), 'mime': 'image/webp', 'width': img.width, 'height': img.height}, False


def store_image(variants, metadata):
    storage = get_private_storage()
    prefix = f'linktree-templates/assets/{uuid.uuid4().hex}'
    paths = {}
    try:
        for density, raw in variants.items():
            paths[str(density)] = storage.save(f'{prefix}/{density}', ContentFile(raw))
            if _written_files.get() is not None:
                _written_files.get().append(paths[str(density)])
    except Exception:
        for path in paths.values():
            storage.delete(path)
        raise
    return {**metadata, 'paths': paths, 'size': len(variants[3])}
