"""Small, closed Mustache dialect and parser-based HTML/CSS validation.

No evaluation, partials, lambdas, raw values or dynamic attribute names. The
HTML author controls structure; data can only occupy escaped text/quoted values.
"""
import html
import re
from html.parser import HTMLParser

import tinycss2

PROFILE = {'name', 'role', 'bio', 'company', 'badge', 'footer_tagline', 'photo_url',
           'logo_url', 'profile_url', 'initials'}
LINK = {'label', 'url', 'icon', 'kind', 'index', 'first', 'last'}
KINDS = {'web', 'whatsapp', 'email', 'phone', 'social', 'file'}
SECTIONS = PROFILE | LINK | {'primary_link', 'links'} | {f'links.{k}' for k in KINDS}
ACTIONS = {'save-contact', 'install-pwa', 'share', 'whatsapp', 'email', 'copy'}
TAGS = set('html head body title main header footer section article aside nav div span p h1 h2 h3 h4 h5 h6 a button img picture figure figcaption ul ol li dl dt dd strong em b i u s small blockquote q cite abbr time address br hr pre code mark sub sup style'.split())
ATTRS = set('id class title lang dir role alt width height loading decoding type hidden tabindex aria-label aria-hidden aria-labelledby aria-describedby data-asset data-action data-value data-link data-icon href src style'.split())
TOKEN = re.compile(r'{{\s*([#^/]?)\s*([A-Za-z_][A-Za-z_0-9.]*)\s*}}')


class TemplateError(ValueError):
    def __init__(self, message, file='template.html', line=1, code='invalid_template'):
        super().__init__(message)
        self.issue = {'severity': 'error', 'code': code, 'message': message, 'file': file, 'line': line}


def issue(message, file='template.html', line=1, code='invalid_template'):
    raise TemplateError(message, file, line, code)


def parse_mustache(source):
    if '{{{' in source:
        issue('No se permiten variables sin escapar.')
    nodes, stack = [], []
    current = nodes
    offset = 0
    for match in TOKEN.finditer(source):
        prefix = source[offset:match.start()]
        if '{{' in prefix:
            issue('Sintaxis Mustache no admitida; usa variables escapadas y secciones.', line=source.count('\n', 0, offset) + 1)
        current.append(prefix)
        op, key = match.groups()
        line = source.count('\n', 0, match.start()) + 1
        if op in ('#', '^'):
            if key not in SECTIONS:
                issue(f'Sección desconocida: {key}.', line=line)
            child = []
            current.append((op, key, child))
            stack.append((key, current))
            current = child
            if len(stack) > 20:
                issue('Demasiados niveles de secciones.', line=line)
        elif op == '/':
            if not stack or stack[-1][0] != key:
                issue(f'Cierre de sección incorrecto: {key}.', line=line)
            _, current = stack.pop()
        else:
            if key not in PROFILE | LINK:
                issue(f'Variable desconocida: {key}.', line=line)
            if key in LINK and not any(k == 'links' or k.startswith('links.') or k == 'primary_link' for k, _ in stack):
                issue(f'La variable {key} debe estar dentro de un bloque de enlaces.', line=line)
            current.append(('', key, []))
        offset = match.end()
    if '{{' in source[offset:]:
        issue('No se permiten variables sin escapar ni delimitadores personalizados.')
    current.append(source[offset:])
    if stack:
        issue(f'Falta cerrar la sección {stack[-1][0]}.')
    return nodes


def render_mustache(source, context):
    def render(nodes, values):
        result = []
        for node in nodes:
            if isinstance(node, str):
                result.append(node)
                continue
            op, key, children = node
            value = values.get(key, '')
            if not op:
                result.append(html.escape(str(value if value is not None else ''), quote=True))
            elif op == '^':
                if not value:
                    result.append(render(children, values))
            elif isinstance(value, list):
                result.extend(render(children, {**values, **item}) for item in value)
            elif value:
                result.append(render(children, {**values, **value} if isinstance(value, dict) else values))
        return ''.join(result)
    return render(parse_mustache(source), context)


def check_css(source, asset_keys, file='template.css', line_offset=0, declarations=False):
    if '{{' in source:
        issue('El CSS no admite variables de datos; usa variables CSS.', file, line_offset + 1)
    used = set()

    def fail(node, message):
        issue(message, file, getattr(node, 'source_line', 1) + line_offset)

    def values(tokens):
        for token in tokens:
            if token.type == 'error':
                fail(token, 'CSS inválido.')
            if token.type == 'url':
                if not re.fullmatch(r'#[\w-]+', token.value):
                    fail(token, 'Usa asset(clave) en lugar de url().')
            if token.type == 'function':
                name = token.lower_name
                if name == 'asset':
                    key = tinycss2.serialize(token.arguments).strip()
                    if key not in asset_keys:
                        fail(token, f'Asset no declarado: {key}.')
                    used.add(key)
                elif name == 'url':
                    args = [t for t in token.arguments if t.type != 'whitespace']
                    if len(args) != 1 or args[0].type != 'string' or not re.fullmatch(r'#[\w-]+', args[0].value):
                        fail(token, 'Usa asset(clave) en lugar de url().')
                elif name in {'image-set', '-webkit-image-set', 'src', 'expression', 'paint'}:
                    fail(token, f'La función {name} no está permitida.')
                else:
                    values(token.arguments)
            elif hasattr(token, 'content'):
                values(token.content)

    def declarations_in(tokens, keyframes=False):
        for dec in tinycss2.parse_declaration_list(tokens, skip_comments=True, skip_whitespace=True):
            if dec.type != 'declaration':
                fail(dec, 'Declaración CSS inválida.')
            if dec.lower_name in {'behavior', '-moz-binding'}:
                fail(dec, f'La propiedad {dec.name} no está permitida.')
            if keyframes and dec.lower_name not in {'transform', 'opacity'}:
                fail(dec, 'Sólo se animan transform y opacity.')
            values(dec.value)

    def rules_in(rules, keyframes=False):
        for rule in rules:
            if rule.type in {'comment', 'whitespace'}:
                continue
            if rule.type == 'error':
                fail(rule, 'Regla CSS inválida.')
            if rule.type == 'at-rule':
                if rule.lower_at_keyword not in {'media', 'supports', 'keyframes', '-webkit-keyframes', 'layer', 'container'} or rule.content is None:
                    fail(rule, f'@{rule.at_keyword} no está permitido.')
                values(rule.prelude)
                rules_in(tinycss2.parse_rule_list(rule.content), rule.lower_at_keyword.endswith('keyframes'))
            elif rule.type == 'qualified-rule':
                values(rule.prelude)
                declarations_in(rule.content, keyframes)
            else:
                fail(rule, 'CSS no admitido.')
    if declarations:
        declarations_in(source)
    else:
        rules_in(tinycss2.parse_stylesheet(source))
    return used


def rewrite_css(source, urls):
    def visit(tokens):
        result = []
        for token in tokens:
            if token.type == 'function' and token.lower_name == 'asset':
                key = tinycss2.serialize(token.arguments).strip()
                result.extend(tinycss2.parse_component_value_list(f'url("{urls[key]}")'))
            else:
                if token.type == 'function':
                    token.arguments = visit(token.arguments)
                if hasattr(token, 'content'):
                    token.content = visit(token.content)
                result.append(token)
        return result
    return tinycss2.serialize(visit(tinycss2.parse_component_value_list(source)))


class TemplateHTMLParser(HTMLParser):
    def __init__(self, asset_keys):
        super().__init__(convert_charrefs=True)
        self.asset_keys, self.used, self.styles = asset_keys, set(), []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        if tag not in TAGS:
            issue(f'Elemento no permitido: <{tag}>.', line=line)
        names = [name for name, _ in attrs]
        if len(names) != len(set(names)):
            issue('No se permiten atributos duplicados.', line=line)
        data = dict(attrs)
        # Quoting is necessary: escaping quotes cannot secure unquoted attributes.
        if '{{' in self.get_starttag_text():
            for raw in re.finditer(r'[^\s=<>]+\s*=\s*([^\s"\'][^\s>]*)', self.get_starttag_text()):
                if '{{' in raw.group(1):
                    issue('Las variables de atributos deben ir entre comillas.', line=line)
        for name, value in attrs:
            if name not in ATTRS or '{{' in name:
                issue(f'Atributo no permitido: {name}.', line=line)
            if value and any(m.group(1) for m in TOKEN.finditer(value)):
                issue('Las secciones deben envolver elementos, no atributos.', line=line)
        if 'href' in data and (tag != 'a' or not re.fullmatch(r'{{\s*url\s*}}', data['href'] or '')):
            issue('Los enlaces deben usar href="{{url}}" dentro de un bloque de enlaces.', line=line)
        if tag == 'a' and 'data-action' not in data and ('href' not in data or 'data-link' not in data):
            issue('Cada enlace debe incluir data-link y href="{{url}}".', line=line)
        if 'src' in data and (tag != 'img' or not re.fullmatch(r'{{\s*(photo_url|logo_url)\s*}}', data['src'] or '')):
            issue('Las imágenes sólo admiten variables de foto/logo o data-asset.', line=line)
        if tag == 'img' and 'src' not in data and 'data-asset' not in data:
            issue('La imagen necesita data-asset o una variable de foto/logo.', line=line)
        if 'data-asset' in data:
            key = data['data-asset']
            if tag != 'img' or key not in self.asset_keys:
                issue(f'Asset no declarado o fuera de una imagen: {key}.', line=line)
            self.used.add(key)
        if 'data-action' in data and (tag not in {'a', 'button'} or data['data-action'] not in ACTIONS):
            issue('Acción desconocida o fuera de un botón/enlace.', line=line)
        if 'data-icon' in data and not re.fullmatch(r'(?:[a-z][a-z0-9-]{0,60}|{{\s*icon\s*}})', data['data-icon'] or ''):
            issue('Nombre de icono inválido.', line=line)
        if data.get('style'):
            self.used |= check_css(data['style'], self.asset_keys, 'template.html', line - 1, declarations=True)
        self.in_style = tag == 'style'

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag not in TAGS:
            issue(f'Elemento no permitido: </{tag}>.', line=self.getpos()[0])
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.used |= check_css(data, self.asset_keys, 'template.html', self.getpos()[0] - 1)
            self.styles.append(data)

    def handle_comment(self, data):
        if '{{' in data or '}}' in data:
            issue('Las variables no pueden estar en comentarios.', line=self.getpos()[0])


def validate_sources(source, css, manifest):
    parse_mustache(source)
    if re.search(r'<\s*/?\s*{{', source):
        issue('Las variables no pueden definir etiquetas HTML.')
    if not re.search(r'{{\s*name\s*}}', source) or not re.search(r'{{\s*#\s*links\s*}}', source):
        issue('Incluye {{name}} y el bloque {{#links}}…{{/links}}.')
    parser = TemplateHTMLParser({asset['key'] for asset in manifest['assets']})
    parser.feed(source)
    used = parser.used | check_css(css, parser.asset_keys)
    if manifest.get('motion') and not re.search(r'prefers-reduced-motion\s*:\s*reduce', css + '\n'.join(parser.styles)):
        issue('motion: true requiere @media (prefers-reduced-motion: reduce).', 'template.css', code='reduced_motion')
    return [{'severity': 'warning', 'code': 'unused_asset', 'message': f'Imagen decorativa sin usar: {key}.', 'file': 'manifest.json', 'line': 1}
            for key in parser.asset_keys - used]
